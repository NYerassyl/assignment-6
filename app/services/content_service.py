from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.errors import conflict, not_found
from app.models import Course, Lesson, LessonProgress, Problem, Submission, Topic
from app.schemas import CourseCreate, CourseUpdate, LessonCreate, LessonUpdate, ProblemCreate, ProblemUpdate, TopicCreate, TopicUpdate


def commit(session: Session) -> None:
    try:
        session.commit()
    except IntegrityError as exc:
        session.rollback()
        raise conflict(
            "CONTENT_CONFLICT", "Content violates a uniqueness or reference rule."
        ) from exc


def lesson_summary(lesson: Lesson) -> dict:
    return {"id": lesson.id, "title": lesson.title, "position": lesson.position}


def topic_summary(topic: Topic) -> dict:
    return {
        "id": topic.id,
        "title": topic.title,
        "position": topic.position,
        "lessons": [lesson_summary(item) for item in topic.lessons],
    }


def course_out(course: Course) -> dict:
    return {
        "id": course.id,
        "title": course.title,
        "language": course.language,
        "description": course.description,
        "is_published": course.is_published,
        "topics": [topic_summary(item) for item in course.topics],
    }


def problem_out(problem: Problem) -> dict:
    return {
        "id": problem.id,
        "lesson_id": problem.lesson_id,
        "title": problem.title,
        "difficulty": problem.difficulty,
        "function_name": problem.function_name,
        "starter_code": problem.starter_code,
        "reward_xp": problem.reward_xp,
        "reward_coins": problem.reward_coins,
        "is_published": problem.is_published,
    }


def lesson_out(lesson: Lesson) -> dict:
    return {
        "id": lesson.id,
        "topic_id": lesson.topic_id,
        "title": lesson.title,
        "theory_md": lesson.theory_md,
        "position": lesson.position,
        "prerequisite": (
            {"id": lesson.prerequisite.id, "title": lesson.prerequisite.title}
            if lesson.prerequisite
            else None
        ),
        "problems": [problem_out(item) for item in lesson.problems if item.is_published],
    }


def get_course(session: Session, course_id: int) -> Course:
    course = session.scalar(
        select(Course)
        .options(selectinload(Course.topics).selectinload(Topic.lessons))
        .where(Course.id == course_id)
    )
    if course is None:
        raise not_found("course")
    return course


def list_courses(session: Session) -> list[dict]:
    courses = session.scalars(
        select(Course)
        .options(selectinload(Course.topics).selectinload(Topic.lessons))
        .where(Course.is_published.is_(True))
        .order_by(Course.id)
    ).all()
    return [course_out(item) for item in courses]


def create_course(session: Session, data: CourseCreate) -> Course:
    course = Course(**data.model_dump())
    session.add(course)
    commit(session)
    session.refresh(course)
    return course


def update_course(session: Session, course_id: int, data: CourseUpdate) -> Course:
    course = get_course(session, course_id)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(course, field, value)
    commit(session)
    return course


def _lesson_history(session: Session, lesson_ids: list[int]) -> int:
    if not lesson_ids:
        return 0
    submissions = session.scalar(
        select(func.count())
        .select_from(Submission)
        .join(Problem, Submission.problem_id == Problem.id)
        .where(Problem.lesson_id.in_(lesson_ids))
    )
    progress = session.scalar(
        select(func.count())
        .select_from(LessonProgress)
        .where(LessonProgress.lesson_id.in_(lesson_ids))
    )
    return int(submissions or 0) + int(progress or 0)


def _course_lesson_ids(session: Session, course_id: int) -> list[int]:
    return list(
        session.scalars(
            select(Lesson.id)
            .join(Topic, Lesson.topic_id == Topic.id)
            .where(Topic.course_id == course_id)
        ).all()
    )


def delete_course(session: Session, course_id: int) -> None:
    course = get_course(session, course_id)
    if _lesson_history(session, _course_lesson_ids(session, course_id)):
        raise conflict(
            "COURSE_HAS_HISTORY",
            "This course has learner submissions or progress and cannot be deleted.",
        )
    session.delete(course)
    commit(session)


def get_topic(session: Session, topic_id: int) -> Topic:
    topic = session.scalar(
        select(Topic).options(selectinload(Topic.lessons)).where(Topic.id == topic_id)
    )
    if topic is None:
        raise not_found("topic")
    return topic


