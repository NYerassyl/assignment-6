from fastapi import APIRouter

from app.deps import CurrentUser, DbSession
from app.errors import not_found
from app.models import User
from app.schemas import UserPrivate, UserPublic

router = APIRouter(prefix="/api/users", tags=["users"])


@router.get("/me", response_model=UserPrivate)
def private_profile(user: CurrentUser) -> UserPrivate:
    return UserPrivate.model_validate(user)


@router.get("/{user_id}", response_model=UserPublic)
def public_profile(user_id: int, session: DbSession) -> UserPublic:
    user = session.get(User, user_id)
    if user is None:
        raise not_found("user")
    return UserPublic.model_validate(user)
