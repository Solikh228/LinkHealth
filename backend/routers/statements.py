import csv
from datetime import datetime, timezone
import io
import re
from typing import List, Optional
import uuid

from fastapi import APIRouter, Depends, File, Form, HTTPException, Response, UploadFile, status
from pydantic import BaseModel

from dependencies import (
    get_connection_repo,
    get_finding_repo,
    get_subscription_repo,
    get_transaction_repo,
)
from repositories.base import (
    ConnectionRepository,
    FindingRepository,
    SubscriptionRepository,
    TransactionRepository,
)
from schemas import ConnectionResponse, Money, TransactionResponse
from services.cadence import detect_subscriptions
from services.waste_detector import generate_waste_findings

router = APIRouter(tags=["Statements & Reports"])


def _parse_amount(raw_val: str) -> int:
    """Parses a raw currency amount string into minor units (cents)."""
    cleaned = raw_val.strip()
    is_negative = False
    if cleaned.startswith("(") and cleaned.endswith(")"):
        is_negative = True
        cleaned = cleaned[1:-1].strip()
    elif cleaned.startswith("-"):
        is_negative = True
        cleaned = cleaned[1:].strip()

    # Remove currency symbols and formatting commas
    cleaned = re.sub(r"[^\d.]", "", cleaned)
    if not cleaned:
        return 0
    val_float = float(cleaned)
    minor = int(round(val_float * 100))
    # Charges in SubTracker transactions are represented as negative amounts
    return -minor if is_negative or minor > 0 else minor


def _find_column(headers: List[str], candidates: List[str], explicit: Optional[str] = None) -> Optional[str]:
    if explicit and explicit in headers:
        return explicit
    for c in candidates:
        for h in headers:
            if h.strip().lower() == c.lower():
                return h
    return None


def process_csv_rows(
    rows: List[dict],
    date_col: str,
    merchant_col: str,
    amount_col: str,
    currency_col: Optional[str] = None,
    default_currency: str = "USD",
) -> List[TransactionResponse]:
    transactions: List[TransactionResponse] = []
    for i, row in enumerate(rows):
        date_val = str(row.get(date_col, "")).strip()
        merchant_val = str(row.get(merchant_col, "")).strip()
        amount_raw = str(row.get(amount_col, "")).strip()
        if not date_val or not merchant_val or not amount_raw:
            continue

        curr_val = (
            str(row.get(currency_col, "")).strip()
            if currency_col and row.get(currency_col)
            else default_currency
        ) or default_currency

        minor = _parse_amount(amount_raw)
        tx_id = f"tx_csv_{uuid.uuid4().hex[:10]}"
        tx = TransactionResponse(
            id=tx_id,
            connectionId="conn_csv_import",
            accountName="Manual CSV Statement",
            date=date_val,
            descriptionRaw=merchant_val,
            merchantNormalized=merchant_val,
            amount=Money(amountMinor=minor, currency=curr_val),
            status="posted",
            isRecurringCandidate=True,
        )
        transactions.append(tx)
    return transactions


class CsvImportPayload(BaseModel):
    csvContent: str
    dateColumn: Optional[str] = None
    merchantColumn: Optional[str] = None
    amountColumn: Optional[str] = None
    currencyColumn: Optional[str] = None
    defaultCurrency: Optional[str] = "USD"


