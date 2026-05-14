from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from datetime import timedelta

import structlog
from fastapi import FastAPI

from kaggle_harness.api.errors import install_handlers
from kaggle_harness.api.routes import competitions, datasets, experiments, kernels, submissions, workers
from kaggle_harness.bundles.store import ArtifactStore, MinioBundleStore
from kaggle_harness.config import Settings
from kaggle_harness.db.engine import build_engine, build_session_factory
from kaggle_harness.inputs.staging import InputsStager
from kaggle_harness.jobs.repository import PostgresJobRepository
from kaggle_harness.jobs.service import JobService
from kaggle_harness.logging import configure_logging

logger = structlog.get_logger()


async def _requeue_stale_loop(app: FastAPI) -> None:
    while True:
        await asyncio.sleep(30)
        try:
            async with app.state.session_factory() as session:
                svc = JobService(PostgresJobRepository(session))
                n = await svc.requeue_stale(
                    timedelta(seconds=app.state.settings.worker_heartbeat_timeout_seconds)
                )
                if n:
                    logger.info("jobs.requeued_stale", count=n)
        except Exception as exc:
            logger.warning("jobs.requeue_stale_error", error=str(exc))


@asynccontextmanager
async def _lifespan(app: FastAPI):
    settings = Settings()
    configure_logging(debug=settings.debug)
    app.state.settings = settings

    from kaggle_harness.kaggle.client import KaggleApiClient

    try:
        app.state.kaggle_client = KaggleApiClient(
            kaggle_username=settings.kaggle_username,
            kaggle_key=settings.kaggle_key,
            kaggle_config_dir=settings.kaggle_config_dir,
        )
        logger.info("kaggle.authenticated")
    except Exception as exc:
        logger.warning("kaggle.auth_failed", error=str(exc))
        app.state.kaggle_client = None

    engine = build_engine(settings.database_url)
    app.state.engine = engine
    app.state.session_factory = build_session_factory(engine)

    app.state.bundle_store = MinioBundleStore(
        endpoint=settings.minio_endpoint,
        access_key=settings.minio_access_key,
        secret_key=settings.minio_secret_key,
        bucket=settings.minio_bucket_bundles,
        secure=settings.minio_secure,
    )
    app.state.artifact_store = ArtifactStore(
        endpoint=settings.minio_endpoint,
        access_key=settings.minio_access_key,
        secret_key=settings.minio_secret_key,
        bucket=settings.minio_bucket_artifacts,
        secure=settings.minio_secure,
    )
    app.state.inputs_store = MinioBundleStore(
        endpoint=settings.minio_endpoint,
        access_key=settings.minio_access_key,
        secret_key=settings.minio_secret_key,
        bucket=settings.minio_bucket_inputs,
        secure=settings.minio_secure,
    )

    if app.state.kaggle_client is not None:
        from kaggle_harness.kaggle.service import KaggleService
        kaggle_svc = KaggleService(app.state.kaggle_client)
        app.state.kaggle_service = kaggle_svc
        app.state.inputs_stager = InputsStager(kaggle_svc, app.state.inputs_store)
    else:
        app.state.kaggle_service = None
        app.state.inputs_stager = None

    try:
        from kaggle_harness.tracking.tracker import MlflowTracker
        app.state.tracker = MlflowTracker(settings.mlflow_tracking_uri)
        logger.info("mlflow.connected", uri=settings.mlflow_tracking_uri)
    except Exception as exc:
        logger.warning("mlflow.connect_failed", error=str(exc))
        app.state.tracker = None

    requeue_task = asyncio.create_task(_requeue_stale_loop(app))

    logger.info("gateway.started", port=settings.port)
    yield

    requeue_task.cancel()
    await engine.dispose()
    logger.info("gateway.stopped")


def create_app() -> FastAPI:
    app = FastAPI(title="Kaggle Harness", version="0.1.0", lifespan=_lifespan)
    install_handlers(app)
    app.include_router(competitions.router)
    app.include_router(datasets.router)
    app.include_router(kernels.router)
    app.include_router(experiments.router)
    app.include_router(workers.router)
    app.include_router(submissions.router)
    return app
