from datetime import datetime, timezone
import threading
from typing import Dict, List, Optional

from schemas import (
    BillingEvidenceResponse,
    ConnectionResponse,
    FindingActionRequest,
    FindingResponse,
    Money,
    OverviewMetricsResponse,
    SubscriptionResponse,
    TransactionResponse,
)
from .base import (
    ConnectionRepository,
    FindingRepository,
    SubscriptionRepository,
    TransactionRepository,
)


class InMemorySubscriptionRepository(SubscriptionRepository):
    def __init__(self, data: Optional[Dict[str, SubscriptionResponse]] = None):
        self._lock = threading.RLock()
        self._subs: Dict[str, SubscriptionResponse] = data or {}

    def list(
        self,
        status: Optional[str] = None,
        cadence: Optional[str] = None,
        search: Optional[str] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> List[SubscriptionResponse]:
        with self._lock:
            res = list(self._subs.values())
            if status:
                res = [s for s in res if s.status == status]
            if cadence:
                res = [s for s in res if s.billingInterval == cadence]
            if search:
                q = search.lower()
                res = [s for s in res if q in s.name.lower() or (s.vendorDomain and q in s.vendorDomain.lower())]
            return res[skip : skip + limit]

    def get_by_id(self, subscription_id: str) -> Optional[SubscriptionResponse]:
        with self._lock:
            return self._subs.get(subscription_id)

    def update(
        self,
        subscription_id: str,
        name: Optional[str] = None,
        billing_interval: Optional[str] = None,
        category: Optional[str] = None,
        status: Optional[str] = None,
        note: Optional[str] = None,
    ) -> Optional[SubscriptionResponse]:
        with self._lock:
            sub = self._subs.get(subscription_id)
            if not sub:
                return None
            data = sub.model_dump()
            if name is not None:
                data["name"] = name
            if billing_interval is not None:
                data["billingInterval"] = billing_interval
            if category is not None:
                data["category"] = category
            if status is not None:
                data["status"] = status
            updated = SubscriptionResponse(**data)
            self._subs[subscription_id] = updated
            return updated

    def add(self, subscription: SubscriptionResponse) -> SubscriptionResponse:
        with self._lock:
            self._subs[subscription.id] = subscription
            return subscription

    def clear(self) -> None:
        with self._lock:
            self._subs.clear()


class InMemoryFindingRepository(FindingRepository):
    def __init__(self, data: Optional[Dict[str, FindingResponse]] = None):
        self._lock = threading.RLock()
        self._findings: Dict[str, FindingResponse] = data or {}

    def list(
        self,
        status: Optional[str] = None,
        finding_type: Optional[str] = None,
    ) -> List[FindingResponse]:
        with self._lock:
            res = list(self._findings.values())
            if status:
                res = [f for f in res if f.status == status]
            if finding_type:
                res = [f for f in res if f.type == finding_type]
            return res

    def get_by_id(self, finding_id: str) -> Optional[FindingResponse]:
        with self._lock:
            return self._findings.get(finding_id)

    def apply_action(
        self,
        finding_id: str,
        action: FindingActionRequest,
    ) -> Optional[FindingResponse]:
        with self._lock:
            f = self._findings.get(finding_id)
            if not f:
                return None
            data = f.model_dump()
            data["status"] = action.decision
            data["decision"] = action.decision
            data["decisionNote"] = action.note
            data["decisionAt"] = datetime.now(timezone.utc).isoformat()
            if action.decision == "confirmed_waste":
                data["confirmedSavings"] = data["potentialSavings"]
            updated = FindingResponse(**data)
            self._findings[finding_id] = updated
            return updated

    def add(self, finding: FindingResponse) -> FindingResponse:
        with self._lock:
            self._findings[finding.id] = finding
            return finding

    def clear(self) -> None:
        with self._lock:
            self._findings.clear()


class InMemoryTransactionRepository(TransactionRepository):
    def __init__(self, data: Optional[List[TransactionResponse]] = None):
        self._lock = threading.RLock()
        self._txs: List[TransactionResponse] = data or []

    def list(
        self,
        subscription_id: Optional[str] = None,
        connection_id: Optional[str] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> List[TransactionResponse]:
        with self._lock:
            res = self._txs
            if subscription_id:
                res = [t for t in res if t.id == subscription_id]
            if connection_id:
                res = [t for t in res if t.connectionId == connection_id]
            return res[skip : skip + limit]

    def add(self, transaction: TransactionResponse) -> TransactionResponse:
        with self._lock:
            self._txs.append(transaction)
            return transaction

    def clear(self) -> None:
        with self._lock:
            self._txs.clear()


class InMemoryConnectionRepository(ConnectionRepository):
    def __init__(self, data: Optional[Dict[str, ConnectionResponse]] = None):
        self._lock = threading.RLock()
        self._conns: Dict[str, ConnectionResponse] = data or {}

    def list(self) -> List[ConnectionResponse]:
        with self._lock:
            return list(self._conns.values())

    def get_by_id(self, connection_id: str) -> Optional[ConnectionResponse]:
        with self._lock:
            return self._conns.get(connection_id)

    def sync(self, connection_id: Optional[str] = None) -> bool:
        with self._lock:
            now_iso = datetime.now(timezone.utc).isoformat()
            if connection_id:
                c = self._conns.get(connection_id)
                if c:
                    c.lastSyncedAt = now_iso
                    c.status = "connected"
                    return True
                return False
            for c in self._conns.values():
                c.lastSyncedAt = now_iso
                c.status = "connected"
            return True

    def disconnect(self, connection_id: str, delete_data: bool = False) -> bool:
        with self._lock:
            c = self._conns.get(connection_id)
            if c:
                c.status = "disconnected"
                return True
            return False
