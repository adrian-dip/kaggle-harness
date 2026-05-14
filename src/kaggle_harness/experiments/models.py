from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import text
from sqlmodel import Column, Field, SQLModel
from sqlalchemy.dialects.postgresql import JSONB


class Experiment(SQLModel, table=True):
    __tablename__ = "experiments"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    name: str = Field(nullable=False)
    manifest: dict[str, Any] = Field(
        default_factory=dict,
        sa_column=Column(JSONB, nullable=False, server_default=text("'{}'")),
    )
    mlflow_run_id: str | None = Field(default=None, nullable=True)
    # MinIO keys for each staged input: {"competition/titanic.zip": "/data/competitions/titanic"}
    staged_inputs: dict[str, Any] = Field(
        default_factory=dict,
        sa_column=Column(JSONB, nullable=False, server_default=text("'{}'")),
    )
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
