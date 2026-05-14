from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from kaggle_harness.api.deps import get_submission_service
from kaggle_harness.submissions.service import SubmissionService

router = APIRouter(prefix="/submissions", tags=["submissions"])


class SubmissionResponse(BaseModel):
    id: UUID
    experiment_id: UUID
    competition: str
    kaggle_ref: str | None
    public_score: float | None
    private_score: float | None
    status: str
    created_at: str


@router.get("/{submission_id}", response_model=SubmissionResponse)
async def get_submission(
    submission_id: UUID,
    svc: SubmissionService = Depends(get_submission_service),
):
    sub = await svc.get(submission_id)
    if sub is None:
        raise HTTPException(404, detail="Submission not found")
    return SubmissionResponse(
        id=sub.id,
        experiment_id=sub.experiment_id,
        competition=sub.competition,
        kaggle_ref=sub.kaggle_ref,
        public_score=sub.public_score,
        private_score=sub.private_score,
        status=sub.status,
        created_at=sub.created_at.isoformat(),
    )
