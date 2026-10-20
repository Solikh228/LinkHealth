from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from ..auth import get_optional_user
from ..models import ConnectResponse, DisconnectRequest, IntegrationConnection, User
from ..store import store

router = APIRouter(tags=["Integrations"])


@router.get("/integrations", response_model=List[IntegrationConnection])
def list_integrations(user: User = Depends(get_optional_user)):
    return store.list_integrations()


@router.post("/integrations/bank/connect", response_model=ConnectResponse)
def connect_bank(user: User = Depends(get_optional_user)):
    conn = store.connect_bank()
    return ConnectResponse(redirectUrl=None, connection=conn)


@router.post("/integrations/gmail/connect", response_model=ConnectResponse)
def connect_gmail(user: User = Depends(get_optional_user)):
    conn = store.connect_gmail()
    return ConnectResponse(redirectUrl=None, connection=conn)


@router.post("/integrations/{id}/sync", response_model=IntegrationConnection)
def sync_integration(id: str, user: User = Depends(get_optional_user)):
    conn = store.sync_integration(id)
    if not conn:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Integration '{id}' not found",
        )
    return conn


@router.post("/integrations/{id}/disconnect", status_code=status.HTTP_204_NO_CONTENT)
def disconnect_integration(
    id: str,
    body: DisconnectRequest = DisconnectRequest(),
    user: User = Depends(get_optional_user),
):
    success = store.disconnect_integration(id, delete_data=body.deleteData)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Integration '{id}' not found",
        )
    return None
