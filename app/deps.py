from datetime import datetime, timezone
from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.errors import unauthorized
from app.models import AuthSession, User
from app.security import token_digest

bearer = HTTPBearer(auto_error=False)
DbSession = Annotated[Session, Depends(get_db)]


def current_user(
    session: DbSession,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> User:
    if credentials is None or not credentials.credentials:
        raise unauthorized()
    session_row = session.scalar(
        select(AuthSession).where(
            AuthSession.token_hash == token_digest(credentials.credentials),
            AuthSession.revoked_at.is_(None),
            AuthSession.expires_at > datetime.now(timezone.utc),
        )
    )
    if session_row is None:
        raise unauthorized("Invalid, expired or revoked session.")
    return session_row.user


CurrentUser = Annotated[User, Depends(current_user)]
