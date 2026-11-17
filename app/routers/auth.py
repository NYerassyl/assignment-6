from fastapi import APIRouter, Depends, status
from fastapi.security import HTTPAuthorizationCredentials

from app.deps import DbSession, bearer
from app.schemas import AuthResponse, LoginRequest, RegisterRequest, UserPrivate
from app.services import auth_service

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def register(data: RegisterRequest, session: DbSession) -> AuthResponse:
    user, token = auth_service.register(session, data)
    return AuthResponse(token=token, user=UserPrivate.model_validate(user))


@router.post("/login", response_model=AuthResponse)
def login(data: LoginRequest, session: DbSession) -> AuthResponse:
    user, token = auth_service.login(session, data)
    return AuthResponse(token=token, user=UserPrivate.model_validate(user))


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    session: DbSession,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
) -> None:
    if credentials is not None:
        auth_service.logout(session, credentials.credentials)
