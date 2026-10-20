from fastapi import APIRouter, Depends, HTTPException, status
from ..auth import create_access_token, get_current_user
from ..models import SessionRequest, SessionResponse, User, Workspace
from ..store import store

router = APIRouter(tags=["Auth"])


@router.post("/auth/session", response_model=SessionResponse)
def create_session(body: SessionRequest):
    user = store.authenticate_user(body.email, body.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    token = create_access_token({"sub": user.id, "email": user.email})
    return SessionResponse(token=token, user=user)


@router.get("/me", response_model=User)
def get_me(user: User = Depends(get_current_user)):
    return user


@router.get("/workspace", response_model=Workspace)
def get_workspace(user: User = Depends(get_current_user)):
    return store.get_workspace_for_user(user.id)


@router.delete("/account", status_code=status.HTTP_204_NO_CONTENT)
def delete_account(user: User = Depends(get_current_user)):
    store.delete_account(user.id)
    return None
