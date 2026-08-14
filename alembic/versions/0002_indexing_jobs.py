"""Add indexing job ledger.

Revision ID: 0002_indexing_jobs
Revises: 0001_initial_schema
Create Date: 2026-08-14
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0002_indexing_jobs"
down_revision: str | None = "0001_initial_schema"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def created_at_column() -> sa.Column:
    return sa.Column(
        "created_at",
        sa.DateTime(timezone=True),
        server_default=sa.text("now()"),
        nullable=False,
    )


def updated_at_column() -> sa.Column:
    return sa.Column(
        "updated_at",
        sa.DateTime(timezone=True),
        server_default=sa.text("now()"),
        nullable=False,
    )


def upgrade() -> None:
    op.create_table(
        "indexing_jobs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("job_type", sa.String(length=100), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("owner", sa.String(length=255), nullable=True),
        sa.Column("repository", sa.String(length=255), nullable=True),
        sa.Column("module", sa.String(length=255), nullable=True),
        sa.Column("odoo_version", sa.String(length=20), nullable=True),
        sa.Column("parameters", sa.JSON(), nullable=True),
        sa.Column("counters", sa.JSON(), nullable=True),
        sa.Column("errors", sa.JSON(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        created_at_column(),
        updated_at_column(),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_indexing_jobs")),
    )
    op.create_index(op.f("ix_indexing_jobs_job_type"), "indexing_jobs", ["job_type"])
    op.create_index(op.f("ix_indexing_jobs_module"), "indexing_jobs", ["module"])
    op.create_index(op.f("ix_indexing_jobs_odoo_version"), "indexing_jobs", ["odoo_version"])
    op.create_index(op.f("ix_indexing_jobs_owner"), "indexing_jobs", ["owner"])
    op.create_index(op.f("ix_indexing_jobs_repository"), "indexing_jobs", ["repository"])
    op.create_index(op.f("ix_indexing_jobs_status"), "indexing_jobs", ["status"])


def downgrade() -> None:
    op.drop_table("indexing_jobs")
