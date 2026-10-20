from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Dict, Generator, List, Optional
import uuid

from sqlalchemy import func, or_
from sqlalchemy.orm import Session, sessionmaker

from ..auth.security import hash_password, verify_password
from ..database import Base, engine as default_engine, SessionLocal as default_sessionmaker
from ..models import (
    DashboardSummary,
    EmailEvidence,
    Finding,
    FindingBrief,
    FindingDetail,
    FindingEvidenceItem,
    IntegrationConnection,
    Money,
    Paginated,
    RecentChangeItem,
    ReviewInput,
    SpendByCategoryItem,
    Subscription,
    SubscriptionDetail,
    SubscriptionPatch,
    Transaction,
    UpcomingItem,
    User,
    UserReview,
    Workspace,
)
from .db_models import (
    EmailEvidenceDB,
    FindingDB,
    IntegrationConnectionDB,
    SubscriptionDB,
    TransactionDB,
    UserDB,
    UserReviewDB,
    WorkspaceDB,
)
from .seeds import get_initial_seed_data


class DatabaseStore:
    """
    Database-agnostic store backed by SQLAlchemy.
    Works seamlessly with SQLite, PostgreSQL, MySQL, etc.
    """

    def __init__(self, engine=None, session_factory=None):
        self.engine = engine or default_engine
        self.Session = session_factory or default_sessionmaker
        self._init_db()

    def _init_db(self):
        # Create all tables if they don't exist
        Base.metadata.create_all(bind=self.engine)
        self.seed_if_empty()

    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        session: Session = self.Session()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def reset(self):
        """Drops all tables and reseeds initial data (useful for test isolation)."""
        Base.metadata.drop_all(bind=self.engine)
        Base.metadata.create_all(bind=self.engine)
        self.seed_all()

    def seed_all(self):
        data = get_initial_seed_data()
        with self.get_session() as s:
            # 1. User
            u = data["user"]
            pwd = data["user_passwords"][u.id]
            user_db = UserDB(
                id=u.id,
                email=u.email.lower(),
                password_hash=pwd,
                created_at=u.createdAt,
            )
            s.add(user_db)

            # 2. Workspace
            ws = data["workspace"]
            ws_db = WorkspaceDB(
                id=ws.id,
                name=ws.name,
                owner_user_id=ws.ownerUserId,
                base_currency=ws.baseCurrency,
                created_at=ws.createdAt,
            )
            s.add(ws_db)

            # 3. Connections
            for c in data["connections"]:
                c_db = IntegrationConnectionDB(
                    id=c.id,
                    kind=c.kind,
                    provider=c.provider,
                    display_name=c.displayName,
                    status=c.status,
                    sync_state=c.syncState,
                    scopes_granted=c.scopesGranted,
                    last_sync_at=c.lastSyncAt,
                    last_sync_status=c.lastSyncStatus,
                    created_at=c.createdAt,
                )
                s.add(c_db)

            # 4. Subscriptions
            for sub in data["subscriptions"]:
                sub_db = SubscriptionDB(
                    id=sub.id,
                    vendor_name=sub.vendorName,
                    vendor_domain=sub.vendorDomain,
                    category=sub.category,
                    display_name=sub.displayName,
                    status=sub.status,
                    billing_interval=sub.billingInterval,
                    expected_amount_minor=sub.expectedAmount.amountMinor if sub.expectedAmount else None,
                    expected_amount_currency=sub.expectedAmount.currency if sub.expectedAmount else None,
                    monthly_equivalent_minor=sub.monthlyEquivalent.amountMinor if sub.monthlyEquivalent else None,
                    monthly_equivalent_currency=sub.monthlyEquivalent.currency if sub.monthlyEquivalent else None,
                    estimated_next_charge_at=sub.estimatedNextChargeAt,
                    detection_confidence=sub.detectionConfidence,
                    detection_explanation=sub.detectionExplanation,
                    last_detected_at=sub.lastDetectedAt,
                    note=sub.note,
                )
                s.add(sub_db)

            # 5. Transactions
            for tx in data["transactions"]:
                tx_db = TransactionDB(
                    id=tx.id,
                    connection_id=tx.connectionId,
                    account_name=tx.accountName,
                    posted_at=tx.postedAt,
                    amount_minor=tx.amount.amountMinor,
                    amount_currency=tx.amount.currency,
                    description_raw=tx.descriptionRaw,
                    merchant_normalized=tx.merchantNormalized,
                    status=tx.status,
                    is_recurring_candidate=tx.isRecurringCandidate,
                    subscription_id=tx.subscriptionId,
                )
                s.add(tx_db)

            # 6. Evidence
            for sub_id, ev_list in data["evidence"].items():
                for ev in ev_list:
                    ev_db = EmailEvidenceDB(
                        id=ev.id,
                        subscription_id=sub_id,
                        received_at=ev.receivedAt,
                        sender_domain=ev.senderDomain,
                        subject_minimized=ev.subjectMinimized,
                        evidence_type=ev.evidenceType,
                        amount_minor=ev.amount.amountMinor if ev.amount else None,
                        amount_currency=ev.amount.currency if ev.amount else None,
                        invoice_date=ev.invoiceDate,
                        extraction_confidence=ev.extractionConfidence,
                        match_score=ev.matchScore,
                        match_status=ev.matchStatus,
                        match_reason=ev.matchReason,
                    )
                    s.add(ev_db)

            # 7. Findings
            for f in data["findings"]:
                f_db = FindingDB(
                    id=f.id,
                    subscription_id=f.subscriptionId,
                    subscription_name=f.subscriptionName,
                    finding_type=f.findingType,
                    severity=f.severity,
                    status=f.status,
                    title=f.title,
                    explanation=f.explanation,
                    estimated_impact_minor=f.estimatedImpact.amountMinor if f.estimatedImpact else None,
                    estimated_impact_currency=f.estimatedImpact.currency if f.estimatedImpact else None,
                    confidence=f.confidence,
                    rule_version=f.ruleVersion,
                    created_at=f.createdAt,
                    updated_at=f.updatedAt,
                )
                s.add(f_db)

    def seed_if_empty(self):
        with self.get_session() as s:
            user_count = s.query(UserDB).count()
            if user_count == 0:
                self.seed_all()

    # --- Auth & User ---
    def authenticate_user(self, email: str, password: str) -> Optional[User]:
        email_clean = email.strip().lower()
        with self.get_session() as s:
            user = s.query(UserDB).filter(func.lower(UserDB.email) == email_clean).first()
            if not user:
                # Demo convenience: auto-create user & workspace if not found
                new_id = f"usr_{uuid.uuid4().hex[:8]}"
                new_user = UserDB(
                    id=new_id,
                    email=email_clean,
                    password_hash=hash_password(password),
                    created_at=datetime.now(timezone.utc).isoformat(),
                )
                s.add(new_user)
                new_ws = WorkspaceDB(
                    id=f"ws_{uuid.uuid4().hex[:8]}",
                    name=f"{email_clean.split('@')[0].capitalize()} Workspace",
                    owner_user_id=new_id,
                    base_currency="USD",
                    created_at=datetime.now(timezone.utc).isoformat(),
                )
                s.add(new_ws)
                s.flush()
                return new_user.to_pydantic()

            if verify_password(password, user.password_hash):
                return user.to_pydantic()
            return None

    def get_user_by_id(self, user_id: str) -> Optional[User]:
        with self.get_session() as s:
            user = s.query(UserDB).filter(UserDB.id == user_id).first()
            return user.to_pydantic() if user else None

    def get_workspace_for_user(self, user_id: str) -> Workspace:
        with self.get_session() as s:
            ws = s.query(WorkspaceDB).filter(WorkspaceDB.owner_user_id == user_id).first()
            if ws:
                return ws.to_pydantic()
            # Fallback to any workspace or create a default
            first = s.query(WorkspaceDB).first()
            if first:
                return first.to_pydantic()
            new_ws = WorkspaceDB(
                id=f"ws_{uuid.uuid4().hex[:8]}",
                name="Default Workspace",
                owner_user_id=user_id,
                base_currency="USD",
                created_at=datetime.now(timezone.utc).isoformat(),
            )
            s.add(new_ws)
            s.flush()
            return new_ws.to_pydantic()

    def delete_account(self, user_id: str) -> None:
        with self.get_session() as s:
            user = s.query(UserDB).filter(UserDB.id == user_id).first()
            if user:
                s.delete(user)

    # --- Integrations ---
    def list_integrations(self) -> List[IntegrationConnection]:
        with self.get_session() as s:
            conns = s.query(IntegrationConnectionDB).all()
            return [c.to_pydantic() for c in conns]

    def connect_bank(self) -> IntegrationConnection:
        now_iso = datetime.now(timezone.utc).isoformat()
        with self.get_session() as s:
            conn = s.query(IntegrationConnectionDB).filter(IntegrationConnectionDB.id == "conn_bank").first()
            if not conn:
                conn = IntegrationConnectionDB(
                    id="conn_bank",
                    kind="bank",
                    provider="plaid",
                    display_name="Chase Business ••4821",
                    status="active",
                    sync_state="up_to_date",
                    scopes_granted=["transactions:read", "accounts:read"],
                    last_sync_at=now_iso,
                    last_sync_status="success",
                    created_at=now_iso,
                )
                s.add(conn)
            else:
                conn.status = "active"
                conn.sync_state = "up_to_date"
                conn.last_sync_at = now_iso
                conn.last_sync_status = "success"
            s.flush()
            return conn.to_pydantic()

    def connect_gmail(self) -> IntegrationConnection:
        now_iso = datetime.now(timezone.utc).isoformat()
        with self.get_session() as s:
            conn = s.query(IntegrationConnectionDB).filter(IntegrationConnectionDB.id == "conn_gmail").first()
            if not conn:
                conn = IntegrationConnectionDB(
                    id="conn_gmail",
                    kind="gmail",
                    provider="google",
                    display_name="alex@studio.dev",
                    status="active",
                    sync_state="up_to_date",
                    scopes_granted=["gmail.readonly"],
                    last_sync_at=now_iso,
                    last_sync_status="success",
                    created_at=now_iso,
                )
                s.add(conn)
            else:
                conn.status = "active"
                conn.sync_state = "up_to_date"
                conn.last_sync_at = now_iso
                conn.last_sync_status = "success"
            s.flush()
            return conn.to_pydantic()

    def sync_integration(self, connection_id: str) -> Optional[IntegrationConnection]:
        now_iso = datetime.now(timezone.utc).isoformat()
        with self.get_session() as s:
            conn = s.query(IntegrationConnectionDB).filter(IntegrationConnectionDB.id == connection_id).first()
            if not conn:
                return None
            conn.last_sync_at = now_iso
            conn.last_sync_status = "success"
            conn.sync_state = "up_to_date"
            s.flush()
            return conn.to_pydantic()

    def disconnect_integration(self, connection_id: str, delete_data: bool = False) -> bool:
        with self.get_session() as s:
            conn = s.query(IntegrationConnectionDB).filter(IntegrationConnectionDB.id == connection_id).first()
            if not conn:
                return False
            conn.status = "disconnected"
            conn.sync_state = "disconnected"
            if delete_data:
                s.query(TransactionDB).filter(TransactionDB.connection_id == connection_id).delete(synchronize_session=False)
            return True

    # --- Transactions ---
    def list_transactions(
        self,
        q: Optional[str] = None,
        status: Optional[str] = None,
        subscription_id: Optional[str] = None,
        page: int = 1,
        page_size: int = 50,
    ) -> Paginated[Transaction]:
        with self.get_session() as s:
            query = s.query(TransactionDB)
            if q:
                pattern = f"%{q.strip()}%"
                query = query.filter(
                    or_(
                        TransactionDB.description_raw.ilike(pattern),
                        TransactionDB.merchant_normalized.ilike(pattern),
                    )
                )
            if status:
                query = query.filter(TransactionDB.status == status)
            if subscription_id:
                query = query.filter(TransactionDB.subscription_id == subscription_id)

            total = query.count()
            query = query.order_by(TransactionDB.posted_at.desc())
            offset = max(0, (page - 1) * page_size)
            rows = query.offset(offset).limit(page_size).all()

            items = [r.to_pydantic() for r in rows]
            has_more = (offset + len(items)) < total

            return Paginated(
                items=items,
                total=total,
                page=page,
                pageSize=page_size,
                hasMore=has_more,
            )

    # --- Subscriptions ---
    def list_subscriptions(self) -> List[Subscription]:
        with self.get_session() as s:
            subs = s.query(SubscriptionDB).all()
            return [sub.to_pydantic() for sub in subs]

    def get_subscription_detail(self, subscription_id: str) -> Optional[SubscriptionDetail]:
        with self.get_session() as s:
            sub = s.query(SubscriptionDB).filter(SubscriptionDB.id == subscription_id).first()
            if not sub:
                return None
            txs = (
                s.query(TransactionDB)
                .filter(TransactionDB.subscription_id == subscription_id)
                .order_by(TransactionDB.posted_at.desc())
                .all()
            )
            evs = (
                s.query(EmailEvidenceDB)
                .filter(EmailEvidenceDB.subscription_id == subscription_id)
                .order_by(EmailEvidenceDB.received_at.desc())
                .all()
            )
            fnds = (
                s.query(FindingDB)
                .filter(FindingDB.subscription_id == subscription_id)
                .all()
            )

            return SubscriptionDetail(
                **sub.to_pydantic().model_dump(),
                transactions=[t.to_pydantic() for t in txs],
                evidence=[e.to_pydantic() for e in evs],
                findings=[f.to_brief() for f in fnds],
            )

    def update_subscription(self, subscription_id: str, patch: SubscriptionPatch) -> Optional[Subscription]:
        with self.get_session() as s:
            sub = s.query(SubscriptionDB).filter(SubscriptionDB.id == subscription_id).first()
            if not sub:
                return None
            if patch.displayName is not None:
                sub.display_name = patch.displayName
            if patch.category is not None:
                sub.category = patch.category
            if patch.billingInterval is not None:
                sub.billing_interval = patch.billingInterval
            if patch.note is not None:
                sub.note = patch.note
            if patch.status is not None:
                sub.status = patch.status
            s.flush()
            return sub.to_pydantic()

    def confirm_subscription(self, subscription_id: str) -> Optional[Subscription]:
        with self.get_session() as s:
            sub = s.query(SubscriptionDB).filter(SubscriptionDB.id == subscription_id).first()
            if not sub:
                return None
            sub.status = "confirmed"
            s.flush()
            return sub.to_pydantic()

    def dismiss_subscription(self, subscription_id: str) -> Optional[Subscription]:
        with self.get_session() as s:
            sub = s.query(SubscriptionDB).filter(SubscriptionDB.id == subscription_id).first()
            if not sub:
                return None
            sub.status = "dismissed"
            s.flush()
            return sub.to_pydantic()

    # --- Findings ---
    def list_findings(
        self,
        status: Optional[str] = None,
        finding_type: Optional[str] = None,
    ) -> List[Finding]:
        with self.get_session() as s:
            query = s.query(FindingDB)
            if status:
                if status == "open":
                    query = query.filter(FindingDB.status.in_(["new", "reviewing"]))
                else:
                    query = query.filter(FindingDB.status == status)
            if finding_type:
                query = query.filter(FindingDB.finding_type == finding_type)
            rows = query.order_by(FindingDB.created_at.desc()).all()
            return [r.to_pydantic() for r in rows]

    def get_finding_detail(self, finding_id: str) -> Optional[FindingDetail]:
        with self.get_session() as s:
            f = s.query(FindingDB).filter(FindingDB.id == finding_id).first()
            if not f:
                return None

            txs = (
                s.query(TransactionDB)
                .filter(TransactionDB.subscription_id == f.subscription_id)
                .order_by(TransactionDB.posted_at.desc())
                .limit(4)
                .all()
            )
            evs = (
                s.query(EmailEvidenceDB)
                .filter(EmailEvidenceDB.subscription_id == f.subscription_id)
                .order_by(EmailEvidenceDB.received_at.desc())
                .limit(2)
                .all()
            )

            evidence_items: List[FindingEvidenceItem] = []
            for i, tx in enumerate(txs):
                evidence_items.append(
                    FindingEvidenceItem(
                        role="trigger" if i == 0 else "supporting",
                        explanation="Most recent charge that triggered this rule."
                        if i == 0
                        else "Earlier charge in the same series.",
                        transaction=tx.to_pydantic(),
                    )
                )
            for ev in evs:
                evidence_items.append(
                    FindingEvidenceItem(
                        role="context",
                        explanation="Matched email evidence.",
                        email=ev.to_pydantic(),
                    )
                )

            reviews = (
                s.query(UserReviewDB)
                .filter(UserReviewDB.finding_id == finding_id)
                .order_by(UserReviewDB.created_at.desc())
                .all()
            )

            return FindingDetail(
                **f.to_pydantic().model_dump(),
                evidence=evidence_items,
                reviews=[r.to_pydantic() for r in reviews],
            )

    def review_finding(self, finding_id: str, input_data: ReviewInput) -> Optional[FindingDetail]:
        with self.get_session() as s:
            f = s.query(FindingDB).filter(FindingDB.id == finding_id).first()
            if not f:
                return None

            status_map = {
                "confirm": "confirmed",
                "dismiss": "dismissed",
                "mark_reviewing": "reviewing",
                "resolve": "resolved",
            }
            f.status = status_map.get(input_data.decision, f.status)
            f.updated_at = datetime.now(timezone.utc).isoformat()

            savings_minor = input_data.estimatedSavings.amountMinor if input_data.estimatedSavings else None
            savings_currency = input_data.estimatedSavings.currency if input_data.estimatedSavings else None

            rev = UserReviewDB(
                id=f"rev_{uuid.uuid4().hex[:8]}",
                finding_id=finding_id,
                decision=input_data.decision,
                note=input_data.note,
                estimated_savings_minor=savings_minor,
                estimated_savings_currency=savings_currency,
                created_at=datetime.now(timezone.utc).isoformat(),
            )
            s.add(rev)
            s.flush()

        return self.get_finding_detail(finding_id)

    # --- Dashboard Summary ---
    def get_dashboard_summary(self) -> DashboardSummary:
        with self.get_session() as s:
            active_subs = (
                s.query(SubscriptionDB)
                .filter(SubscriptionDB.status.notin_(["dismissed", "inactive"]))
                .all()
            )

            def to_usd(minor: Optional[int], cur: Optional[str]) -> int:
                if minor is None:
                    return 0
                return round(minor * 1.08) if cur == "EUR" else minor

            monthly = sum(
                to_usd(sub.monthly_equivalent_minor, sub.monthly_equivalent_currency)
                for sub in active_subs
            )

            open_findings = (
                s.query(FindingDB)
                .filter(FindingDB.status.in_(["new", "reviewing"]))
                .all()
            )

            categories: Dict[str, int] = {}
            for sub in active_subs:
                cat = sub.category or "Other"
                amt = to_usd(sub.monthly_equivalent_minor, sub.monthly_equivalent_currency)
                categories[cat] = categories.get(cat, 0) + amt

            reviews = s.query(UserReviewDB).all()
            total_user_savings = sum(
                to_usd(r.estimated_savings_minor, r.estimated_savings_currency)
                for r in reviews
                if r.estimated_savings_minor is not None
            )

            potential_savings_minor = sum(
                to_usd(f.estimated_impact_minor, f.estimated_impact_currency)
                for f in open_findings
                if f.estimated_impact_minor and f.finding_type != "renewal_approaching"
            )

            upcoming_subs = [sub for sub in active_subs if sub.estimated_next_charge_at]
            upcoming_subs.sort(key=lambda x: x.estimated_next_charge_at or "")
            upcoming = [
                UpcomingItem(
                    subscriptionId=sub.id,
                    name=sub.display_name,
                    date=sub.estimated_next_charge_at,
                    amount=Money(amountMinor=sub.expected_amount_minor, currency=sub.expected_amount_currency or "USD")
                    if sub.expected_amount_minor is not None else None,
                )
                for sub in upcoming_subs[:5]
            ]

            recent_changes = [
                RecentChangeItem(
                    subscriptionId="sub_unknown",
                    name="PAYPAL *DGTLSRV",
                    kind="new",
                    date=datetime.now(timezone.utc).isoformat(),
                    detail="New recurring charge detected",
                ),
                RecentChangeItem(
                    subscriptionId="sub_notion",
                    name="Notion Plus",
                    kind="price_change",
                    date=datetime.now(timezone.utc).isoformat(),
                    detail="$10.00 → $12.00",
                ),
                RecentChangeItem(
                    subscriptionId="sub_adobe",
                    name="Adobe Creative Cloud",
                    kind="price_change",
                    date=datetime.now(timezone.utc).isoformat(),
                    detail="$54.99 → $59.99",
                ),
            ]

            spend_by_category = [
                SpendByCategoryItem(category=c, monthly=Money(amountMinor=amt, currency="USD"))
                for c, amt in sorted(categories.items(), key=lambda item: item[1], reverse=True)
            ]

            conns = s.query(IntegrationConnectionDB).all()

            return DashboardSummary(
                monthlyRecurringSpend=Money(amountMinor=monthly, currency="USD"),
                annualizedSpend=Money(amountMinor=monthly * 12, currency="USD"),
                subscriptionCount=len(active_subs),
                candidateCount=len([sub for sub in active_subs if sub.status == "candidate"]),
                openFindingsCount=len(open_findings),
                potentialSavings=Money(amountMinor=potential_savings_minor, currency="USD"),
                userEstimatedSavings=Money(amountMinor=total_user_savings, currency="USD"),
                upcoming=upcoming,
                recentChanges=recent_changes,
                spendByCategory=spend_by_category,
                connections=[c.to_pydantic() for c in conns],
            )


# Global singleton instance backed by database
store = DatabaseStore()
