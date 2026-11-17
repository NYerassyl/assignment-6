from fastapi import APIRouter, status

from app.deps import CurrentUser, DbSession
from app.errors import not_found
from app.schemas import SubmissionOut, SubmissionRequest
from app.services import content_service, submission_service

router = APIRouter(prefix="/api", tags=["submissions"])


@router.post(
    "/problems/{problem_id}/submit",
    status_code=status.HTTP_201_CREATED,
)
def submit_answer(
    problem_id: int, data: SubmissionRequest, session: DbSession, user: CurrentUser
) -> dict:
    problem = content_service.get_problem(session, problem_id)
    if not problem.is_published:
        raise not_found("problem")
    return submission_service.submit(session, user, problem, data.answer)


@router.get("/submissions")
def my_submissions(session: DbSession, user: CurrentUser) -> dict:
    return {"submissions": submission_service.history(session, user)}


@router.get("/submissions/{submission_id}", response_model=SubmissionOut)
def get_submission(submission_id: int, session: DbSession, user: CurrentUser) -> SubmissionOut:
    return SubmissionOut.model_validate(
        submission_service.get_submission(session, user, submission_id)
    )
