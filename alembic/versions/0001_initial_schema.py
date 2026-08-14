"""Initial schema.

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-08-14
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0001_initial_schema"
down_revision: str | None = None
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
        "repositories",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("provider", sa.String(length=50), nullable=False),
        sa.Column("owner", sa.String(length=255), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("full_name", sa.String(length=512), nullable=False),
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column("default_branch", sa.String(length=255), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("stars", sa.Integer(), nullable=False),
        sa.Column("forks", sa.Integer(), nullable=False),
        sa.Column("open_issues", sa.Integer(), nullable=False),
        sa.Column("license", sa.String(length=255), nullable=True),
        sa.Column("last_commit_sha", sa.String(length=128), nullable=True),
        sa.Column("last_commit_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_indexed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("archived", sa.Boolean(), nullable=False),
        sa.Column("visibility", sa.String(length=50), nullable=False),
        created_at_column(),
        updated_at_column(),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_repositories")),
        sa.UniqueConstraint("provider", "owner", "name", name=op.f("uq_repositories_provider")),
    )
    op.create_index(op.f("ix_repositories_full_name"), "repositories", ["full_name"], unique=False)
    op.create_index(op.f("ix_repositories_name"), "repositories", ["name"], unique=False)
    op.create_index(op.f("ix_repositories_owner"), "repositories", ["owner"], unique=False)

    op.create_table(
        "branches",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("repository_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("odoo_version", sa.String(length=20), nullable=True),
        sa.Column("commit_sha", sa.String(length=128), nullable=True),
        sa.Column("last_indexed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_odoo_version_branch", sa.Boolean(), nullable=False),
        created_at_column(),
        updated_at_column(),
        sa.ForeignKeyConstraint(
            ["repository_id"],
            ["repositories.id"],
            name=op.f("fk_branches_repository_id_repositories"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_branches")),
        sa.UniqueConstraint("repository_id", "name", name=op.f("uq_branches_repository_id")),
    )
    op.create_index(op.f("ix_branches_name"), "branches", ["name"], unique=False)
    op.create_index(op.f("ix_branches_odoo_version"), "branches", ["odoo_version"], unique=False)

    op.create_table(
        "modules",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("repository_id", sa.Integer(), nullable=False),
        sa.Column("branch_id", sa.Integer(), nullable=False),
        sa.Column("technical_name", sa.String(length=255), nullable=False),
        sa.Column("display_name", sa.String(length=512), nullable=True),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("odoo_version", sa.String(length=20), nullable=True),
        sa.Column("module_version", sa.String(length=50), nullable=True),
        sa.Column("category", sa.String(length=255), nullable=True),
        sa.Column("license", sa.String(length=255), nullable=True),
        sa.Column("license_source", sa.Text(), nullable=True),
        sa.Column("author", sa.Text(), nullable=True),
        sa.Column("maintainers", sa.JSON(), nullable=True),
        sa.Column("website", sa.Text(), nullable=True),
        sa.Column("path", sa.Text(), nullable=False),
        sa.Column("installable", sa.Boolean(), nullable=False),
        sa.Column("application", sa.Boolean(), nullable=False),
        sa.Column("auto_install", sa.Boolean(), nullable=False),
        sa.Column("source_url", sa.Text(), nullable=True),
        sa.Column("readme_path", sa.Text(), nullable=True),
        sa.Column("manifest_path", sa.Text(), nullable=True),
        sa.Column("last_commit_sha", sa.String(length=128), nullable=True),
        created_at_column(),
        updated_at_column(),
        sa.ForeignKeyConstraint(
            ["branch_id"], ["branches.id"], name=op.f("fk_modules_branch_id_branches")
        ),
        sa.ForeignKeyConstraint(
            ["repository_id"],
            ["repositories.id"],
            name=op.f("fk_modules_repository_id_repositories"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_modules")),
        sa.UniqueConstraint(
            "repository_id", "branch_id", "technical_name", name=op.f("uq_modules_repository_id")
        ),
    )
    op.create_index(op.f("ix_modules_license"), "modules", ["license"], unique=False)
    op.create_index(op.f("ix_modules_odoo_version"), "modules", ["odoo_version"], unique=False)
    op.create_index(op.f("ix_modules_technical_name"), "modules", ["technical_name"], unique=False)

    op.create_table(
        "dependencies",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("module_id", sa.Integer(), nullable=False),
        sa.Column("dependency_name", sa.String(length=255), nullable=False),
        sa.Column("dependency_type", sa.String(length=50), nullable=False),
        sa.Column("is_external", sa.Boolean(), nullable=False),
        sa.Column("source", sa.String(length=255), nullable=False),
        created_at_column(),
        updated_at_column(),
        sa.ForeignKeyConstraint(
            ["module_id"], ["modules.id"], name=op.f("fk_dependencies_module_id_modules")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_dependencies")),
    )
    op.create_index(
        op.f("ix_dependencies_dependency_name"),
        "dependencies",
        ["dependency_name"],
        unique=False,
    )
    op.create_index(op.f("ix_dependencies_module_id"), "dependencies", ["module_id"], unique=False)

    op.create_table(
        "source_files",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("module_id", sa.Integer(), nullable=False),
        sa.Column("path", sa.Text(), nullable=False),
        sa.Column("file_type", sa.String(length=50), nullable=False),
        sa.Column("language", sa.String(length=50), nullable=True),
        sa.Column("size", sa.Integer(), nullable=False),
        sa.Column("sha", sa.String(length=128), nullable=True),
        sa.Column("content_hash", sa.String(length=128), nullable=True),
        sa.Column("indexed_at", sa.DateTime(timezone=True), nullable=True),
        created_at_column(),
        updated_at_column(),
        sa.ForeignKeyConstraint(
            ["module_id"], ["modules.id"], name=op.f("fk_source_files_module_id_modules")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_source_files")),
        sa.UniqueConstraint("module_id", "path", name=op.f("uq_source_files_module_id")),
    )
    op.create_index(op.f("ix_source_files_module_id"), "source_files", ["module_id"], unique=False)

    op.create_table(
        "search_documents",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("module_id", sa.Integer(), nullable=False),
        sa.Column("source_file_id", sa.Integer(), nullable=True),
        sa.Column("document_type", sa.String(length=100), nullable=False),
        sa.Column("title", sa.Text(), nullable=True),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("extra", sa.JSON(), nullable=True),
        created_at_column(),
        updated_at_column(),
        sa.ForeignKeyConstraint(
            ["module_id"], ["modules.id"], name=op.f("fk_search_documents_module_id_modules")
        ),
        sa.ForeignKeyConstraint(
            ["source_file_id"],
            ["source_files.id"],
            name=op.f("fk_search_documents_source_file_id_source_files"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_search_documents")),
    )
    op.create_index(
        op.f("ix_search_documents_document_type"),
        "search_documents",
        ["document_type"],
        unique=False,
    )
    op.create_index(
        op.f("ix_search_documents_module_id"),
        "search_documents",
        ["module_id"],
        unique=False,
    )

    op.create_table(
        "symbols",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("module_id", sa.Integer(), nullable=False),
        sa.Column("source_file_id", sa.Integer(), nullable=False),
        sa.Column("symbol_type", sa.String(length=100), nullable=False),
        sa.Column("name", sa.String(length=512), nullable=True),
        sa.Column("odoo_model", sa.String(length=255), nullable=True),
        sa.Column("inherited_model", sa.String(length=255), nullable=True),
        sa.Column("xml_id", sa.String(length=512), nullable=True),
        sa.Column("parent_xml_id", sa.String(length=512), nullable=True),
        sa.Column("line_start", sa.Integer(), nullable=True),
        sa.Column("line_end", sa.Integer(), nullable=True),
        sa.Column("extra", sa.JSON(), nullable=True),
        created_at_column(),
        updated_at_column(),
        sa.ForeignKeyConstraint(
            ["module_id"], ["modules.id"], name=op.f("fk_symbols_module_id_modules")
        ),
        sa.ForeignKeyConstraint(
            ["source_file_id"],
            ["source_files.id"],
            name=op.f("fk_symbols_source_file_id_source_files"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_symbols")),
    )
    op.create_index(
        op.f("ix_symbols_inherited_model"),
        "symbols",
        ["inherited_model"],
        unique=False,
    )
    op.create_index(op.f("ix_symbols_module_id"), "symbols", ["module_id"], unique=False)
    op.create_index(op.f("ix_symbols_name"), "symbols", ["name"], unique=False)
    op.create_index(op.f("ix_symbols_odoo_model"), "symbols", ["odoo_model"], unique=False)
    op.create_index(op.f("ix_symbols_parent_xml_id"), "symbols", ["parent_xml_id"], unique=False)
    op.create_index(op.f("ix_symbols_symbol_type"), "symbols", ["symbol_type"], unique=False)
    op.create_index(op.f("ix_symbols_xml_id"), "symbols", ["xml_id"], unique=False)


def downgrade() -> None:
    op.drop_table("symbols")
    op.drop_table("search_documents")
    op.drop_table("source_files")
    op.drop_table("dependencies")
    op.drop_table("modules")
    op.drop_table("branches")
    op.drop_table("repositories")
