from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import delete, select
from sqlalchemy.orm import Session, selectinload

from models import Action, BillingEvidence, Connection, Finding, Subscription, Transaction
from schemas import (
    BillingEvidenceResponse,
    ConnectionResponse,
    FindingActionRequest,
    FindingResponse,
    Money,
    SubscriptionResponse,
    TransactionResponse,
)
from .base import (
    ConnectionRepository,
    FindingRepository,
    SubscriptionRepository,
    TransactionRepository,
)


def _sub_to_response(model: Subscription) -> SubscriptionResponse:
    tx_responses = [
        TransactionResponse(
            id=t.id,
            connectionId=t.connection_id,
            accountName=t.account_name,
            date=t.date,
            descriptionRaw=t.description_raw,
            merchantNormalized=t.merchant_normalized,
            amount=Money(amountMinor=t.amount_minor, currency=t.currency),
            status=t.status,  # type: ignore
            isRecurringCandidate=t.is_recurring_candidate,
            subscriptionId=t.subscription_id,
        )
        for t in (model.transactions or [])
    ]
    ev_responses = [
        BillingEvidenceResponse(
            id=e.id,
            subscriptionId=e.subscription_id or model.id,
            senderDomain=e.sender_domain,
            subject=e.subject,
            receivedAt=e.received_at,
            confidence=e.confidence,
            snippet=e.snippet,
            extractedAmountMinor=e.amount_minor,
        )
        for e in (model.billing_evidence or [])
    ]
    return SubscriptionResponse(
        id=model.id,
        name=model.name,
        vendorDomain=model.vendor_domain,
        category=model.category,
        status=model.status,  # type: ignore
        billingInterval=model.billing_interval,  # type: ignore
        amount=Money(amountMinor=model.amount_minor, currency=model.currency),
        monthlyEquivalent=Money(amountMinor=model.monthly_equivalent_minor, currency=model.currency),
        nextRenewalDate=model.next_renewal_date,
        confidence=model.confidence,
        explanation=model.explanation,
        lastChargeDate=model.last_charge_date,
        note=model.note,
        transactions=tx_responses,
        evidence=ev_responses,
    )


def _finding_to_response(f: Finding) -> FindingResponse:
    return FindingResponse(
        id=f.id,
        subscriptionId=f.subscription_id or "",
        subscriptionName=f.subscription_name,
        type=f.type,  # type: ignore
        severity=f.severity,  # type: ignore
        status=f.status,  # type: ignore
        title=f.title,
        explanation=f.explanation,
        potentialSavings=Money(amountMinor=f.potential_savings_minor, currency=f.currency),
        confirmedSavings=Money(amountMinor=f.confirmed_savings_minor, currency=f.currency)
        if f.confirmed_savings_minor is not None
        else None,
        createdAt=f.created_at,
        decision=f.decision,  # type: ignore
        decisionNote=f.decision_note,
        decisionAt=f.decision_at,
    )


def _tx_to_response(t: Transaction) -> TransactionResponse:
    return TransactionResponse(
        id=t.id,
        connectionId=t.connection_id,
        accountName=t.account_name,
        date=t.date,
        descriptionRaw=t.description_raw,
        merchantNormalized=t.merchant_normalized,
        amount=Money(amountMinor=t.amount_minor, currency=t.currency),
        status=t.status,  # type: ignore
        isRecurringCandidate=t.is_recurring_candidate,
        subscriptionId=t.subscription_id,
    )


def _conn_to_response(c: Connection) -> ConnectionResponse:
    return ConnectionResponse(
        id=c.id,
        name=c.name,
        type=c.type,  # type: ignore
        provider=c.provider,  # type: ignore
        status=c.status,  # type: ignore
        lastSyncedAt=c.last_synced_at,
    )


