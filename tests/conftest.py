import os

os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///:memory:")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app import models  # noqa: F401 - registers metadata
from app.database import Base, get_db
from app.main import app

engine = create_engine(
    "sqlite+pysqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)


@event.listens_for(engine, "connect")
def _enable_foreign_keys(connection, _record) -> None:
    connection.execute("PRAGMA foreign_keys=ON")


TestingSession = sessionmaker(bind=engine, expire_on_commit=False, autoflush=False)


@pytest.fixture(autouse=True)
def fresh_database():
    with engine.connect() as connection:
        connection.exec_driver_sql("PRAGMA foreign_keys=OFF")
        Base.metadata.drop_all(connection)
        connection.exec_driver_sql("PRAGMA foreign_keys=ON")
        Base.metadata.create_all(connection)
        connection.commit()
    yield


@pytest.fixture
def client():
    def override():
        session = TestingSession()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def register(client):
    def _register(nickname: str = "alice", email: str | None = None, password: str = "Passw0rd!"):
        response = client.post(
            "/api/auth/register",
            json={
                "email": email or f"{nickname}@example.com",
                "password": password,
                "nickname": nickname,
            },
        )
        assert response.status_code == 201, response.text
        payload = response.json()
        return {"Authorization": f"Bearer {payload['token']}"}, payload["user"]

    return _register


@pytest.fixture
def catalog(client, register):
    headers, _user = register()
    course = client.post(
        "/api/courses",
        json={"title": "Python", "language": "python", "description": "demo"},
        headers=headers,
    ).json()["course"]
    topic = client.post(
        f"/api/courses/{course['id']}/topics",
        json={"title": "Basics", "position": 0},
        headers=headers,
    ).json()["topic"]
    lesson = client.post(
        f"/api/topics/{topic['id']}/lessons",
        json={"title": "Functions", "theory_md": "theory", "position": 0},
        headers=headers,
    ).json()
    problem = client.post(
        f"/api/lessons/{lesson['lesson_id']}/problems",
        json={
            "title": "Add two numbers",
            "function_name": "add",
            "starter_code": "def add(a, b):\n    ...\n",
            "expected_answer": "def add(a, b):\n    return a + b",
            "reward_xp": 10,
            "reward_coins": 2,
        },
        headers=headers,
    ).json()["problem"]
    return {
        "headers": headers,
        "course": course,
        "topic": topic,
        "lesson": lesson,
        "problem": problem,
    }
