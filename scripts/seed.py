"""Seed a small demo catalog. Safe to run repeatedly (idempotent by title)."""

from sqlalchemy import select

from app.database import SessionLocal
from app.models import Course, Lesson, Problem, Topic


def main() -> None:
    with SessionLocal() as session:
        course = session.scalar(select(Course).where(Course.title == "Python Fundamentals"))
        if course is not None:
            print("Seed already present; nothing to do.")
            return

        course = Course(
            title="Python Fundamentals",
            language="python",
            description="A small demo course used by the Assignment 6 API.",
        )
        session.add(course)
        session.flush()

        basics = Topic(course_id=course.id, title="Getting started", position=0)
        flow = Topic(course_id=course.id, title="Control flow", position=1)
        session.add_all([basics, flow])
        session.flush()

        variables = Lesson(
            topic_id=basics.id,
            title="Variables and functions",
            theory_md="A function packages a reusable block of code.\n",
            position=0,
        )
        numbers = Lesson(
            topic_id=basics.id,
            title="Working with numbers",
            theory_md="Arithmetic operators combine numeric values.\n",
            position=1,
            prerequisite=variables,
        )
        branches = Lesson(
            topic_id=flow.id,
            title="Conditionals",
            theory_md="Use `if` to run code only when a condition holds.\n",
            position=0,
            prerequisite=numbers,
        )
        session.add_all([variables, numbers, branches])
        session.flush()

        session.add_all(
            [
                Problem(
                    lesson_id=variables.id,
                    title="Add two numbers",
                    difficulty="EASY",
                    function_name="add",
                    starter_code="def add(a, b):\n    ...\n",
                    expected_answer="def add(a, b):\n    return a + b",
                    reward_xp=10,
                    reward_coins=2,
                ),
                Problem(
                    lesson_id=variables.id,
                    title="Double a number",
                    difficulty="EASY",
                    function_name="double",
                    starter_code="def double(value):\n    ...\n",
                    expected_answer="def double(value):\n    return value * 2",
                    reward_xp=10,
                    reward_coins=2,
                ),
                Problem(
                    lesson_id=numbers.id,
                    title="Square a number",
                    difficulty="MEDIUM",
                    function_name="square",
                    starter_code="def square(value):\n    ...\n",
                    expected_answer="def square(value):\n    return value ** 2",
                    reward_xp=15,
                    reward_coins=3,
                ),
                Problem(
                    lesson_id=branches.id,
                    title="Is the number even?",
                    difficulty="MEDIUM",
                    function_name="is_even",
                    starter_code="def is_even(value):\n    ...\n",
                    expected_answer="def is_even(value):\n    return value % 2 == 0",
                    reward_xp=15,
                    reward_coins=3,
                ),
            ]
        )
        session.commit()
        print("Seeded: 1 course, 2 topics, 3 lessons, 4 problems.")


if __name__ == "__main__":
    main()
