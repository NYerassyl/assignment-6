from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.errors import DomainError
from app.routers import auth, comments, content, meta, progress, submissions, users

DESCRIPTION = """
WorldOfCodes learning API — Assignment 6.

Persistent PostgreSQL storage through SQLAlchemy with Alembic migrations.
Register or log in, then use **Authorize → Bearer token** in Swagger.

Relationships:
- Course → Topic → Lesson → Problem (one-to-many, cascade delete)
- User → AuthSession, Submission, LessonProgress, ProblemCompletion, Comment
- Lesson → prerequisite Lesson (self-referencing, cycle-protected)
"""

app = FastAPI(
    title="WorldOfCodes Assignment 6 API",
    description=DESCRIPTION,
    version="6.0.0",
    openapi_tags=[
        {"name": "meta", "description": "Health and service metadata."},
        {"name": "auth", "description": "Registration, login and session revocation."},
        {"name": "users", "description": "Private and public profiles."},
        {"name": "content", "description": "Course, topic, lesson and problem CRUD."},
        {"name": "progress", "description": "Lesson start, completion and XP."},
        {"name": "submissions", "description": "Answer submission and history."},
        {"name": "comments", "description": "Problem comments with author-only edits."},
    ],
)


@app.exception_handler(DomainError)
async def domain_error_handler(_request: Request, exc: DomainError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": exc.code, "message": exc.message}},
    )


app.include_router(meta.router)
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(content.router)
app.include_router(progress.router)
app.include_router(submissions.router)
app.include_router(comments.router)
