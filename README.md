# Assignment 6 — PostgreSQL integration with FastAPI, SQLAlchemy, Alembic and Pydantic

A small, self-contained backend that stores a learning platform (courses, topics,
lessons, problems, users, progress, submissions, comments) in **PostgreSQL**.
Every requirement of the assignment is implemented here without any dependency on
the larger project it was extracted from.

## Stack

| Layer | Technology |
| --- | --- |
| Web framework | FastAPI 0.163 |
| ORM | SQLAlchemy 2.0 typed mappings (`Mapped`, `mapped_column`) |
| Database | PostgreSQL 14+ via `psycopg` 3 |
| Migrations | Alembic 1.20 |
| Validation | Pydantic v2 (`EmailStr`, `Field`, `field_validator`) |
| Tests | pytest + FastAPI `TestClient` (in-memory SQLite) |

## Requirement mapping

### 1. PostgreSQL Integration

`app/database.py` builds the engine from `settings.database_url`; the URL comes from
the `DATABASE_URL` environment variable (`app/config.py` and `.env.example`). No
connection string is hard-coded in application code — only a local default for
development is provided.

### 2. Database Models and Relationships

`app/models.py` defines ten tables. Every relationship direction is declared with
`relationship(back_populates=...)`.

| Parent | Children | Type |
| --- | --- | --- |
| `Course` | `Topic` | one-to-many, cascade delete |
| `Topic` | `Lesson` | one-to-many, cascade delete |
| `Lesson` | `Problem` | one-to-many, cascade delete |
| `Lesson` | `LessonProgress` | one-to-many |
| `Lesson` | `Lesson` (prerequisite) | self-referencing many-to-one |
| `Problem` | `Submission`, `ProblemCompletion`, `Comment` | one-to-many |
| `User` | `AuthSession`, `Submission`, `LessonProgress`, `ProblemCompletion`, `Comment` | one-to-many |

Integrity rules live in the database too: unique email, unique nickname, unique
token hash, `(course_id, position)`, `(topic_id, position)`,
`(user_id, lesson_id)`, `(user_id, problem_id)` constraints and `ON DELETE CASCADE`
foreign keys.

### 3. Database Migrations

`migrations/` contains the Alembic environment and one reviewed initial revision,
`a1aa8b672e9f_initial_schema.py`, that creates all eleven tables (ten models plus
`alembic_version`).

```sh
alembic upgrade head        # apply
alembic downgrade base      # drop everything created by the migration
alembic upgrade head        # recreate from an empty database
```

Verified on an empty PostgreSQL database: `upgrade head` produced 11 tables,
`downgrade base` left only `alembic_version`, and `upgrade head` again restored
the full schema.

### 4. Database CRUD Operations

All create/read/update/delete paths run through a SQLAlchemy session:

| Resource | Endpoints |
| --- | --- |
| Courses | `GET/POST /api/courses`, `GET/PATCH/DELETE /api/courses/{id}` |
| Topics | `POST /api/courses/{id}/topics`, `PATCH/DELETE /api/topics/{id}` |
| Lessons | `POST /api/topics/{id}/lessons`, `GET/PATCH/DELETE /api/lessons/{id}` |
| Problems | `POST /api/lessons/{id}/problems`, `GET/PATCH/DELETE /api/problems/{id}` |
| Users | `GET /api/users/me`, `GET /api/users/{id}` |
| Progress | `POST /api/lessons/{id}/start`, `POST /api/lessons/{id}/complete`, `DELETE /api/lessons/{id}/progress`, `GET /api/progress` |
| Submissions | `POST /api/problems/{id}/submit`, `GET /api/submissions`, `GET /api/submissions/{id}` |
| Comments | `GET/POST /api/problems/{id}/comments`, `PATCH/DELETE /api/comments/{id}` |

Persistence was verified by restarting the Uvicorn process: the same bearer token
still returned the user, both accepted submissions, the completed lesson, the
completion rows and the comment, all read from PostgreSQL.

### 5. Data Validation and Integrity

Pydantic v2 validates every request body (`app/schemas.py`): email format,
password length, nickname pattern `^[A-Za-z0-9_]{3,24}$`, positional fields
`>= 0`, reward bounds, difficulty enum, non-blank comments, and maximum lengths.
Validation failures return FastAPI's `422`. Business rules (duplicate email or
nickname, duplicate positions, prerequisite cycles, missing prerequisites,
incomplete lessons, author-only comment edits) are enforced in the service layer
and mapped to `409`/`403`/`404` with a stable `{"error": {"code", "message"}}`
body.

### 6. Architecture and Testing

```
app/
  routers/     HTTP layer: paths, status codes, request/response models
  schemas.py   Pydantic request and response models
  services/    Business rules, transactions, authorization
  models.py    SQLAlchemy ORM models and relationships
  deps.py      Session and bearer-token dependencies
  security.py  scrypt password hashing, token generation and hashing
tests/         pytest suites per feature area
migrations/    Alembic environment and revisions
scripts/       Idempotent demo seed
```

Routers depend on services, services own database work, and only services touch
`models.py`; HTTP concerns never leak into the data layer.

## Quick start

```sh
# 1. Database (any PostgreSQL instance works)
psql -d postgres -c "CREATE ROLE assignment6 LOGIN PASSWORD 'assignment6'"
psql -d postgres -c "CREATE DATABASE assignment6 OWNER assignment6"

# 2. Environment and dependencies
cp .env.example .env            # adjust DATABASE_URL if needed
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt

# 3. Schema and demo data
.venv/bin/alembic upgrade head
.venv/bin/python -m scripts.seed

# 4. Run the API
.venv/bin/python -m uvicorn app.main:app --reload --port 8000
```

Open <http://127.0.0.1:8000/docs> for Swagger UI, or
<http://127.0.0.1:8000/openapi.json> for the raw schema
(24 paths / 34 operations).

## Testing with Swagger UI

1. `POST /api/auth/register` — creates an account and returns a bearer token.
2. Click **Authorize**, paste the token, authorize.
3. `GET /api/users/me` — private profile (email included).
4. `POST /api/lessons/1/start` — progress is stored.
5. `POST /api/problems/1/submit` with the body
   `{"answer": "def add(a, b):\n    return a + b"}` — accepted, rewards granted,
   and the lesson completes automatically once all of its published problems are
   accepted.
6. `GET /api/progress` and `GET /api/submissions` — persisted state.
7. `GET /api/courses` without a token — public nested catalog (the stored
   `expected_answer` is never exposed).
8. Restart Uvicorn and repeat steps 3, 6 — the same records are returned.

## Automated tests

```sh
.venv/bin/python -m pytest -q
# 23 passed
```

The suite runs against SQLite in memory with foreign keys enabled, and covers
authentication, catalog CRUD and validation, prerequisite cycles, progress,
submissions and rewards, and comment ownership.

## Grading model

Submissions compare the normalized answer (line endings and trailing whitespace
are ignored) with the problem's stored reference solution. This keeps the service
pure Python/HTTP — no subprocess, container or code execution — while still giving
deterministic `ACCEPTED` / `WRONG_ANSWER` verdicts.
