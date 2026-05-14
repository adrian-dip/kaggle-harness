from __future__ import annotations

import asyncio
from datetime import datetime, timedelta
from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, Header, HTTPException, Request, Response
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from kaggle_harness.api.deps import (
    get_bundle_store,
    get_job_service,
    get_session,
    get_settings,
)
from kaggle_harness.bundles.store import ArtifactStore, BundleStore, MinioBundleStore
from kaggle_harness.config import Settings
from kaggle_harness.experiments.models import Experiment
from kaggle_harness.jobs.service import JobService
from kaggle_harness.protocol.messages import (
    ArtifactRef,
    ClaimRequest,
    JobAssignment,
    JobReport,
    JobRequires,
    JobStatus,
    RegisterRequest,
    RegisterResponse,
    StagedInput,
    WorkerCapabilities,
)
from kaggle_harness.workers.models import Worker

logger = structlog.get_logger()

router = APIRouter(prefix="/workers", tags=["workers"])


def _check_token(authorization: str | None, settings: Settings) -> None:
    if authorization != f"Bearer {settings.worker_token}":
        raise HTTPException(401, detail="Invalid worker token")


def _get_artifact_store(request: Request) -> ArtifactStore:
    return request.app.state.artifact_store


def _get_inputs_store(request: Request) -> MinioBundleStore:
    return request.app.state.inputs_store


@router.post("/register", response_model=RegisterResponse)
async def register_worker(
    body: RegisterRequest,
    authorization: str | None = Header(default=None),
    settings: Settings = Depends(get_settings),
    session: AsyncSession = Depends(get_session),
):
    _check_token(authorization, settings)
    caps = body.capabilities
    worker = Worker(
        id=caps.worker_id,
        labels=caps.labels,
        gpu=caps.gpu,
        cpu=caps.cpu,
        memory_mb=caps.memory_mb,
        last_seen=datetime.utcnow(),
    )
    await session.merge(worker)
    await session.commit()
    logger.info("worker.registered", worker_id=caps.worker_id)
    return RegisterResponse(token=settings.worker_token)


@router.post("/claim", response_model=JobAssignment | None)
async def claim_job(
    body: ClaimRequest,
    request: Request,
    authorization: str | None = Header(default=None),
    settings: Settings = Depends(get_settings),
    job_svc: JobService = Depends(get_job_service),
    session: AsyncSession = Depends(get_session),
):
    _check_token(authorization, settings)

    deadline = asyncio.get_event_loop().time() + 30
    while True:
        job = await job_svc.claim_next(body.worker_id, body.capabilities)
        if job is not None:
            break
        remaining = deadline - asyncio.get_event_loop().time()
        if remaining <= 0:
            return None
        await asyncio.sleep(min(1.0, remaining))

    result = await session.execute(
        text("SELECT * FROM experiments WHERE id=:id"), {"id": job.experiment_id}
    )
    row = result.mappings().first()
    if row is None:
        raise HTTPException(500, detail="Experiment row missing for job")
    exp = Experiment(**dict(row))

    from kaggle_harness.bundles.manifest import ExperimentManifest
    manifest = ExperimentManifest.model_validate(exp.manifest)

    # Build presigned URLs for each staged input
    inputs_store: MinioBundleStore = request.app.state.inputs_store
    staged: list[StagedInput] = []
    for minio_key, local_path in (exp.staged_inputs or {}).items():
        url = await inputs_store.signed_url(minio_key, ttl=timedelta(hours=1))
        staged.append(StagedInput(local_path=local_path, download_url=url))

    requires = JobRequires(
        gpu=manifest.resources.gpu,
        labels=manifest.resources.labels,
        cpu=manifest.resources.cpu,
        memory_mb=manifest.memory_mb(),
    )

    return JobAssignment(
        job_id=job.id,
        experiment_id=job.experiment_id,
        bundle_id=job.bundle_id,
        entrypoint=manifest.entrypoint,
        image=manifest.runtime.image,
        requirements_file=manifest.runtime.requirements,
        env=manifest.env,
        requires=requires,
        staged_inputs=staged,
        declared_outputs=manifest.outputs,
        mlflow_run_id=exp.mlflow_run_id,
        mlflow_tracking_uri=settings.mlflow_tracking_uri,
        mlflow_experiment_name=manifest.mlflow.experiment if manifest.mlflow else None,
    )


@router.post("/jobs/{job_id}/heartbeat", status_code=204)
async def heartbeat(
    job_id: UUID,
    worker_id: str,
    authorization: str | None = Header(default=None),
    settings: Settings = Depends(get_settings),
    job_svc: JobService = Depends(get_job_service),
):
    _check_token(authorization, settings)
    await job_svc.heartbeat(job_id, worker_id)
    return Response(status_code=204)


@router.post("/jobs/{job_id}/logs", status_code=204)
async def append_logs(
    job_id: UUID,
    body: dict,
    authorization: str | None = Header(default=None),
    settings: Settings = Depends(get_settings),
):
    _check_token(authorization, settings)
    logger.debug("worker.log", job_id=str(job_id), text=body.get("text", ""))
    return Response(status_code=204)


