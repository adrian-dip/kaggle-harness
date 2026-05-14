from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import text
from sqlmodel import Column, Field, SQLModel
from sqlalchemy.dialects.postgresql import JSONB, ARRAY
from sqlalchemy import String


class Worker(SQLModel, table=True):
    __tablename__ = "workers"

    id: str = Field(primary_key=True)
    labels: list[str] = Field(
        default_factory=list,
        sa_column=Column(ARRAY(String), nullable=False, server_default=text("'{}'"))
    )
    gpu: bool = Field(default=False, nullable=False)
    cpu: int = Field(default=1, nullable=False)
    memory_mb: int = Field(default=2048, nullable=False)
    last_seen: datetime = Field(default_factory=datetime.utcnow, nullable=False)
