from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from odoo_osi.db.base import Base, TimestampMixin


class Repository(Base, TimestampMixin):
    __tablename__ = "repositories"
    __table_args__ = (UniqueConstraint("provider", "owner", "name"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    provider: Mapped[str] = mapped_column(String(50), default="github", nullable=False)
    owner: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    full_name: Mapped[str] = mapped_column(String(512), nullable=False, index=True)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    default_branch: Mapped[str | None] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text)
    stars: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    forks: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    open_issues: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    license: Mapped[str | None] = mapped_column(String(255))
    last_commit_sha: Mapped[str | None] = mapped_column(String(128))
    last_commit_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_indexed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    archived: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    visibility: Mapped[str] = mapped_column(String(50), default="public", nullable=False)

    branches: Mapped[list["Branch"]] = relationship(back_populates="repository")
    modules: Mapped[list["Module"]] = relationship(back_populates="repository")


class Branch(Base, TimestampMixin):
    __tablename__ = "branches"
    __table_args__ = (UniqueConstraint("repository_id", "name"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    repository_id: Mapped[int] = mapped_column(ForeignKey("repositories.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    odoo_version: Mapped[str | None] = mapped_column(String(20), index=True)
    commit_sha: Mapped[str | None] = mapped_column(String(128))
    last_indexed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    is_odoo_version_branch: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    repository: Mapped[Repository] = relationship(back_populates="branches")
    modules: Mapped[list["Module"]] = relationship(back_populates="branch")


class Module(Base, TimestampMixin):
    __tablename__ = "modules"
    __table_args__ = (UniqueConstraint("repository_id", "branch_id", "technical_name"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    repository_id: Mapped[int] = mapped_column(ForeignKey("repositories.id"), nullable=False)
    branch_id: Mapped[int] = mapped_column(ForeignKey("branches.id"), nullable=False)
    technical_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    display_name: Mapped[str | None] = mapped_column(String(512))
    summary: Mapped[str | None] = mapped_column(Text)
    description: Mapped[str | None] = mapped_column(Text)
    odoo_version: Mapped[str | None] = mapped_column(String(20), index=True)
    module_version: Mapped[str | None] = mapped_column(String(50))
    category: Mapped[str | None] = mapped_column(String(255))
    license: Mapped[str | None] = mapped_column(String(255), index=True)
    license_source: Mapped[str | None] = mapped_column(Text)
    author: Mapped[str | None] = mapped_column(Text)
    maintainers: Mapped[list[str] | None] = mapped_column(JSON)
    website: Mapped[str | None] = mapped_column(Text)
    path: Mapped[str] = mapped_column(Text, nullable=False)
    installable: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    application: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    auto_install: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    source_url: Mapped[str | None] = mapped_column(Text)
    readme_path: Mapped[str | None] = mapped_column(Text)
    manifest_path: Mapped[str | None] = mapped_column(Text)
    last_commit_sha: Mapped[str | None] = mapped_column(String(128))

    repository: Mapped[Repository] = relationship(back_populates="modules")
    branch: Mapped[Branch] = relationship(back_populates="modules")
    dependencies: Mapped[list["Dependency"]] = relationship(back_populates="module")
    source_files: Mapped[list["SourceFile"]] = relationship(back_populates="module")
    search_documents: Mapped[list["SearchDocument"]] = relationship(back_populates="module")


class Dependency(Base, TimestampMixin):
    __tablename__ = "dependencies"

    id: Mapped[int] = mapped_column(primary_key=True)
    module_id: Mapped[int] = mapped_column(ForeignKey("modules.id"), nullable=False, index=True)
    dependency_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    dependency_type: Mapped[str] = mapped_column(String(50), nullable=False)
    is_external: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    source: Mapped[str] = mapped_column(String(255), nullable=False)

    module: Mapped[Module] = relationship(back_populates="dependencies")


class SourceFile(Base, TimestampMixin):
    __tablename__ = "source_files"
    __table_args__ = (UniqueConstraint("module_id", "path"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    module_id: Mapped[int] = mapped_column(ForeignKey("modules.id"), nullable=False, index=True)
    path: Mapped[str] = mapped_column(Text, nullable=False)
    file_type: Mapped[str] = mapped_column(String(50), nullable=False)
    language: Mapped[str | None] = mapped_column(String(50))
    size: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    sha: Mapped[str | None] = mapped_column(String(128))
    content_hash: Mapped[str | None] = mapped_column(String(128))
    indexed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    module: Mapped[Module] = relationship(back_populates="source_files")
    symbols: Mapped[list["Symbol"]] = relationship(back_populates="source_file")
    search_documents: Mapped[list["SearchDocument"]] = relationship(back_populates="source_file")


class Symbol(Base, TimestampMixin):
    __tablename__ = "symbols"

    id: Mapped[int] = mapped_column(primary_key=True)
    module_id: Mapped[int] = mapped_column(ForeignKey("modules.id"), nullable=False, index=True)
    source_file_id: Mapped[int] = mapped_column(ForeignKey("source_files.id"), nullable=False)
    symbol_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    name: Mapped[str | None] = mapped_column(String(512), index=True)
    odoo_model: Mapped[str | None] = mapped_column(String(255), index=True)
    inherited_model: Mapped[str | None] = mapped_column(String(255), index=True)
    xml_id: Mapped[str | None] = mapped_column(String(512), index=True)
    parent_xml_id: Mapped[str | None] = mapped_column(String(512), index=True)
    line_start: Mapped[int | None] = mapped_column(Integer)
    line_end: Mapped[int | None] = mapped_column(Integer)
    extra: Mapped[dict | None] = mapped_column(JSON)

    source_file: Mapped[SourceFile] = relationship(back_populates="symbols")


class SearchDocument(Base, TimestampMixin):
    __tablename__ = "search_documents"

    id: Mapped[int] = mapped_column(primary_key=True)
    module_id: Mapped[int] = mapped_column(ForeignKey("modules.id"), nullable=False, index=True)
    source_file_id: Mapped[int | None] = mapped_column(ForeignKey("source_files.id"))
    document_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    title: Mapped[str | None] = mapped_column(Text)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    extra: Mapped[dict | None] = mapped_column(JSON)

    module: Mapped[Module] = relationship(back_populates="search_documents")
    source_file: Mapped[SourceFile | None] = relationship(back_populates="search_documents")


class IndexingJob(Base, TimestampMixin):
    __tablename__ = "indexing_jobs"

    id: Mapped[int] = mapped_column(primary_key=True)
    job_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    owner: Mapped[str | None] = mapped_column(String(255), index=True)
    repository: Mapped[str | None] = mapped_column(String(255), index=True)
    module: Mapped[str | None] = mapped_column(String(255), index=True)
    odoo_version: Mapped[str | None] = mapped_column(String(20), index=True)
    parameters: Mapped[dict | None] = mapped_column(JSON)
    counters: Mapped[dict | None] = mapped_column(JSON)
    errors: Mapped[list | None] = mapped_column(JSON)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
