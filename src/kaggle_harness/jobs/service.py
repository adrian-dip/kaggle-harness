from __future__ import annotations

from datetime import timedelta
from uuid import UUID

from kaggle_harness.jobs.models import Job
from kaggle_harness.jobs.repository import JobRepository
from kaggle_harness.protocol.messages import ArtifactRef, WorkerCapabilities


class JobService:
    def __init__(self, repo: JobRepository) -> None:
        self._repo = repo

    async def enqueue(self, job: Job) -> Job:
        await self._repo.enqueue(job)
        return job

    async def claim_next(self, worker_id: str, caps: WorkerCapabilities) -> Job | None:
        return await self._repo.claim_next(worker_id, caps)

    async def heartbeat(self, job_id: UUID, worker_id: str) -> None:
        await self._repo.heartbeat(job_id, worker_id)

    async def complete(self, job_id: UUID, artifacts: list[ArtifactRef]) -> None:
        await self._repo.mark_succeeded(job_id, artifacts)

    async def fail(self, job_id: UUID, reason: str) -> None:
        await self._repo.mark_failed(job_id, reason)

    async def requeue_stale(self, timeout: timedelta) -> int:
        return await self._repo.requeue_stale(timeout)

    async def get(self, job_id: UUID) -> Job | None:
        return await self._repo.get(job_id)

    async def get_by_experiment(self, experiment_id: UUID) -> list[Job]:
        return await self._repo.get_by_experiment(experiment_id)
