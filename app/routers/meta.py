from fastapi import APIRouter
from sqlalchemy import func, select

from app.deps import DbSession
from app.models import Course, Lesson, Problem, Submission, User

router = APIRouter(tags=["meta"])


@router.get("/")
def index() -> dict:
    return {
        "service": "assignment-6",
        "docs": "/docs",
        "health": "/api/health",
    }


@router.get("/api/health")
def health(session: DbSession) -> dict:
    return {
        "status": "ok",
        "service": "assignment-6",
        "users": session.scalar(select(func.count()).select_from(User)),
        "courses": session.scalar(select(func.count()).select_from(Course)),
        "lessons": session.scalar(select(func.count()).select_from(Lesson)),
        "problems": session.scalar(select(func.count()).select_from(Problem)),
        "submissions": session.scalar(select(func.count()).select_from(Submission)),
    }