def create_topic(session: Session, course_id: int, data: TopicCreate) -> Topic:
    get_course(session, course_id)
    topic = Topic(course_id=course_id, **data.model_dump())
    session.add(topic)
    commit(session)
    session.refresh(topic)
    return topic


def update_topic(session: Session, topic_id: int, data: TopicUpdate) -> Topic:
    topic = get_topic(session, topic_id)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(topic, field, value)
    commit(session)
    return topic


def delete_topic(session: Session, topic_id: int) -> None:
    topic = get_topic(session, topic_id)
    lesson_ids = [lesson.id for lesson in topic.lessons]
    if _lesson_history(session, lesson_ids):
        raise conflict(
            "TOPIC_HAS_HISTORY",
            "This topic has learner submissions or progress and cannot be deleted.",
        )
    session.delete(topic)
    commit(session)


def get_lesson(session: Session, lesson_id: int) -> Lesson:
    lesson = session.scalar(
        select(Lesson)
        .options(selectinload(Lesson.problems), selectinload(Lesson.prerequisite))
        .where(Lesson.id == lesson_id)
    )
    if lesson is None:
        raise not_found("lesson")
    return lesson


def _assert_prerequisite(
    session: Session, lesson_id: int | None, prerequisite_id: int | None
) -> None:
    if prerequisite_id is None:
        return
    if session.get(Lesson, prerequisite_id) is None:
        raise not_found("prerequisite lesson")
    cursor = prerequisite_id
    seen: set[int] = set()
    while cursor is not None and cursor not in seen:
        if cursor == lesson_id:
            raise conflict(
                "PREREQUISITE_CYCLE", "A lesson cannot depend on itself directly or indirectly."
            )
        seen.add(cursor)
        cursor = session.scalar(select(Lesson.prerequisite_id).where(Lesson.id == cursor))


def create_lesson(session: Session, topic_id: int, data: LessonCreate) -> Lesson:
    get_topic(session, topic_id)
    _assert_prerequisite(session, None, data.prerequisite_id)
    lesson = Lesson(topic_id=topic_id, **data.model_dump())
    session.add(lesson)
    commit(session)
    session.refresh(lesson)
    return lesson


def update_lesson(session: Session, lesson_id: int, data: LessonUpdate) -> Lesson:
    lesson = get_lesson(session, lesson_id)
    changes = data.model_dump(exclude_unset=True)
    if "prerequisite_id" in changes:
        _assert_prerequisite(session, lesson.id, changes["prerequisite_id"])
    for field, value in changes.items():
        setattr(lesson, field, value)
    commit(session)
    return lesson


def delete_lesson(session: Session, lesson_id: int) -> None:
    lesson = get_lesson(session, lesson_id)
    if _lesson_history(session, [lesson.id]):
        raise conflict(
            "LESSON_HAS_HISTORY",
            "This lesson has learner submissions or progress and cannot be deleted.",
        )
    dependent = session.scalar(
        select(Lesson.id).where(Lesson.prerequisite_id == lesson.id).limit(1)
    )
    if dependent is not None:
        raise conflict(
            "LESSON_IS_PREREQUISITE",
            "Another lesson depends on this prerequisite; update it first.",
        )
    session.delete(lesson)
    commit(session)


def get_problem(session: Session, problem_id: int) -> Problem:
    problem = session.get(Problem, problem_id)
    if problem is None:
        raise not_found("problem")
    return problem


def create_problem(session: Session, lesson_id: int, data: ProblemCreate) -> Problem:
    get_lesson(session, lesson_id)
    problem = Problem(lesson_id=lesson_id, **data.model_dump())
    session.add(problem)
    commit(session)
    session.refresh(problem)
    return problem


def update_problem(session: Session, problem_id: int, data: ProblemUpdate) -> Problem:
    problem = get_problem(session, problem_id)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(problem, field, value)
    commit(session)
    return problem


def delete_problem(session: Session, problem_id: int) -> None:
    problem = get_problem(session, problem_id)
    submissions = session.scalar(
        select(func.count()).select_from(Submission).where(Submission.problem_id == problem.id)
    )
    if submissions:
        raise conflict(
            "PROBLEM_HAS_HISTORY",
            "This problem has submissions and cannot be deleted.",
        )
    session.delete(problem)
    commit(session)
