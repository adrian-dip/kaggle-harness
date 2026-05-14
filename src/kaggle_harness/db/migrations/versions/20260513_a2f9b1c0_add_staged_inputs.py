"""add staged_inputs to experiments

Revision ID: a2f9b1c0
Revises: ce94e3e3
Create Date: 2026-05-13 00:01:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = "a2f9b1c0"
down_revision = "ce94e3e3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "experiments",
        sa.Column("staged_inputs", JSONB(), nullable=False, server_default="{}"),
    )


def downgrade() -> None:
    op.drop_column("experiments", "staged_inputs")
