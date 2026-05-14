from __future__ import annotations

from uuid import UUID

import httpx

from kaggle_harness.protocol.messages import (
    ArtifactRef,
    ClaimRequest,
    JobAssignment,
    JobReport,
    JobStatus,
    RegisterRequest,
    WorkerCapabilities,
)
from kaggle_harness_worker.config import WorkerSettings


class GatewayClient:
    def __init__(self, settings: WorkerSettings) -> None:
        self._base = settings.gateway_url.rstrip("/")
        self._token = settings.worker_token
        self._caps = WorkerCapabilities(
            worker_id=settings.worker_id,
            labels=settings.worker_labels,
            gpu=settings.worker_gpu,
            cpu=settings.worker_cpu,
            memory_mb=settings.worker_memory_mb,
        )

    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self._token}"}

    def _http(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(base_url=self._base, headers=self._headers(), timeout=35.0)

    async def register(self) -> None:
        async with self._http() as client:
            resp = await client.post(
                "/workers/register",
                content=RegisterRequest(capabilities=self._caps).model_dump_json(),
                headers={"Content-Type": "application/json"},
            )
            resp.raise_for_status()

    async def claim(self) -> JobAssignment | None:
        async with self._http() as client:
            resp = await client.post(
                "/workers/claim",
                content=ClaimRequest(
                    worker_id=self._caps.worker_id, capabilities=self._caps
                ).model_dump_json(),
                headers={"Content-Type": "application/json"},
            )
            resp.raise_for_status()
            if resp.status_code == 204 or resp.text.strip() in ("null", ""):
                return None
            data = resp.json()
            if data is None:
                return None
            return JobAssignment.model_validate(data)

    async def heartbeat(self, job_id: UUID) -> None:
        async with self._http() as client:
            resp = await client.post(
                f"/workers/jobs/{job_id}/heartbeat",
                params={"worker_id": self._caps.worker_id},
            )
            resp.raise_for_status()

    async def send_log(self, job_id: UUID, seq: int, text: str) -> None:
        from datetime import datetime
        from kaggle_harness.protocol.messages import LogChunk
        chunk = LogChunk(job_id=job_id, seq=seq, text=text, ts=datetime.utcnow())
        async with self._http() as client:
            resp = await client.post(
                f"/workers/jobs/{job_id}/logs",
                content=chunk.model_dump_json(),
                headers={"Content-Type": "application/json"},
            )
            resp.raise_for_status()

    async def report(self, report: JobReport) -> None:
        async with self._http() as client:
            resp = await client.post(
                f"/workers/jobs/{report.job_id}/report",
                content=report.model_dump_json(),
                headers={"Content-Type": "application/json"},
            )
            resp.raise_for_status()

    async def bundle_url(self, bundle_id: str) -> str:
        """Return the redirect URL (presigned) for downloading a bundle."""
        async with httpx.AsyncClient(
            base_url=self._base, headers=self._headers(), timeout=10.0, follow_redirects=False
        ) as client:
            resp = await client.get(f"/workers/bundles/{bundle_id}")
            if resp.status_code in (301, 302, 307, 308):
                return resp.headers["location"]
            resp.raise_for_status()
            return str(resp.url)

    async def get_artifact_upload_url(self, job_id: UUID, filename: str) -> tuple[str, str]:
        """Returns (upload_url, store_key) for uploading an artifact directly to MinIO."""
        async with self._http() as client:
            resp = await client.post(f"/workers/jobs/{job_id}/artifacts/{filename}")
            resp.raise_for_status()
            data = resp.json()
            return data["upload_url"], data["store_key"]

    async def upload_artifact(self, job_id: UUID, filename: str, data: bytes) -> ArtifactRef:
        upload_url, store_key = await self.get_artifact_upload_url(job_id, filename)
        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.put(upload_url, content=data)
            resp.raise_for_status()
        return ArtifactRef(name=filename, store_key=store_key)
