from fastapi import APIRouter, status

from app.deps import CurrentUser, DbSession
from app.schemas import CommentCreate, CommentOut
from app.services import comment_service, content_service

router = APIRouter(prefix="/api", tags=["comments"])


@router.get("/problems/{problem_id}/comments")
def list_comments(problem_id: int, session: DbSession) -> dict:
    problem = content_service.get_problem(session, problem_id)
    return {
        "comments": [
            CommentOut.model_validate(item) for item in comment_service.list_comments(session, problem)
        ]
    }


@router.post(
    "/problems/{problem_id}/comments",
    response_model=CommentOut,
    status_code=status.HTTP_201_CREATED,
)
def create_comment(
    problem_id: int, data: CommentCreate, session: DbSession, user: CurrentUser
) -> CommentOut:
    problem = content_service.get_problem(session, problem_id)
    return CommentOut.model_validate(
        comment_service.create_comment(session, problem, user, data)
    )


@router.patch("/comments/{comment_id}", response_model=CommentOut)
def update_comment(
    comment_id: int, data: CommentCreate, session: DbSession, user: CurrentUser
) -> CommentOut:
    return CommentOut.model_validate(comment_service.update_comment(session, comment_id, user, data))


@router.delete("/comments/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_comment(comment_id: int, session: DbSession, user: CurrentUser) -> None:
    comment_service.delete_comment(session, comment_id, user)
