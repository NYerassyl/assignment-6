from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.errors import conflict
from app.models import Lesson, LessonProgress, Problem, ProblemCompletion, User


def _now() -> datetime:
    return datetime.now(timezone.utc)


def progress_state(row: LessonProgress) -> dict:
    return {
        "lesson_id": row.lesson_id,
        "state": "COMPLETED" if row.completed_at else "IN_PROGRESS",
        "started_at": row.started_at,
        "completed_at": row.completed_at,
    }


def start(session: Session, user: User, lesson: Lesson) -> dict:
    if lesson.prerequisite_id is not None:
        prerequisite = session.scalar(
            select(LessonProgress).where(
                LessonProgress.user_id == user.id,
                LessonProgress.lesson_id == lesson.prerequisite_id,
            )
        )
        if prerequisite is None or prerequisite.completed_at is None:
            raise conflict(
                "PREREQUISITE_REQUIRED",
                "Complete the prerequisite lesson before starting this one.",
            )
    row = session.scalar(
        select(LessonProgress).where(
            LessonProgress.user_id == user.id, LessonProgress.lesson_id == lesson.id
        )
    )
    if row is None:
        row = LessonProgress(user_id=user.id, lesson_id=lesson.id)
        session.add(row)
        session.commit()
        session.refresh(row)
    return progress_state(row)


def overview(session: Session, user: User) -> dict:
    rows = session.scalars(
        select(LessonProgress)
        .where(LessonProgress.user_id == user.id)
        .order_by(LessonProgress.lesson_id)
    ).all()
    completions = session.scalars(
        select(ProblemCompletion)
        .where(ProblemCompletion.user_id == user.id)
        .order_by(ProblemCompletion.problem_id)
    ).all()
    return {
        "lessons": [progress_state(row) for row in rows],
        "completed_problems": [
            {"problem_id": item.problem_id, "completed_at": item.completed_at}
            for item in completions
        ],
    }


def complete(session: Session, user: User, lesson: Lesson) -> dict:
    row = session.scalar(
        select(LessonProgress).where(
            LessonProgress.user_id == user.id, LessonProgress.lesson_id == lesson.id
        )
    )
    if row is not None and row.completed_at is not None:
        return progress_state(row)
    problem_ids = list(
        session.scalars(
            select(Problem.id).where(
                Problem.lesson_id == lesson.id, Problem.is_published.is_(True)
            )
        ).all()
    )
    completed = set(
        session.scalars(
            select(ProblemCompletion.problem_id).where(
                ProblemCompletion.user_id == user.id,
                ProblemCompletion.problem_id.in_(problem_ids or [0]),
            )
        ).all()
    )
    if set(problem_ids) - completed:
        raise conflict(
            "LESSON_INCOMPLETE",
            "Every published problem in the lesson must be accepted before completion.",
        )
    if row is None:
        row = LessonProgress(user_id=user.id, lesson_id=lesson.id)
        session.add(row)
    row.completed_at = _now()
    session.commit()
    session.refresh(row)
    return progress_state(row)


def reset(session: Session, user: User, lesson: Lesson) -> None:
    row = session.scalar(
        select(LessonProgress).where(
            LessonProgress.user_id == user.id, LessonProgress.lesson_id == lesson.id
        )
    )
    if row is None:
        return
    if row.completed_at is not None:
        raise conflict(
            "COMPLETED_PROGRESS",
            "Completed progress cannot be reset; rewards were already granted.",
        )
    session.delete(row)
    session.commit()
