from __future__ import annotations

from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel


class WorkerCapabilities(BaseModel):
    worker_id: str
    labels: list[str] = []
    gpu: bool = False
    cpu: int = 1
    memory_mb: int = 2048


class RegisterRequest(BaseModel):
    capabilities: WorkerCapabilities


class RegisterResponse(BaseModel):
    token: str


class ClaimRequest(BaseModel):
    worker_id: str
    capabilities: WorkerCapabilities


class JobRequires(BaseModel):
    gpu: bool = False
    labels: list[str] = []
    cpu: int = 1
    memory_mb: int = 2048


class StagedInput(BaseModel):
    local_path: str       # e.g. /data/competitions/titanic
    download_url: str     # presigned MinIO URL


class JobAssignment(BaseModel):
    job_id: UUID
    experiment_id: UUID
    bundle_id: str
    entrypoint: str
    image: str
    requirements_file: str | None
    env: dict[str, str] = {}
    requires: JobRequires = JobRequires()
    staged_inputs: list[StagedInput] = []
    declared_outputs: list[str] = []
    mlflow_run_id: str | None = None
    mlflow_tracking_uri: str | None = None
    mlflow_experiment_name: str | None = None


class LogChunk(BaseModel):
    job_id: UUID
    seq: int
    text: str
    ts: datetime


class ArtifactRef(BaseModel):
    name: str
    store_key: str


class JobStatus(str, Enum):
    queued = "queued"
    running = "running"
    succeeded = "succeeded"
    failed = "failed"
    cancelled = "cancelled"


class JobReport(BaseModel):
    job_id: UUID
    status: JobStatus
    artifacts: list[ArtifactRef] = []
    error: str | None = None
