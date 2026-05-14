from __future__ import annotations

import enum
from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import text
from sqlmodel import Column, Field, SQLModel
from sqlalchemy.dialects.postgresql import JSONB


class JobStatus(str, enum.Enum):
    queued = "queued"
    running = "running"
    succeeded = "succeeded"
    failed = "failed"
    cancelled = "cancelled"


class Job(SQLModel, table=True):
    __tablename__ = "jobs"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    experiment_id: UUID = Field(nullable=False, index=True)
    bundle_id: str = Field(nullable=False)
    status: str = Field(default=JobStatus.queued, nullable=False, index=True)
    worker_id: str | None = Field(default=None, nullable=True)
    priority: int = Field(default=0, nullable=False)
    requires: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSONB, nullable=False, server_default=text("'{}'")))
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    started_at: datetime | None = Field(default=None, nullable=True)
    finished_at: datetime | None = Field(default=None, nullable=True)
    heartbeat_at: datetime | None = Field(default=None, nullable=True)
    error: str | None = Field(default=None, nullable=True)
    artifacts: list[Any] = Field(default_factory=list, sa_column=Column(JSONB, nullable=False, server_default=text("'[]'")))
