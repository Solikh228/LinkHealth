from abc import ABC, abstractmethod
from typing import List, Optional
from schemas import (
    ConnectionResponse,
    FindingActionRequest,
    FindingResponse,
    OverviewMetricsResponse,
    SubscriptionResponse,
    TransactionResponse,
)


class SubscriptionRepository(ABC):
    @abstractmethod
    def list(
        self,
        status: Optional[str] = None,
        cadence: Optional[str] = None,
        search: Optional[str] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> List[SubscriptionResponse]:
        pass

    @abstractmethod
    def get_by_id(self, subscription_id: str) -> Optional[SubscriptionResponse]:
        pass

    @abstractmethod
    def update(
        self,
        subscription_id: str,
        name: Optional[str] = None,
        billing_interval: Optional[str] = None,
        category: Optional[str] = None,
        status: Optional[str] = None,
        note: Optional[str] = None,
    ) -> Optional[SubscriptionResponse]:
        pass


class FindingRepository(ABC):
    @abstractmethod
    def list(
        self,
        status: Optional[str] = None,
        finding_type: Optional[str] = None,
    ) -> List[FindingResponse]:
        pass

    @abstractmethod
    def get_by_id(self, finding_id: str) -> Optional[FindingResponse]:
        pass

    @abstractmethod
    def apply_action(
        self,
        finding_id: str,
        action: FindingActionRequest,
    ) -> Optional[FindingResponse]:
        pass


class TransactionRepository(ABC):
    @abstractmethod
    def list(
        self,
        subscription_id: Optional[str] = None,
        connection_id: Optional[str] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> List[TransactionResponse]:
        pass

    @abstractmethod
    def add(self, transaction: TransactionResponse) -> TransactionResponse:
        pass


class ConnectionRepository(ABC):
    @abstractmethod
    def list(self) -> List[ConnectionResponse]:
        pass

    @abstractmethod
    def get_by_id(self, connection_id: str) -> Optional[ConnectionResponse]:
        pass

    @abstractmethod
    def sync(self, connection_id: Optional[str] = None) -> bool:
        pass

    @abstractmethod
    def disconnect(self, connection_id: str, delete_data: bool = False) -> bool:
        pass
