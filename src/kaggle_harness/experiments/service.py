from __future__ import annotations

import io
import uuid
from uuid import UUID

import structlog
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from kaggle_harness.bundles.bundle import Bundle
from kaggle_harness.bundles.store import BundleStore
from kaggle_harness.experiments.models import Experiment
from kaggle_harness.inputs.staging import InputsStager
from kaggle_harness.jobs.models import Job
from kaggle_harness.jobs.service import JobService
from kaggle_harness.tracking.linkage import tag_experiment
from kaggle_harness.tracking.tracker import Tracker

logger = structlog.get_logger()


class ExperimentService:
    def __init__(
        self,
        session: AsyncSession,
        job_service: JobService,
        bundle_store: BundleStore,
        stager: InputsStager | None = None,
        tracker: Tracker | None = None,
    ) -> None:
        self._session = session
        self._jobs = job_service
        self._bundles = bundle_store
        self._stager = stager
        self._tracker = tracker

    async def submit(self, zip_bytes: bytes) -> Experiment:
        bundle_id = str(uuid.uuid4())
        bundle = Bundle.from_zip_bytes(bundle_id, zip_bytes)
        manifest = bundle.manifest

        await self._bundles.put(bundle.bundle_id, io.BytesIO(zip_bytes))

        # Stage inputs into MinIO (keyed by slug, cached)
        staged_inputs: dict[str, str] = {}  # minio_key → local_path
        if self._stager is not None:
            for slug in manifest.inputs.competitions:
                key = await self._stager.stage_competition(slug)
                staged_inputs[key] = f"/data/competitions/{slug}"
            for slug in manifest.inputs.datasets:
                key = await self._stager.stage_dataset(slug)
                safe = slug.replace("/", "__")
                staged_inputs[key] = f"/data/datasets/{safe}"

        # Create MLflow run
        mlflow_run_id: str | None = None
        if self._tracker is not None and manifest.mlflow is not None:
            handle = self._tracker.create_run(
                experiment=manifest.mlflow.experiment, name=manifest.name
            )
            mlflow_run_id = handle.run_id

        experiment = Experiment(
            name=manifest.name,
            manifest=manifest.model_dump(mode="json"),
            staged_inputs=staged_inputs,
            mlflow_run_id=mlflow_run_id,
        )
        self._session.add(experiment)
        await self._session.commit()
        await self._session.refresh(experiment)

        if self._tracker is not None and mlflow_run_id:
            tag_experiment(self._tracker, mlflow_run_id, experiment.id, manifest.name)
            self._tracker.log_params(mlflow_run_id, {
                "entrypoint": manifest.entrypoint,
                "image": manifest.runtime.image,
                "cpu": manifest.resources.cpu,
                "memory": manifest.resources.memory,
                "gpu": manifest.resources.gpu,
            })

        job = Job(
            experiment_id=experiment.id,
            bundle_id=bundle.bundle_id,
            requires={
                "gpu": manifest.resources.gpu,
                "labels": manifest.resources.labels,
                "cpu": manifest.resources.cpu,
                "memory_mb": manifest.memory_mb(),
            },
        )
        await self._jobs.enqueue(job)
        logger.info("experiment.submitted", experiment_id=str(experiment.id), name=manifest.name)
        return experiment

    async def get(self, experiment_id: UUID) -> Experiment | None:
        result = await self._session.execute(
            text("SELECT * FROM experiments WHERE id=:id"), {"id": experiment_id}
        )
        row = result.mappings().first()
        return Experiment(**dict(row)) if row else None

    async def cancel(self, experiment_id: UUID) -> None:
        await self._session.execute(
            text("""
                UPDATE jobs SET status='cancelled', finished_at=now()
                WHERE experiment_id=:eid AND status IN ('queued', 'running')
            """),
            {"eid": experiment_id},
        )
        await self._session.commit()
