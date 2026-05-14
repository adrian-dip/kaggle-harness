"""create core tables

Revision ID: ce94e3e3
Revises:
Create Date: 2026-05-13 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, ARRAY

revision = "ce94e3e3"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "experiments",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("manifest", JSONB(), nullable=False, server_default="{}"),
        sa.Column("mlflow_run_id", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )

    op.create_table(
        "workers",
        sa.Column("id", sa.Text(), primary_key=True),
        sa.Column("labels", ARRAY(sa.Text()), nullable=False, server_default="{}"),
        sa.Column("gpu", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("cpu", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("memory_mb", sa.Integer(), nullable=False, server_default="2048"),
        sa.Column("last_seen", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "jobs",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("experiment_id", sa.Uuid(), sa.ForeignKey("experiments.id"), nullable=False, index=True),
        sa.Column("bundle_id", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False, server_default="queued", index=True),
        sa.Column("worker_id", sa.Text(), sa.ForeignKey("workers.id"), nullable=True),
        sa.Column("priority", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("requires", JSONB(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("finished_at", sa.DateTime(), nullable=True),
        sa.Column("heartbeat_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("artifacts", JSONB(), nullable=False, server_default="[]"),
    )

    op.create_table(
        "submissions",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("experiment_id", sa.Uuid(), sa.ForeignKey("experiments.id"), nullable=False),
        sa.Column("competition", sa.Text(), nullable=False),
        sa.Column("kaggle_ref", sa.Text(), nullable=True),
        sa.Column("public_score", sa.Float(), nullable=True),
        sa.Column("private_score", sa.Float(), nullable=True),
        sa.Column("status", sa.Text(), nullable=False, server_default="pending"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("submissions")
    op.drop_table("jobs")
    op.drop_table("workers")
    op.drop_table("experiments")
