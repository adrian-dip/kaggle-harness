from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from pydantic import BaseModel

from kaggle_harness.api.deps import get_experiment_service, get_job_service
from kaggle_harness.experiments.service import ExperimentService
from kaggle_harness.jobs.service import JobService

router = APIRouter(prefix="/experiments", tags=["experiments"])


class ExperimentResponse(BaseModel):
    id: UUID
    name: str
    manifest: dict
    mlflow_run_id: str | None
    created_at: str
    jobs: list[dict]


@router.post("", status_code=201, response_model=ExperimentResponse)
async def submit_experiment(
    bundle: UploadFile,
    svc: ExperimentService = Depends(get_experiment_service),
    job_svc: JobService = Depends(get_job_service),
):
    data = await bundle.read()
    try:
        experiment = await svc.submit(data)
    except ValueError as exc:
        raise HTTPException(400, detail=str(exc))
    jobs = await job_svc.get_by_experiment(experiment.id)
    return ExperimentResponse(
        id=experiment.id,
        name=experiment.name,
        manifest=experiment.manifest,
        mlflow_run_id=experiment.mlflow_run_id,
        created_at=experiment.created_at.isoformat(),
        jobs=[{"id": str(j.id), "status": j.status} for j in jobs],
    )


@router.get("/{experiment_id}", response_model=ExperimentResponse)
async def get_experiment(
    experiment_id: UUID,
    svc: ExperimentService = Depends(get_experiment_service),
    job_svc: JobService = Depends(get_job_service),
):
    experiment = await svc.get(experiment_id)
    if experiment is None:
        raise HTTPException(404, detail="Experiment not found")
    jobs = await job_svc.get_by_experiment(experiment.id)
    return ExperimentResponse(
        id=experiment.id,
        name=experiment.name,
        manifest=experiment.manifest,
        mlflow_run_id=experiment.mlflow_run_id,
        created_at=experiment.created_at.isoformat(),
        jobs=[{"id": str(j.id), "status": j.status} for j in jobs],
    )