class SqlAlchemySubscriptionRepository(SubscriptionRepository):
    def __init__(self, session: Session):
        self.session = session

    def list(
        self,
        status: Optional[str] = None,
        cadence: Optional[str] = None,
        search: Optional[str] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> List[SubscriptionResponse]:
        stmt = (
            select(Subscription)
            .options(
                selectinload(Subscription.transactions),
                selectinload(Subscription.billing_evidence),
            )
            .offset(skip)
            .limit(limit)
        )
        if status:
            stmt = stmt.where(Subscription.status == status)
        if cadence:
            stmt = stmt.where(Subscription.billing_interval == cadence)
        if search:
            q = f"%{search.lower()}%"
            stmt = stmt.where(
                (Subscription.name.ilike(q)) | (Subscription.vendor_domain.ilike(q))
            )

        items = self.session.scalars(stmt).all()
        return [_sub_to_response(m) for m in items]

    def get_by_id(self, subscription_id: str) -> Optional[SubscriptionResponse]:
        stmt = (
            select(Subscription)
            .options(
                selectinload(Subscription.transactions),
                selectinload(Subscription.billing_evidence),
            )
            .where(Subscription.id == subscription_id)
        )
        item = self.session.scalars(stmt).first()
        return _sub_to_response(item) if item else None

    def update(
        self,
        subscription_id: str,
        name: Optional[str] = None,
        billing_interval: Optional[str] = None,
        category: Optional[str] = None,
        status: Optional[str] = None,
        note: Optional[str] = None,
    ) -> Optional[SubscriptionResponse]:
        stmt = (
            select(Subscription)
            .options(
                selectinload(Subscription.transactions),
                selectinload(Subscription.billing_evidence),
            )
            .where(Subscription.id == subscription_id)
        )
        item = self.session.scalars(stmt).first()
        if not item:
            return None

        if name is not None:
            item.name = name
        if billing_interval is not None:
            item.billing_interval = billing_interval
        if category is not None:
            item.category = category
        if status is not None:
            item.status = status
        if note is not None:
            item.note = note

        self.session.commit()
        self.session.refresh(item)
        return _sub_to_response(item)

    def add(self, subscription: SubscriptionResponse) -> SubscriptionResponse:
        existing = self.session.get(Subscription, subscription.id)
        if existing:
            existing.name = subscription.name
            existing.vendor_domain = subscription.vendorDomain
            existing.category = subscription.category
            existing.status = subscription.status
            existing.billing_interval = subscription.billingInterval
            existing.amount_minor = subscription.amount.amountMinor
            existing.currency = subscription.amount.currency
            existing.monthly_equivalent_minor = subscription.monthlyEquivalent.amountMinor
            existing.next_renewal_date = subscription.nextRenewalDate
            existing.confidence = subscription.confidence
            existing.explanation = subscription.explanation
            existing.last_charge_date = subscription.lastChargeDate
            existing.note = getattr(subscription, "note", None)
            item = existing
        else:
            item = Subscription(
                id=subscription.id,
                name=subscription.name,
                vendor_domain=subscription.vendorDomain,
                category=subscription.category,
                status=subscription.status,
                billing_interval=subscription.billingInterval,
                amount_minor=subscription.amount.amountMinor,
                currency=subscription.amount.currency,
                monthly_equivalent_minor=subscription.monthlyEquivalent.amountMinor,
                next_renewal_date=subscription.nextRenewalDate,
                confidence=subscription.confidence,
                explanation=subscription.explanation,
                last_charge_date=subscription.lastChargeDate,
                note=getattr(subscription, "note", None),
            )
            self.session.add(item)

        # Handle embedded transactions and evidence if provided
        if subscription.transactions:
            for t in subscription.transactions:
                # Ensure connection exists
                conn = self.session.get(Connection, t.connectionId)
                if not conn:
                    conn = Connection(
                        id=t.connectionId,
                        name=t.accountName or "Bank Account",
                        type="bank",
                        provider="plaid",
                        status="connected",
                    )
                    self.session.add(conn)
                    self.session.flush()

                existing_tx = self.session.get(Transaction, t.id)
                if existing_tx:
                    existing_tx.subscription_id = item.id
                else:
                    tx_model = Transaction(
                        id=t.id,
                        connection_id=t.connectionId,
                        subscription_id=item.id,
                        account_name=t.accountName,
                        date=t.date,
                        description_raw=t.descriptionRaw,
                        merchant_normalized=t.merchantNormalized,
                        amount_minor=t.amount.amountMinor,
                        currency=t.amount.currency,
                        status=t.status,
                        is_recurring_candidate=t.isRecurringCandidate,
                    )
                    self.session.add(tx_model)

        if subscription.evidence:
            for ev in subscription.evidence:
                existing_ev = self.session.get(BillingEvidence, ev.id)
                if not existing_ev:
                    ev_model = BillingEvidence(
                        id=ev.id,
                        subscription_id=item.id,
                        sender_domain=ev.senderDomain,
                        subject=ev.subject,
                        received_at=ev.receivedAt,
                        confidence=ev.confidence,
                        snippet=ev.snippet,
                    )
                    self.session.add(ev_model)

        self.session.commit()
        return self.get_by_id(subscription.id) or _sub_to_response(item)

    def clear(self) -> None:
        self.session.execute(delete(BillingEvidence))
        self.session.execute(delete(Subscription))
        self.session.commit()


class SqlAlchemyFindingRepository(FindingRepository):
    def __init__(self, session: Session):
        self.session = session

    def list(
        self,
        status: Optional[str] = None,
        finding_type: Optional[str] = None,
    ) -> List[FindingResponse]:
        stmt = select(Finding)
        if status:
            stmt = stmt.where(Finding.status == status)
        if finding_type:
            stmt = stmt.where(Finding.type == finding_type)

        items = self.session.scalars(stmt).all()
        return [_finding_to_response(f) for f in items]

    def get_by_id(self, finding_id: str) -> Optional[FindingResponse]:
        item = self.session.get(Finding, finding_id)
        return _finding_to_response(item) if item else None

    def apply_action(
        self,
        finding_id: str,
        action: FindingActionRequest,
    ) -> Optional[FindingResponse]:
        item = self.session.get(Finding, finding_id)
        if not item:
            return None

        now_iso = datetime.now(timezone.utc).isoformat()
        item.status = action.decision
        item.decision = action.decision
        item.decision_note = action.note
        item.decision_at = now_iso

        if action.decision == "confirmed_waste":
            item.confirmed_savings_minor = item.potential_savings_minor

        action_record = Action(
            id=f"act_{finding_id}_{int(datetime.now(timezone.utc).timestamp())}",
            finding_id=item.id,
            decision=action.decision,
            note=action.note,
            created_at=now_iso,
        )
        self.session.add(action_record)
        self.session.commit()
        self.session.refresh(item)
        return _finding_to_response(item)

    def add(self, finding: FindingResponse) -> FindingResponse:
        existing = self.session.get(Finding, finding.id)
        # Check if subscription exists, otherwise set subscription_id to None to satisfy FK
        sub_id = finding.subscriptionId
        if sub_id and not self.session.get(Subscription, sub_id):
            sub_id = None

        if existing:
            existing.subscription_id = sub_id
            existing.subscription_name = finding.subscriptionName
            existing.type = finding.type
            existing.severity = finding.severity
            existing.status = finding.status
            existing.title = finding.title
            existing.explanation = finding.explanation
            existing.potential_savings_minor = finding.potentialSavings.amountMinor
            existing.confirmed_savings_minor = (
                finding.confirmedSavings.amountMinor if finding.confirmedSavings else None
            )
            existing.currency = finding.potentialSavings.currency
            existing.created_at = finding.createdAt
            existing.decision = getattr(finding, "decision", None)
            existing.decision_note = getattr(finding, "decisionNote", None)
            existing.decision_at = getattr(finding, "decisionAt", None)
            item = existing
        else:
            item = Finding(
                id=finding.id,
                subscription_id=sub_id,
                subscription_name=finding.subscriptionName,
                type=finding.type,
                severity=finding.severity,
                status=finding.status,
                title=finding.title,
                explanation=finding.explanation,
                potential_savings_minor=finding.potentialSavings.amountMinor,
                confirmed_savings_minor=(
                    finding.confirmedSavings.amountMinor if finding.confirmedSavings else None
                ),
                currency=finding.potentialSavings.currency,
                created_at=finding.createdAt,
                decision=getattr(finding, "decision", None),
                decision_note=getattr(finding, "decisionNote", None),
                decision_at=getattr(finding, "decisionAt", None),
            )
            self.session.add(item)

        self.session.commit()
        self.session.refresh(item)
        return _finding_to_response(item)

    def clear(self) -> None:
        self.session.execute(delete(Action))
        self.session.execute(delete(Finding))
        self.session.commit()


class SqlAlchemyTransactionRepository(TransactionRepository):
    def __init__(self, session: Session):
        self.session = session

    def list(
        self,
        subscription_id: Optional[str] = None,
        connection_id: Optional[str] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> List[TransactionResponse]:
        stmt = select(Transaction).offset(skip).limit(limit)
        if subscription_id:
            stmt = stmt.where(Transaction.subscription_id == subscription_id)
        if connection_id:
            stmt = stmt.where(Transaction.connection_id == connection_id)

        items = self.session.scalars(stmt).all()
        return [_tx_to_response(t) for t in items]

    def add(self, transaction: TransactionResponse) -> TransactionResponse:
        # Ensure connection exists
        conn = self.session.get(Connection, transaction.connectionId)
        if not conn:
            conn = Connection(
                id=transaction.connectionId,
                name=transaction.accountName or "Bank Account",
                type="bank",
                provider="plaid",
                status="connected",
            )
            self.session.add(conn)
            self.session.flush()

        # Check subscription if present
        sub_id = getattr(transaction, "subscriptionId", None)
        if sub_id and not self.session.get(Subscription, sub_id):
            sub_id = None

        existing = self.session.get(Transaction, transaction.id)
        if existing:
            existing.connection_id = transaction.connectionId
            existing.subscription_id = sub_id
            existing.account_name = transaction.accountName
            existing.date = transaction.date
            existing.description_raw = transaction.descriptionRaw
            existing.merchant_normalized = transaction.merchantNormalized
            existing.amount_minor = transaction.amount.amountMinor
            existing.currency = transaction.amount.currency
            existing.status = transaction.status
            existing.is_recurring_candidate = transaction.isRecurringCandidate
            item = existing
        else:
            item = Transaction(
                id=transaction.id,
                connection_id=transaction.connectionId,
                subscription_id=sub_id,
                account_name=transaction.accountName,
                date=transaction.date,
                description_raw=transaction.descriptionRaw,
                merchant_normalized=transaction.merchantNormalized,
                amount_minor=transaction.amount.amountMinor,
                currency=transaction.amount.currency,
                status=transaction.status,
                is_recurring_candidate=transaction.isRecurringCandidate,
            )
            self.session.add(item)

        self.session.commit()
        self.session.refresh(item)
        return _tx_to_response(item)

    def clear(self) -> None:
        self.session.execute(delete(Transaction))
        self.session.commit()


class SqlAlchemyConnectionRepository(ConnectionRepository):
    def __init__(self, session: Session):
        self.session = session

    def list(self) -> List[ConnectionResponse]:
        items = self.session.scalars(select(Connection)).all()
        return [_conn_to_response(c) for c in items]

    def get_by_id(self, connection_id: str) -> Optional[ConnectionResponse]:
        item = self.session.get(Connection, connection_id)
        return _conn_to_response(item) if item else None

    def sync(self, connection_id: Optional[str] = None) -> bool:
        now_iso = datetime.now(timezone.utc).isoformat()
        if connection_id:
            c = self.session.get(Connection, connection_id)
            if c:
                c.last_synced_at = now_iso
                c.status = "connected"
                self.session.commit()
                return True
            return False

        conns = self.session.scalars(select(Connection)).all()
        for c in conns:
            c.last_synced_at = now_iso
            c.status = "connected"
        self.session.commit()
        return True

    def disconnect(self, connection_id: str, delete_data: bool = False) -> bool:
        c = self.session.get(Connection, connection_id)
        if not c:
            return False

        c.status = "disconnected"
        if delete_data:
            self.session.delete(c)
        self.session.commit()
        return True

    def add(self, connection: ConnectionResponse) -> ConnectionResponse:
        existing = self.session.get(Connection, connection.id)
        if existing:
            existing.name = connection.name
            existing.type = connection.type
            existing.provider = connection.provider
            existing.status = connection.status
            existing.last_synced_at = connection.lastSyncedAt
            item = existing
        else:
            item = Connection(
                id=connection.id,
                name=connection.name,
                type=connection.type,
                provider=connection.provider,
                status=connection.status,
                last_synced_at=connection.lastSyncedAt,
            )
            self.session.add(item)

        self.session.commit()
        self.session.refresh(item)
        return _conn_to_response(item)

    def clear(self) -> None:
        self.session.execute(delete(Connection))
        self.session.commit()