@router.post("/jobs/{job_id}/report", status_code=204)
async def report_job(
    job_id: UUID,
    body: JobReport,
    request: Request,
    authorization: str | None = Header(default=None),
    settings: Settings = Depends(get_settings),
    job_svc: JobService = Depends(get_job_service),
    session: AsyncSession = Depends(get_session),
):
    _check_token(authorization, settings)

    if body.status == JobStatus.succeeded:
        await job_svc.complete(job_id, body.artifacts)
        logger.info("job.succeeded", job_id=str(job_id))

        # Log artifacts to MLflow and check for auto-submit
        await _on_success(request, session, job_id, body.artifacts)
    else:
        await job_svc.fail(job_id, body.error or "unknown error")
        logger.info("job.failed", job_id=str(job_id), error=body.error)

        # Mark MLflow run as failed
        tracker = getattr(request.app.state, "tracker", None)
        if tracker is not None:
            result = await session.execute(
                text("SELECT e.mlflow_run_id FROM jobs j JOIN experiments e ON e.id=j.experiment_id WHERE j.id=:id"),
                {"id": job_id},
            )
            row = result.mappings().first()
            if row and row["mlflow_run_id"]:
                tracker.set_terminated(row["mlflow_run_id"], "FAILED")

    return Response(status_code=204)


async def _on_success(
    request: Request,
    session: AsyncSession,
    job_id: UUID,
    artifacts: list[ArtifactRef],
) -> None:
    result = await session.execute(
        text("""
            SELECT e.id, e.mlflow_run_id, e.manifest
            FROM jobs j JOIN experiments e ON e.id=j.experiment_id
            WHERE j.id=:id
        """),
        {"id": job_id},
    )
    row = result.mappings().first()
    if row is None:
        return

    tracker = getattr(request.app.state, "tracker", None)
    artifact_store: ArtifactStore = request.app.state.artifact_store

    # Log artifacts to MLflow
    if tracker is not None and row["mlflow_run_id"]:
        import tempfile
        from pathlib import Path
        run_id = row["mlflow_run_id"]
        for art in artifacts:
            try:
                data = await artifact_store.get(art.store_key)
                with tempfile.NamedTemporaryFile(suffix="_" + art.name, delete=False) as f:
                    f.write(data)
                    tmp_path = Path(f.name)
                tracker.log_artifact(run_id, tmp_path, artifact_path="outputs")
                tmp_path.unlink(missing_ok=True)
            except Exception as exc:
                logger.warning("mlflow.artifact_log_error", error=str(exc), artifact=art.name)
        tracker.set_terminated(run_id, "FINISHED")

    # Auto-submit if manifest has submit:
    from kaggle_harness.bundles.manifest import ExperimentManifest
    manifest = ExperimentManifest.model_validate(row["manifest"])
    if manifest.submit is not None:
        submit_cfg = manifest.submit
        art_match = next((a for a in artifacts if a.name == submit_cfg.file), None)
        if art_match is not None:
            from kaggle_harness.submissions.service import SubmissionService
            from kaggle_harness.submissions import poller
            from kaggle_harness.kaggle.service import KaggleService

            kaggle_client = request.app.state.kaggle_client
            if kaggle_client is not None:
                from kaggle_harness.kaggle.service import KaggleService as KS
                kaggle_svc = KS(kaggle_client)
                sub_svc = SubmissionService(
                    session=session,
                    kaggle=kaggle_svc,
                    artifact_store=artifact_store,
                    tracker=tracker,
                )
                message = submit_cfg.message.format(name=manifest.name)
                sub = await sub_svc.submit(
                    experiment_id=row["id"],
                    mlflow_run_id=row["mlflow_run_id"],
                    competition=submit_cfg.competition,
                    store_key=art_match.store_key,
                    message=message,
                )
                poller.schedule(request.app, sub.id)


@router.get("/bundles/{bundle_id}")
async def download_bundle(
    bundle_id: str,
    authorization: str | None = Header(default=None),
    settings: Settings = Depends(get_settings),
    bundle_store: BundleStore = Depends(get_bundle_store),
):
    _check_token(authorization, settings)
    url = await bundle_store.signed_url(bundle_id, ttl=timedelta(minutes=15))
    return Response(status_code=307, headers={"Location": url})


@router.post("/jobs/{job_id}/artifacts/{filename}")
async def artifact_upload_url(
    job_id: UUID,
    filename: str,
    request: Request,
    authorization: str | None = Header(default=None),
    settings: Settings = Depends(get_settings),
):
    """Return a presigned PUT URL so the worker can upload directly to MinIO."""
    _check_token(authorization, settings)
    artifact_store: ArtifactStore = request.app.state.artifact_store
    key = f"jobs/{job_id}/{filename}"
    url = await artifact_store.signed_put_url(key, ttl=timedelta(minutes=30))
    return {"upload_url": url, "store_key": key}
