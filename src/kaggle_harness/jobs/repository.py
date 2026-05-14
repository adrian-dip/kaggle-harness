from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from kaggle_harness.jobs.models import Job, JobStatus
from kaggle_harness.protocol.messages import ArtifactRef, WorkerCapabilities


class JobRepository(ABC):
    @abstractmethod
    async def enqueue(self, job: Job) -> None: ...

    @abstractmethod
    async def claim_next(self, worker_id: str, caps: WorkerCapabilities) -> Job | None: ...

    @abstractmethod
    async def heartbeat(self, job_id: UUID, worker_id: str) -> None: ...

    @abstractmethod
    async def mark_succeeded(self, job_id: UUID, artifacts: list[ArtifactRef]) -> None: ...

    @abstractmethod
    async def mark_failed(self, job_id: UUID, reason: str) -> None: ...

    @abstractmethod
    async def requeue_stale(self, older_than: timedelta) -> int: ...

    @abstractmethod
    async def get(self, job_id: UUID) -> Job | None: ...

    @abstractmethod
    async def get_by_experiment(self, experiment_id: UUID) -> list[Job]: ...


class PostgresJobRepository(JobRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def enqueue(self, job: Job) -> None:
        self._session.add(job)
        await self._session.commit()
        await self._session.refresh(job)

    async def claim_next(self, worker_id: str, caps: WorkerCapabilities) -> Job | None:
        labels_json = "[" + ",".join(f'"{l}"' for l in caps.labels) + "]"
        result = await self._session.execute(
            text("""
                UPDATE jobs SET status='running', worker_id=:wid,
                    started_at=now(), heartbeat_at=now()
                WHERE id = (
                    SELECT id FROM jobs
                    WHERE status = 'queued'
                      AND (requires->>'gpu' = 'false' OR :worker_has_gpu)
                      AND (requires->'labels' IS NULL
                           OR requires->'labels' <@ to_jsonb(:worker_labels::text[]))
                    ORDER BY priority DESC, created_at ASC
                    FOR UPDATE SKIP LOCKED
                    LIMIT 1
                )
                RETURNING *
            """),
            {
                "wid": worker_id,
                "worker_has_gpu": caps.gpu,
                "worker_labels": caps.labels,
            },
        )
        await self._session.commit()
        row = result.mappings().first()
        if row is None:
            return None
        return Job(**dict(row))

    async def heartbeat(self, job_id: UUID, worker_id: str) -> None:
        await self._session.execute(
            text("UPDATE jobs SET heartbeat_at=now() WHERE id=:id AND worker_id=:wid"),
            {"id": job_id, "wid": worker_id},
        )
        await self._session.commit()

    async def mark_succeeded(self, job_id: UUID, artifacts: list[ArtifactRef]) -> None:
        import json
        await self._session.execute(
            text("""
                UPDATE jobs SET status='succeeded', finished_at=now(),
                    artifacts=:artifacts
                WHERE id=:id
            """),
            {"id": job_id, "artifacts": json.dumps([a.model_dump() for a in artifacts])},
        )
        await self._session.commit()

    async def mark_failed(self, job_id: UUID, reason: str) -> None:
        await self._session.execute(
            text("""
                UPDATE jobs SET status='failed', finished_at=now(), error=:error
                WHERE id=:id
            """),
            {"id": job_id, "error": reason},
        )
        await self._session.commit()

    async def requeue_stale(self, older_than: timedelta) -> int:
        result = await self._session.execute(
            text("""
                UPDATE jobs SET status='queued', worker_id=NULL,
                    started_at=NULL, heartbeat_at=NULL
                WHERE status='running'
                  AND heartbeat_at < now() - make_interval(secs => :secs)
            """),
            {"secs": older_than.total_seconds()},
        )
        await self._session.commit()
        return result.rowcount

    async def get(self, job_id: UUID) -> Job | None:
        result = await self._session.execute(
            text("SELECT * FROM jobs WHERE id=:id"), {"id": job_id}
        )
        row = result.mappings().first()
        if row is None:
            return None
        return Job(**dict(row))

    async def get_by_experiment(self, experiment_id: UUID) -> list[Job]:
        result = await self._session.execute(
            text("SELECT * FROM jobs WHERE experiment_id=:eid ORDER BY created_at"),
            {"eid": experiment_id},
        )
        return [Job(**dict(r)) for r in result.mappings().all()]
