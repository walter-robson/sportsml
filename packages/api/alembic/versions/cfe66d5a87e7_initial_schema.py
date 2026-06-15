"""initial schema — tenants + model_runs

Revision ID: cfe66d5a87e7
Revises:
Create Date: 2026-06-14 22:12:03.159734

Targets Postgres (Supabase). The test suite skips migrations and uses
``Base.metadata.create_all`` against in-memory SQLite instead.
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

# revision identifiers, used by Alembic.
revision: str = "cfe66d5a87e7"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "tenants",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("slug", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_tenants_slug", "tenants", ["slug"], unique=True)

    op.create_table(
        "model_runs",
        sa.Column("run_id", sa.String(length=64), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("model_id", sa.String(length=128), nullable=False),
        sa.Column("config_hash", sa.String(length=64), nullable=False),
        sa.Column("config_json", JSONB(), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("duration_s", sa.Float(), nullable=True),
        sa.Column("row_count", sa.Integer(), nullable=True),
        sa.Column("output_dataset", sa.Text(), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("label", sa.String(length=255), nullable=True),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("run_id"),
        sa.UniqueConstraint("run_id", name="uq_model_runs_run_id"),
    )
    op.create_index(
        "idx_model_runs_lookup",
        "model_runs",
        ["tenant_id", "model_id", "config_hash", "status"],
    )
    op.create_index("ix_model_runs_config_hash", "model_runs", ["config_hash"])
    op.create_index("ix_model_runs_model_id", "model_runs", ["model_id"])
    op.create_index("ix_model_runs_status", "model_runs", ["status"])
    op.create_index("ix_model_runs_tenant_id", "model_runs", ["tenant_id"])


def downgrade() -> None:
    op.drop_index("ix_model_runs_tenant_id", table_name="model_runs")
    op.drop_index("ix_model_runs_status", table_name="model_runs")
    op.drop_index("ix_model_runs_model_id", table_name="model_runs")
    op.drop_index("ix_model_runs_config_hash", table_name="model_runs")
    op.drop_index("idx_model_runs_lookup", table_name="model_runs")
    op.drop_table("model_runs")
    op.drop_index("ix_tenants_slug", table_name="tenants")
    op.drop_table("tenants")
