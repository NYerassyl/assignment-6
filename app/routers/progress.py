from fastapi import APIRouter, status

from app.deps import CurrentUser, DbSession
from app.services import content_service, progress_service

router = APIRouter(prefix="/api", tags=["progress"])


@router.post("/lessons/{lesson_id}/start")
def start_lesson(lesson_id: int, session: DbSession, user: CurrentUser) -> dict:
    lesson = content_service.get_lesson(session, lesson_id)
    return progress_service.start(session, user, lesson)


@router.get("/progress")
def progress_overview(session: DbSession, user: CurrentUser) -> dict:
    return progress_service.overview(session, user)


@router.post("/lessons/{lesson_id}/complete")
def complete_lesson(lesson_id: int, session: DbSession, user: CurrentUser) -> dict:
    lesson = content_service.get_lesson(session, lesson_id)
    return progress_service.complete(session, user, lesson)


@router.delete("/lessons/{lesson_id}/progress", status_code=status.HTTP_204_NO_CONTENT)
def reset_progress(lesson_id: int, session: DbSession, user: CurrentUser) -> None:
    lesson = content_service.get_lesson(session, lesson_id)
    progress_service.reset(session, user, lesson)
