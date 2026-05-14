from fastapi import Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from kaggle_harness.bundles.store import ArtifactStore, BundleStore
from kaggle_harness.config import Settings
from kaggle_harness.experiments.service import ExperimentService
from kaggle_harness.inputs.staging import InputsStager
from kaggle_harness.jobs.repository import PostgresJobRepository
from kaggle_harness.jobs.service import JobService
from kaggle_harness.kaggle.service import KaggleService
from kaggle_harness.submissions.service import SubmissionService
from kaggle_harness.tracking.tracker import Tracker


def get_settings(request: Request) -> Settings:
    return request.app.state.settings


def get_kaggle_service(request: Request) -> KaggleService:
    client = request.app.state.kaggle_client
    if client is None:
        raise HTTPException(503, detail="Kaggle client not configured — check credentials")
    return KaggleService(client)


def get_bundle_store(request: Request) -> BundleStore:
    return request.app.state.bundle_store


def get_artifact_store(request: Request) -> ArtifactStore:
    return request.app.state.artifact_store


def get_tracker(request: Request) -> Tracker | None:
    return getattr(request.app.state, "tracker", None)


async def get_session(request: Request) -> AsyncSession:
    factory: async_sessionmaker[AsyncSession] = request.app.state.session_factory
    async with factory() as session:
        yield session


async def get_job_service(session: AsyncSession = Depends(get_session)) -> JobService:
    return JobService(PostgresJobRepository(session))


async def get_experiment_service(
    request: Request,
    session: AsyncSession = Depends(get_session),
    job_svc: JobService = Depends(get_job_service),
    bundle_store: BundleStore = Depends(get_bundle_store),
) -> ExperimentService:
    stager = getattr(request.app.state, "inputs_stager", None)
    tracker = getattr(request.app.state, "tracker", None)
    return ExperimentService(session, job_svc, bundle_store, stager=stager, tracker=tracker)


async def get_submission_service(
    request: Request,
    session: AsyncSession = Depends(get_session),
) -> SubmissionService:
    kaggle_client = request.app.state.kaggle_client
    if kaggle_client is None:
        raise HTTPException(503, detail="Kaggle client not configured")
    kaggle_svc = KaggleService(kaggle_client)
    artifact_store: ArtifactStore = request.app.state.artifact_store
    tracker: Tracker | None = getattr(request.app.state, "tracker", None)
    return SubmissionService(session, kaggle_svc, artifact_store, tracker)
