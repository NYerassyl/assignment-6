from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.errors import not_found
from app.models import LessonProgress, Problem, ProblemCompletion, Submission, User


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _complete_lesson_if_done(session: Session, user: User, lesson_id: int) -> bool:
    published = list(
        session.scalars(
            select(Problem.id).where(
                Problem.lesson_id == lesson_id, Problem.is_published.is_(True)
            )
        ).all()
    )
    if not published:
        return False
    learned = set(
        session.scalars(
            select(ProblemCompletion.problem_id).where(
                ProblemCompletion.user_id == user.id,
                ProblemCompletion.problem_id.in_(published),
            )
        ).all()
    )
    if set(published) - learned:
        return False
    row = session.scalar(
        select(LessonProgress).where(
            LessonProgress.user_id == user.id, LessonProgress.lesson_id == lesson_id
        )
    )
    if row is None:
        row = LessonProgress(user_id=user.id, lesson_id=lesson_id)
        session.add(row)
    if row.completed_at is None:
        row.completed_at = _now()
        return True
    return False


def _normalize(source: str) -> str:
    lines = [line.rstrip() for line in source.replace("\r\n", "\n").split("\n")]
    while lines and not lines[-1]:
        lines.pop()
    while lines and not lines[0]:
        lines.pop(0)
    return "\n".join(lines)


def submit(session: Session, user: User, problem: Problem, answer: str) -> dict:
    accepted = _normalize(answer) == _normalize(problem.expected_answer)
    submission = Submission(
        user_id=user.id,
        problem_id=problem.id,
        answer=answer,
        status="ACCEPTED" if accepted else "WRONG_ANSWER",
    )
    session.add(submission)
    reward_xp = 0
    reward_coins = 0
    first_completion = False
    lesson_completed = False
    if accepted:
        existing = session.scalar(
            select(ProblemCompletion.id).where(
                ProblemCompletion.user_id == user.id,
                ProblemCompletion.problem_id == problem.id,
            )
        )
        if existing is None:
            session.add(ProblemCompletion(user_id=user.id, problem_id=problem.id))
            session.flush()
            first_completion = True
            reward_xp = problem.reward_xp
            reward_coins = problem.reward_coins
            user.xp += reward_xp
            user.coins += reward_coins
            user.level = user.xp // 100 + 1
            lesson_completed = _complete_lesson_if_done(session, user, problem.lesson_id)
    session.commit()
    session.refresh(submission)
    return {
        "submission": {
            "id": submission.id,
            "problem_id": problem.id,
            "status": submission.status,
            "created_at": submission.created_at,
        },
        "first_completion": first_completion,
        "rewards": {"xp": reward_xp, "coins": reward_coins},
        "lesson_completed": lesson_completed,
        "user": {"id": user.id, "xp": user.xp, "coins": user.coins, "level": user.level},
    }


def history(session: Session, user: User) -> list[dict]:
    rows = session.scalars(
        select(Submission)
        .where(Submission.user_id == user.id)
        .order_by(Submission.id.desc())
        .limit(100)
    ).all()
    return [
        {
            "id": row.id,
            "problem_id": row.problem_id,
            "status": row.status,
            "created_at": row.created_at,
        }
        for row in rows
    ]


def get_submission(session: Session, user: User, submission_id: int) -> Submission:
    row = session.get(Submission, submission_id)
    if row is None or row.user_id != user.id:
        raise not_found("submission")
    return row
