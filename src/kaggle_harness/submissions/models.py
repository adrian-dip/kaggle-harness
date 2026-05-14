from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlmodel import Field, SQLModel


class Submission(SQLModel, table=True):
    __tablename__ = "submissions"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    experiment_id: UUID = Field(nullable=False, index=True)
    competition: str = Field(nullable=False)
    kaggle_ref: str | None = Field(default=None, nullable=True)
    public_score: float | None = Field(default=None, nullable=True)
    private_score: float | None = Field(default=None, nullable=True)
    status: str = Field(default="pending", nullable=False)
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
