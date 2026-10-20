from datetime import datetime, timezone
import threading
from typing import Dict, List, Optional
import uuid

from ..auth.security import hash_password, verify_password
from ..models import (
    DashboardSummary,
    EmailEvidence,
    Finding,
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
from .seeds import get_initial_seed_data


class InMemoryStore:
    def __init__(self):
        self._lock = threading.RLock()
        self.reset()

    def reset(self):
        with self._lock:
            data = get_initial_seed_data()
            self.users: Dict[str, User] = {data["user"].id: data["user"]}
            self.user_emails: Dict[str, str] = {data["user"].email.lower(): data["user"].id}
            self.user_passwords: Dict[str, str] = data["user_passwords"]
            self.workspaces: Dict[str, Workspace] = {data["workspace"].id: data["workspace"]}
            self.connections: Dict[str, IntegrationConnection] = {c.id: c for c in data["connections"]}
            self.subscriptions: Dict[str, Subscription] = {s.id: s for s in data["subscriptions"]}
            self.transactions: List[Transaction] = list(data["transactions"])
            self.evidence: Dict[str, List[EmailEvidence]] = {
                k: list(v) for k, v in data["evidence"].items()
            }
            self.findings: Dict[str, Finding] = {f.id: f for f in data["findings"]}
            self.reviews: Dict[str, List[UserReview]] = {}

    # --- Auth & User ---
    def authenticate_user(self, email: str, password: str) -> Optional[User]:
        with self._lock:
            email_clean = email.strip().lower()
            user_id = self.user_emails.get(email_clean)
            if not user_id:
                # For demo convenience, allow auto-creating a new demo user if not found
                new_id = f"usr_{uuid.uuid4().hex[:8]}"
                new_user = User(
                    id=new_id,
                    email=email_clean,
                    createdAt=datetime.now(timezone.utc).isoformat(),
                )
                self.users[new_id] = new_user
                self.user_emails[email_clean] = new_id
                self.user_passwords[new_id] = hash_password(password)

                new_ws = Workspace(
                    id=f"ws_{uuid.uuid4().hex[:8]}",
                    name=f"{email_clean.split('@')[0].capitalize()} Workspace",
                    ownerUserId=new_id,
                    baseCurrency="USD",
                    createdAt=datetime.now(timezone.utc).isoformat(),
                )
                self.workspaces[new_ws.id] = new_ws
                return new_user

            hashed = self.user_passwords.get(user_id)
            if hashed and verify_password(password, hashed):
                return self.users.get(user_id)
            return None

    def get_user_by_id(self, user_id: str) -> Optional[User]:
        with self._lock:
            return self.users.get(user_id)

    def get_workspace_for_user(self, user_id: str) -> Workspace:
        with self._lock:
            for ws in self.workspaces.values():
                if ws.ownerUserId == user_id:
                    return ws
            # Fallback default workspace
            first = next(iter(self.workspaces.values()), None)
            if first:
                return first
            new_ws = Workspace(
                id=f"ws_{uuid.uuid4().hex[:8]}",
                name="Default Workspace",
                ownerUserId=user_id,
                baseCurrency="USD",
                createdAt=datetime.now(timezone.utc).isoformat(),
            )
            self.workspaces[new_ws.id] = new_ws
            return new_ws

    def delete_account(self, user_id: str) -> None:
        with self._lock:
            # Purge user data
            if user_id in self.users:
                email = self.users[user_id].email.lower()
                self.user_emails.pop(email, None)
                self.users.pop(user_id, None)
                self.user_passwords.pop(user_id, None)

            # Purge workspaces, transactions, findings, subscriptions
            ws_ids = [w.id for w in self.workspaces.values() if w.ownerUserId == user_id]
            for w_id in ws_ids:
                self.workspaces.pop(w_id, None)

    # --- Integrations ---
    def list_integrations(self) -> List[IntegrationConnection]:
        with self._lock:
            return list(self.connections.values())

    def connect_bank(self) -> IntegrationConnection:
        with self._lock:
            conn = self.connections.get("conn_bank")
            if not conn:
                conn = IntegrationConnection(
                    id="conn_bank",
                    kind="bank",
                    provider="plaid",
                    displayName="Chase Business ••4821",
                    status="active",
                    syncState="up_to_date",
                    scopesGranted=["transactions:read", "accounts:read"],
                    lastSyncAt=datetime.now(timezone.utc).isoformat(),
                    lastSyncStatus="success",
                    createdAt=datetime.now(timezone.utc).isoformat(),
                )
                self.connections[conn.id] = conn
            else:
                conn.status = "active"
                conn.syncState = "up_to_date"
                conn.lastSyncAt = datetime.now(timezone.utc).isoformat()
                conn.lastSyncStatus = "success"
            return conn

    def connect_gmail(self) -> IntegrationConnection:
        with self._lock:
            conn = self.connections.get("conn_gmail")
            if not conn:
                conn = IntegrationConnection(
                    id="conn_gmail",
                    kind="gmail",
                    provider="google",
                    displayName="alex@studio.dev",
                    status="active",
                    syncState="up_to_date",
                    scopesGranted=["gmail.readonly"],
                    lastSyncAt=datetime.now(timezone.utc).isoformat(),
                    lastSyncStatus="success",
                    createdAt=datetime.now(timezone.utc).isoformat(),
                )
                self.connections[conn.id] = conn
            else:
                conn.status = "active"
                conn.syncState = "up_to_date"
                conn.lastSyncAt = datetime.now(timezone.utc).isoformat()
                conn.lastSyncStatus = "success"
            return conn

    def sync_integration(self, connection_id: str) -> Optional[IntegrationConnection]:
        with self._lock:
            conn = self.connections.get(connection_id)
            if not conn:
                return None
            conn.lastSyncAt = datetime.now(timezone.utc).isoformat()
            conn.lastSyncStatus = "success"
            conn.syncState = "up_to_date"
            return conn

    def disconnect_integration(self, connection_id: str, delete_data: bool = False) -> bool:
        with self._lock:
            conn = self.connections.get(connection_id)
            if not conn:
                return False
            conn.status = "disconnected"
            conn.syncState = "disconnected"
            if delete_data:
                # Remove transactions associated with this connection
                self.transactions = [t for t in self.transactions if t.connectionId != connection_id]
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
        with self._lock:
            filtered = list(self.transactions)
            if q:
                q_lower = q.lower()
                filtered = [
                    t
                    for t in filtered
                    if q_lower in t.descriptionRaw.lower()
                    or (t.merchantNormalized and q_lower in t.merchantNormalized.lower())
                ]
            if status:
                filtered = [t for t in filtered if t.status == status]
            if subscription_id:
                filtered = [t for t in filtered if t.subscriptionId == subscription_id]

            total = len(filtered)
            start = (page - 1) * page_size
            end = start + page_size
            items = filtered[start:end]
            has_more = end < total

            return Paginated(
                items=items,
                total=total,
                page=page,
                pageSize=page_size,
                hasMore=has_more,
            )

    # --- Subscriptions ---
    def list_subscriptions(self) -> List[Subscription]:
        with self._lock:
            return list(self.subscriptions.values())

    def get_subscription_detail(self, subscription_id: str) -> Optional[SubscriptionDetail]:
        with self._lock:
            sub = self.subscriptions.get(subscription_id)
            if not sub:
                return None
            txs = [t for t in self.transactions if t.subscriptionId == subscription_id]
            evs = self.evidence.get(subscription_id, [])
            fnds = [
                f
                for f in self.findings.values()
                if f.subscriptionId == subscription_id
            ]

            return SubscriptionDetail(
                **sub.model_dump(),
                transactions=txs,
                evidence=evs,
                findings=fnds,
            )

    def update_subscription(self, subscription_id: str, patch: SubscriptionPatch) -> Optional[Subscription]:
        with self._lock:
            sub = self.subscriptions.get(subscription_id)
            if not sub:
                return None
            data = sub.model_dump()
            patch_data = patch.model_dump(exclude_unset=True)
            for k, v in patch_data.items():
                if v is not None:
                    data[k] = v
            updated = Subscription(**data)
            self.subscriptions[subscription_id] = updated
            return updated

    def confirm_subscription(self, subscription_id: str) -> Optional[Subscription]:
        with self._lock:
            sub = self.subscriptions.get(subscription_id)
            if not sub:
                return None
            sub.status = "confirmed"
            return sub

    def dismiss_subscription(self, subscription_id: str) -> Optional[Subscription]:
        with self._lock:
            sub = self.subscriptions.get(subscription_id)
            if not sub:
                return None
            sub.status = "dismissed"
            return sub

    # --- Findings ---
    def list_findings(
        self,
        status: Optional[str] = None,
        finding_type: Optional[str] = None,
    ) -> List[Finding]:
        with self._lock:
            res = list(self.findings.values())
            if status:
                res = [f for f in res if f.status == status]
            if finding_type:
                res = [f for f in res if f.findingType == finding_type]
            return res

    def get_finding_detail(self, finding_id: str) -> Optional[FindingDetail]:
        with self._lock:
            f = self.findings.get(finding_id)
            if not f:
                return None
            txs = [t for t in self.transactions if t.subscriptionId == f.subscriptionId][:4]
            evs = self.evidence.get(f.subscriptionId or "", [])[-2:]

            evidence_items: List[FindingEvidenceItem] = []
            for i, tx in enumerate(txs):
                evidence_items.append(
                    FindingEvidenceItem(
                        role="trigger" if i == 0 else "supporting",
                        explanation="Most recent charge that triggered this rule."
                        if i == 0
                        else "Earlier charge in the same series.",
                        transaction=tx,
                    )
                )
            for ev in evs:
                evidence_items.append(
                    FindingEvidenceItem(
                        role="context",
                        explanation="Matched email evidence.",
                        email=ev,
                    )
                )

            user_reviews = self.reviews.get(finding_id, [])

            return FindingDetail(
                **f.model_dump(),
                evidence=evidence_items,
                reviews=user_reviews,
            )

    def review_finding(self, finding_id: str, input_data: ReviewInput) -> Optional[FindingDetail]:
        with self._lock:
            f = self.findings.get(finding_id)
            if not f:
                return None

            status_map = {
                "confirm": "confirmed",
                "dismiss": "dismissed",
                "mark_reviewing": "reviewing",
                "resolve": "resolved",
            }
            f.status = status_map.get(input_data.decision, f.status)
            f.updatedAt = datetime.now(timezone.utc).isoformat()

            rev = UserReview(
                id=f"rev_{uuid.uuid4().hex[:8]}",
                decision=input_data.decision,
                note=input_data.note,
                estimatedSavings=input_data.estimatedSavings,
                createdAt=datetime.now(timezone.utc).isoformat(),
            )
            if finding_id not in self.reviews:
                self.reviews[finding_id] = []
            self.reviews[finding_id].append(rev)

            return self.get_finding_detail(finding_id)

    # --- Dashboard Summary ---
    def get_dashboard_summary(self) -> DashboardSummary:
        with self._lock:
            active = [s for s in self.subscriptions.values() if s.status not in ("dismissed", "inactive")]

            def to_usd(m: Money) -> int:
                return round(m.amountMinor * 1.08) if m.currency == "EUR" else m.amountMinor

            monthly = sum(to_usd(s.monthlyEquivalent) for s in active if s.monthlyEquivalent)
            open_findings = [f for f in self.findings.values() if f.status in ("new", "reviewing")]

            categories: Dict[str, int] = {}
            for s in active:
                cat = s.category or "Other"
                amt = to_usd(s.monthlyEquivalent) if s.monthlyEquivalent else 0
                categories[cat] = categories.get(cat, 0) + amt

            total_user_savings = sum(
                rev.estimatedSavings.amountMinor
                for rev_list in self.reviews.values()
                for rev in rev_list
                if rev.estimatedSavings
            )

            potential_savings_minor = sum(
                to_usd(f.estimatedImpact)
                for f in open_findings
                if f.estimatedImpact and f.findingType != "renewal_approaching"
            )

            upcoming = [
                UpcomingItem(
                    subscriptionId=s.id,
                    name=s.displayName,
                    date=s.estimatedNextChargeAt,
                    amount=s.expectedAmount,
                )
                for s in sorted(
                    [s for s in active if s.estimatedNextChargeAt],
                    key=lambda x: x.estimatedNextChargeAt or "",
                )[:5]
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

            return DashboardSummary(
                monthlyRecurringSpend=Money(amountMinor=monthly, currency="USD"),
                annualizedSpend=Money(amountMinor=monthly * 12, currency="USD"),
                subscriptionCount=len(active),
                candidateCount=len([s for s in active if s.status == "candidate"]),
                openFindingsCount=len(open_findings),
                potentialSavings=Money(amountMinor=potential_savings_minor, currency="USD"),
                userEstimatedSavings=Money(amountMinor=total_user_savings, currency="USD"),
                upcoming=upcoming,
                recentChanges=recent_changes,
                spendByCategory=spend_by_category,
                connections=list(self.connections.values()),
            )


# Global singleton instance
store = InMemoryStore()
