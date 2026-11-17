from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.errors import conflict, unauthorized
from app.models import AuthSession, User
from app.schemas import LoginRequest, RegisterRequest
from app.security import hash_password, new_token, token_digest, verify_password


def _issue_token(session: Session, user: User) -> str:
    token = new_token()
    session.add(
        AuthSession(
            user_id=user.id,
            token_hash=token_digest(token),
            expires_at=datetime.now(timezone.utc) + timedelta(hours=settings.token_ttl_hours),
        )
    )
    session.commit()
    return token


def register(session: Session, data: RegisterRequest) -> tuple[User, str]:
    email = data.email.lower()
    if session.scalar(select(User.id).where(User.email == email)) is not None:
        raise conflict("EMAIL_TAKEN", "An account with this email already exists.")
    if session.scalar(select(User.id).where(User.nickname == data.nickname)) is not None:
        raise conflict("NICKNAME_TAKEN", "This nickname is already in use.")
    user = User(
        email=email,
        nickname=data.nickname,
        password_hash=hash_password(data.password),
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user, _issue_token(session, user)


def login(session: Session, data: LoginRequest) -> tuple[User, str]:
    user = session.scalar(select(User).where(User.email == data.email.lower()))
    if user is None or not verify_password(data.password, user.password_hash):
        raise unauthorized("Invalid email or password.")
    return user, _issue_token(session, user)


def logout(session: Session, token: str) -> None:
    row = session.scalar(
        select(AuthSession).where(
            AuthSession.token_hash == token_digest(token),
            AuthSession.revoked_at.is_(None),
        )
    )
    if row is not None:
        row.revoked_at = datetime.now(timezone.utc)
        session.commit()
