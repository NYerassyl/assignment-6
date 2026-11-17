from fastapi import APIRouter, status

from app.deps import CurrentUser, DbSession
from app.schemas import (
    CourseCreate,
    CourseUpdate,
    LessonCreate,
    LessonUpdate,
    ProblemCreate,
    ProblemUpdate,
    TopicCreate,
    TopicUpdate,
)
from app.services import content_service

router = APIRouter(prefix="/api", tags=["content"])


@router.get("/courses")
def list_courses(session: DbSession) -> dict:
    return {"courses": content_service.list_courses(session)}


@router.get("/courses/{course_id}")
def get_course(course_id: int, session: DbSession) -> dict:
    return {"course": content_service.course_out(content_service.get_course(session, course_id))}


@router.post("/courses", status_code=status.HTTP_201_CREATED)
def create_course(data: CourseCreate, session: DbSession, user: CurrentUser) -> dict:
    return {"course": content_service.course_out(content_service.create_course(session, data))}


@router.patch("/courses/{course_id}")
def update_course(course_id: int, data: CourseUpdate, session: DbSession, user: CurrentUser) -> dict:
    course = content_service.update_course(session, course_id, data)
    return {"course": content_service.course_out(course)}


@router.delete("/courses/{course_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_course(course_id: int, session: DbSession, user: CurrentUser) -> None:
    content_service.delete_course(session, course_id)


@router.post("/courses/{course_id}/topics", status_code=status.HTTP_201_CREATED)
def create_topic(course_id: int, data: TopicCreate, session: DbSession, user: CurrentUser) -> dict:
    topic = content_service.create_topic(session, course_id, data)
    return {"topic": content_service.topic_summary(topic)}


@router.patch("/topics/{topic_id}")
def update_topic(topic_id: int, data: TopicUpdate, session: DbSession, user: CurrentUser) -> dict:
    topic = content_service.update_topic(session, topic_id, data)
    return {"topic": content_service.topic_summary(topic)}


@router.delete("/topics/{topic_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_topic(topic_id: int, session: DbSession, user: CurrentUser) -> None:
    content_service.delete_topic(session, topic_id)


@router.post("/topics/{topic_id}/lessons", status_code=status.HTTP_201_CREATED)
def create_lesson(topic_id: int, data: LessonCreate, session: DbSession, user: CurrentUser) -> dict:
    lesson = content_service.create_lesson(session, topic_id, data)
    return {"lesson_id": lesson.id, "title": lesson.title}


@router.get("/lessons/{lesson_id}")
def get_lesson(lesson_id: int, session: DbSession) -> dict:
    return {"lesson": content_service.lesson_out(content_service.get_lesson(session, lesson_id))}


@router.patch("/lessons/{lesson_id}")
def update_lesson(lesson_id: int, data: LessonUpdate, session: DbSession, user: CurrentUser) -> dict:
    lesson = content_service.update_lesson(session, lesson_id, data)
    return {"lesson": content_service.lesson_out(content_service.get_lesson(session, lesson.id))}


@router.delete("/lessons/{lesson_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_lesson(lesson_id: int, session: DbSession, user: CurrentUser) -> None:
    content_service.delete_lesson(session, lesson_id)


@router.post("/lessons/{lesson_id}/problems", status_code=status.HTTP_201_CREATED)
def create_problem(lesson_id: int, data: ProblemCreate, session: DbSession, user: CurrentUser) -> dict:
    problem = content_service.create_problem(session, lesson_id, data)
    return {"problem": content_service.problem_out(problem)}


@router.get("/problems/{problem_id}")
def get_problem(problem_id: int, session: DbSession) -> dict:
    return {"problem": content_service.problem_out(content_service.get_problem(session, problem_id))}


@router.patch("/problems/{problem_id}")
def update_problem(problem_id: int, data: ProblemUpdate, session: DbSession, user: CurrentUser) -> dict:
    problem = content_service.update_problem(session, problem_id, data)
    return {"problem": content_service.problem_out(problem)}


@router.delete("/problems/{problem_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_problem(problem_id: int, session: DbSession, user: CurrentUser) -> None:
    content_service.delete_problem(session, problem_id)
