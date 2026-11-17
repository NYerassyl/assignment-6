from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    nickname: str = Field(pattern=r"^[A-Za-z0-9_]{3,24}$")


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class UserPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nickname: str
    xp: int
    coins: int
    level: int
    created_at: datetime


class UserPrivate(UserPublic):
    email: EmailStr


class AuthResponse(BaseModel):
    token: str
    user: UserPrivate


class CourseCreate(BaseModel):
    title: str = Field(min_length=1, max_length=120)
    language: str = Field(min_length=2, max_length=32)
    description: str | None = Field(default=None, max_length=2000)
    is_published: bool = True

    @field_validator("title", "language")
    @classmethod
    def _strip(cls, value: str) -> str:
        return value.strip()


class CourseUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=120)
    language: str | None = Field(default=None, min_length=2, max_length=32)
    description: str | None = Field(default=None, max_length=2000)
    is_published: bool | None = None


class TopicCreate(BaseModel):
    title: str = Field(min_length=1, max_length=120)
    position: int = Field(default=0, ge=0)


class TopicUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=120)
    position: int | None = Field(default=None, ge=0)


class LessonCreate(BaseModel):
    title: str = Field(min_length=1, max_length=120)
    theory_md: str = Field(min_length=1, max_length=20000)
    position: int = Field(default=0, ge=0)
    prerequisite_id: int | None = None


class LessonUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=120)
    theory_md: str | None = Field(default=None, min_length=1, max_length=20000)
    position: int | None = Field(default=None, ge=0)
    prerequisite_id: int | None = None


class ProblemCreate(BaseModel):
    title: str = Field(min_length=1, max_length=120)
    difficulty: Literal["EASY", "MEDIUM", "HARD"] = "EASY"
    function_name: str = Field(pattern=r"^[A-Za-z_][A-Za-z0-9_]{0,63}$")
    starter_code: str = Field(min_length=1, max_length=20000)
    expected_answer: str = Field(min_length=1, max_length=20000)
    reward_xp: int = Field(default=0, ge=0, le=10000)
    reward_coins: int = Field(default=0, ge=0, le=10000)
    is_published: bool = True


class ProblemUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=120)
    difficulty: Literal["EASY", "MEDIUM", "HARD"] | None = None
    starter_code: str | None = Field(default=None, min_length=1, max_length=20000)
    expected_answer: str | None = Field(default=None, min_length=1, max_length=20000)
    reward_xp: int | None = Field(default=None, ge=0, le=10000)
    reward_coins: int | None = Field(default=None, ge=0, le=10000)
    is_published: bool | None = None


class SubmissionRequest(BaseModel):
    answer: str = Field(min_length=1, max_length=20000)


class CommentCreate(BaseModel):
    body: str = Field(min_length=1, max_length=2000)

    @field_validator("body")
    @classmethod
    def _not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Comment body must not be blank.")
        return value.strip()


class CommentUpdate(CommentCreate):
    pass


class CommentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    problem_id: int
    author_id: int
    body: str
    created_at: datetime
    updated_at: datetime | None


class ProgressOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    lesson_id: int
    state: Literal["IN_PROGRESS", "COMPLETED"]
    started_at: datetime
    completed_at: datetime | None


class SubmissionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    problem_id: int
    status: str
    created_at: datetime
