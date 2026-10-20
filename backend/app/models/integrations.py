from typing import List, Literal, Optional
from pydantic import BaseModel, ConfigDict

ConnectionStatus = Literal["pending", "active", "needs_reauth", "error", "disconnected"]
SyncState = Literal[
    "not_connected",
    "connecting",
    "initial_sync",
    "up_to_date",
    "delayed",
    "needs_reauth",
    "error",
    "disconnected",
]


class IntegrationConnection(BaseModel):
    id: str
    kind: Literal["bank", "gmail"]
    provider: str
    displayName: str
    status: ConnectionStatus
    syncState: SyncState
    scopesGranted: List[str]
    lastSyncAt: Optional[str] = None
    lastSyncStatus: Optional[Literal["success", "failed", "running"]] = None
    createdAt: str

    model_config = ConfigDict(from_attributes=True)


class ConnectResponse(BaseModel):
    redirectUrl: Optional[str] = None
    connection: IntegrationConnection


class DisconnectRequest(BaseModel):
    deleteData: bool = False