@router.post("/api/statements/import-csv")
def import_csv_data(
    payload: CsvImportPayload,
    conn_repo: ConnectionRepository = Depends(get_connection_repo),
    sub_repo: SubscriptionRepository = Depends(get_subscription_repo),
    tx_repo: TransactionRepository = Depends(get_transaction_repo),
    finding_repo: FindingRepository = Depends(get_finding_repo),
):
    try:
        reader = csv.DictReader(io.StringIO(payload.csvContent.strip()))
        headers = reader.fieldnames or []
        rows = list(reader)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to parse CSV: {str(e)}",
        )

    date_col = _find_column(headers, ["date", "transaction date", "posted date", "trans date"], payload.dateColumn)
    merchant_col = _find_column(
        headers, ["merchant", "description", "payee", "name", "narrative", "details"], payload.merchantColumn
    )
    amount_col = _find_column(headers, ["amount", "total", "charge", "debit", "subtotal"], payload.amountColumn)
    currency_col = _find_column(headers, ["currency", "curr"], payload.currencyColumn)

    if not date_col or not merchant_col or not amount_col:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Missing required columns in CSV. Found: {headers}. Needed: date, merchant/description, amount.",
        )

    now_iso = datetime.now(timezone.utc).isoformat()
    conn_repo.add(
        ConnectionResponse(
            id="conn_csv_import",
            name="Manual CSV Statement",
            type="bank",
            provider="csv",
            status="connected",
            lastSyncedAt=now_iso,
        )
    )

    transactions = process_csv_rows(
        rows,
        date_col=date_col,
        merchant_col=merchant_col,
        amount_col=amount_col,
        currency_col=currency_col,
        default_currency=payload.defaultCurrency or "USD",
    )

    for tx in transactions:
        tx_repo.add(tx)

    # Run detection pipeline
    all_txs = tx_repo.list(limit=5000)
    detected_subs = detect_subscriptions(all_txs)
    for sub in detected_subs:
        sub_repo.add(sub)

    all_subs = sub_repo.list(limit=500)
    findings = generate_waste_findings(subscriptions=all_subs, transactions=all_txs)
    for f in findings:
        finding_repo.add(f)

    return {
        "success": True,
        "importedTransactions": len(transactions),
        "detectedSubscriptions": len(detected_subs),
        "detectedFindings": len(findings),
    }


@router.post("/api/statements/upload-csv")
async def upload_csv_file(
    file: UploadFile = File(...),
    date_column: Optional[str] = Form(None),
    merchant_column: Optional[str] = Form(None),
    amount_column: Optional[str] = Form(None),
    currency_column: Optional[str] = Form(None),
    default_currency: Optional[str] = Form("USD"),
    conn_repo: ConnectionRepository = Depends(get_connection_repo),
    sub_repo: SubscriptionRepository = Depends(get_subscription_repo),
    tx_repo: TransactionRepository = Depends(get_transaction_repo),
    finding_repo: FindingRepository = Depends(get_finding_repo),
):
    contents = await file.read()
    try:
        csv_text = contents.decode("utf-8")
    except UnicodeDecodeError:
        csv_text = contents.decode("latin-1")

    payload = CsvImportPayload(
        csvContent=csv_text,
        dateColumn=date_column,
        merchantColumn=merchant_column,
        amountColumn=amount_column,
        currencyColumn=currency_column,
        defaultCurrency=default_currency,
    )
    return import_csv_data(
        payload=payload,
        conn_repo=conn_repo,
        sub_repo=sub_repo,
        tx_repo=tx_repo,
        finding_repo=finding_repo,
    )


@router.get("/api/reports/savings-csv")
@router.get("/api/findings/export-csv")
def export_savings_csv(
    finding_repo: FindingRepository = Depends(get_finding_repo),
):
    findings = finding_repo.list()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(
        [
            "Finding ID",
            "Subscription ID",
            "Subscription Name",
            "Type",
            "Severity",
            "Status",
            "Decision",
            "Decision Note",
            "Potential Savings ($)",
            "Confirmed Savings ($)",
            "Created At",
        ]
    )

    for f in findings:
        pot_dollars = f"{(f.potentialSavings.amountMinor / 100):.2f}"
        conf_dollars = (
            f"{(f.confirmedSavings.amountMinor / 100):.2f}"
            if f.confirmedSavings
            else "0.00"
        )
        writer.writerow(
            [
                f.id,
                f.subscriptionId,
                f.subscriptionName,
                f.type,
                f.severity,
                f.status,
                getattr(f, "decision", "") or "",
                getattr(f, "decisionNote", "") or "",
                pot_dollars,
                conf_dollars,
                f.createdAt,
            ]
        )

    csv_data = output.getvalue()
    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={
            "Content-Disposition": "attachment; filename=subtracker_savings_report.csv"
        },
    )
