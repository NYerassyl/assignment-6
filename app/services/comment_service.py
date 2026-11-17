from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.errors import forbidden, not_found
from app.models import Comment, Problem, User
from app.schemas import CommentCreate


def list_comments(session: Session, problem: Problem) -> list[Comment]:
    return list(
        session.scalars(
            select(Comment).where(Comment.problem_id == problem.id).order_by(Comment.id)
        ).all()
    )


def create_comment(session: Session, problem: Problem, author: User, data: CommentCreate) -> Comment:
    comment = Comment(problem_id=problem.id, author_id=author.id, body=data.body)
    session.add(comment)
    session.commit()
    session.refresh(comment)
    return comment


def _owned(session: Session, comment_id: int, user: User) -> Comment:
    comment = session.get(Comment, comment_id)
    if comment is None:
        raise not_found("comment")
    if comment.author_id != user.id:
        raise forbidden("COMMENT_FORBIDDEN", "Only the author can change this comment.")
    return comment


def update_comment(session: Session, comment_id: int, user: User, data: CommentCreate) -> Comment:
    comment = _owned(session, comment_id, user)
    comment.body = data.body
    comment.updated_at = datetime.now(timezone.utc)
    session.commit()
    session.refresh(comment)
    return comment


def delete_comment(session: Session, comment_id: int, user: User) -> None:
    comment = _owned(session, comment_id, user)
    session.delete(comment)
    session.commit()
