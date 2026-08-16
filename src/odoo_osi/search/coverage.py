from typing import Any

from sqlalchemy import distinct, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from odoo_osi.db.models import (
    Branch,
    IndexingJob,
    Module,
    Repository,
    SearchDocument,
    SourceFile,
    Symbol,
)


async def coverage_report_payload(
    session: AsyncSession,
    owner: str = "OCA",
    catalog_module_estimate: int | None = None,
) -> dict[str, Any]:
    """Return local index coverage and the best available external gap signals."""

    local_index = {
        "owner": owner,
        "repositories": await _count_repositories(session, owner),
        "version_branches": await _count_version_branches(session, owner),
        "modules": await _count_modules(session, owner),
        "source_files": await _count_source_files(session, owner),
        "symbols": await _count_symbols(session, owner),
        "search_documents": await _count_search_documents(session, owner),
    }
    evidence_depth = {
        "source_indexed_modules": await _count_modules_with_source_files(session, owner),
        "symbol_indexed_modules": await _count_modules_with_symbols(session, owner),
        "readme_indexed_modules": await _count_modules_with_document_type(
            session, owner, "readme_%"
        ),
        "security_indexed_modules": await _count_modules_with_document_type(
            session, owner, "security_access_rule"
        ),
    }
    evidence_depth["source_indexed_module_percent"] = _percent(
        evidence_depth["source_indexed_modules"], local_index["modules"]
    )
    evidence_depth["symbol_indexed_module_percent"] = _percent(
        evidence_depth["symbol_indexed_modules"], local_index["modules"]
    )
    evidence_depth["readme_indexed_module_percent"] = _percent(
        evidence_depth["readme_indexed_modules"], local_index["modules"]
    )
    evidence_depth["security_indexed_module_percent"] = _percent(
        evidence_depth["security_indexed_modules"], local_index["modules"]
    )

    latest_discovery = await _latest_job_payload(session, "discover_oca", owner)
    latest_full_discovery = await _latest_job_payload(
        session, "discover_oca", owner, repository_is_none=True
    )
    latest_source_index = await _latest_job_payload(session, "index_source", owner)

    return {
        "owner": owner,
        "status": _coverage_status(
            local_index["modules"],
            evidence_depth["source_indexed_modules"],
        ),
        "local_index": local_index,
        "evidence_depth": evidence_depth,
        "latest_discovery_job": latest_discovery,
        "latest_source_index_job": latest_source_index,
        "benchmarks": {
            "github_discovery": _github_discovery_benchmark(
                local_index["repositories"], latest_full_discovery
            ),
            "external_module_catalog": _external_catalog_benchmark(
                local_index["modules"], catalog_module_estimate
            ),
        },
        "limitations": _limitations(catalog_module_estimate, latest_full_discovery),
        "next_steps": _next_steps(owner),
    }


async def _count_repositories(session: AsyncSession, owner: str) -> int:
    statement = select(func.count()).select_from(Repository).where(Repository.owner == owner)
    return await _scalar_count(session, statement)


async def _count_version_branches(session: AsyncSession, owner: str) -> int:
    statement = (
        select(func.count())
        .select_from(Branch)
        .join(Repository, Repository.id == Branch.repository_id)
        .where(Repository.owner == owner, Branch.is_odoo_version_branch.is_(True))
    )
    return await _scalar_count(session, statement)


async def _count_modules(session: AsyncSession, owner: str) -> int:
    statement = (
        select(func.count())
        .select_from(Module)
        .join(Repository, Repository.id == Module.repository_id)
        .where(Repository.owner == owner)
    )
    return await _scalar_count(session, statement)


async def _count_source_files(session: AsyncSession, owner: str) -> int:
    statement = (
        select(func.count())
        .select_from(SourceFile)
        .join(Module, Module.id == SourceFile.module_id)
        .join(Repository, Repository.id == Module.repository_id)
        .where(Repository.owner == owner)
    )
    return await _scalar_count(session, statement)


async def _count_symbols(session: AsyncSession, owner: str) -> int:
    statement = (
        select(func.count())
        .select_from(Symbol)
        .join(Module, Module.id == Symbol.module_id)
        .join(Repository, Repository.id == Module.repository_id)
        .where(Repository.owner == owner)
    )
    return await _scalar_count(session, statement)


async def _count_search_documents(session: AsyncSession, owner: str) -> int:
    statement = (
        select(func.count())
        .select_from(SearchDocument)
        .join(Module, Module.id == SearchDocument.module_id)
        .join(Repository, Repository.id == Module.repository_id)
        .where(Repository.owner == owner)
    )
    return await _scalar_count(session, statement)


async def _count_modules_with_source_files(session: AsyncSession, owner: str) -> int:
    statement = (
        select(func.count(distinct(SourceFile.module_id)))
        .select_from(SourceFile)
        .join(Module, Module.id == SourceFile.module_id)
        .join(Repository, Repository.id == Module.repository_id)
        .where(Repository.owner == owner)
    )
    return await _scalar_count(session, statement)


async def _count_modules_with_symbols(session: AsyncSession, owner: str) -> int:
    statement = (
        select(func.count(distinct(Symbol.module_id)))
        .select_from(Symbol)
        .join(Module, Module.id == Symbol.module_id)
        .join(Repository, Repository.id == Module.repository_id)
        .where(Repository.owner == owner)
    )
    return await _scalar_count(session, statement)


async def _count_modules_with_document_type(
    session: AsyncSession,
    owner: str,
    document_type: str,
) -> int:
    statement = (
        select(func.count(distinct(SearchDocument.module_id)))
        .select_from(SearchDocument)
        .join(Module, Module.id == SearchDocument.module_id)
        .join(Repository, Repository.id == Module.repository_id)
        .where(Repository.owner == owner)
    )
    if "%" in document_type:
        statement = statement.where(SearchDocument.document_type.like(document_type))
    else:
        statement = statement.where(SearchDocument.document_type == document_type)
    return await _scalar_count(session, statement)


async def _latest_job_payload(
    session: AsyncSession,
    job_type: str,
    owner: str,
    repository_is_none: bool = False,
) -> dict[str, Any] | None:
    statement = (
        select(IndexingJob)
        .where(IndexingJob.job_type == job_type, IndexingJob.owner == owner)
        .order_by(IndexingJob.created_at.desc())
        .limit(1)
    )
    if repository_is_none:
        statement = statement.where(IndexingJob.repository.is_(None))

    result = await session.execute(statement)
    job = result.scalar_one_or_none()
    if job is None:
        return None

    return {
        "id": job.id,
        "job_type": job.job_type,
        "status": job.status,
        "repository": job.repository,
        "module": job.module,
        "odoo_version": job.odoo_version,
        "parameters": job.parameters or {},
        "counters": job.counters or {},
        "error_count": len(job.errors or []),
        "started_at": job.started_at.isoformat() if job.started_at else None,
        "finished_at": job.finished_at.isoformat() if job.finished_at else None,
    }


async def _scalar_count(session: AsyncSession, statement) -> int:
    result = await session.execute(statement)
    return int(result.scalar_one())


def _github_discovery_benchmark(
    indexed_repositories: int,
    latest_full_discovery: dict[str, Any] | None,
) -> dict[str, Any]:
    if latest_full_discovery is None:
        return {
            "estimated_total_repositories": None,
            "indexed_repositories": indexed_repositories,
            "remaining_repositories": None,
            "coverage_percent": None,
            "basis": "No full owner discovery job has been recorded yet.",
        }

    repositories_seen = latest_full_discovery["counters"].get("repositories_seen")
    if not isinstance(repositories_seen, int) or repositories_seen <= 0:
        return {
            "estimated_total_repositories": None,
            "indexed_repositories": indexed_repositories,
            "remaining_repositories": None,
            "coverage_percent": None,
            "basis": "Latest full discovery job does not include repositories_seen.",
        }

    return {
        "estimated_total_repositories": repositories_seen,
        "indexed_repositories": indexed_repositories,
        "remaining_repositories": max(repositories_seen - indexed_repositories, 0),
        "coverage_percent": _percent(indexed_repositories, repositories_seen),
        "basis": "Latest full OCA GitHub owner discovery job.",
    }


def _external_catalog_benchmark(
    indexed_modules: int,
    catalog_module_estimate: int | None,
) -> dict[str, Any]:
    if catalog_module_estimate is None or catalog_module_estimate <= 0:
        return {
            "estimated_total_modules": None,
            "indexed_modules": indexed_modules,
            "remaining_modules": None,
            "coverage_percent": None,
            "basis": "No external module catalog estimate configured.",
        }

    return {
        "estimated_total_modules": catalog_module_estimate,
        "indexed_modules": indexed_modules,
        "remaining_modules": max(catalog_module_estimate - indexed_modules, 0),
        "coverage_percent": _percent(indexed_modules, catalog_module_estimate),
        "basis": "Configured external catalog estimate; use as a rough gap signal only.",
    }


def _coverage_status(indexed_modules: int, source_indexed_modules: int) -> str:
    if indexed_modules == 0:
        return "empty"
    if source_indexed_modules == 0:
        return "manifest_only"
    if source_indexed_modules < indexed_modules:
        return "partial_source_index"
    return "source_indexed"


def _limitations(
    catalog_module_estimate: int | None,
    latest_full_discovery: dict[str, Any] | None,
) -> list[str]:
    limitations = [
        "Local indexed counts are authoritative only for data already persisted in this database.",
        "Live GitHub fallback candidates are discovery leads until their manifests and source "
        "files are indexed.",
    ]
    if latest_full_discovery is None:
        limitations.append(
            "No full owner discovery job is recorded, so GitHub repository gap is unknown."
        )
    if catalog_module_estimate is not None:
        limitations.append(
            "The external module catalog estimate is not proof that every listed module is "
            "installable, source-backed, or unique across Odoo versions."
        )
    return limitations


def _next_steps(owner: str) -> list[str]:
    return [
        "Run broad discovery with "
        f"`odoo-osi discover-oca --owner {owner} --repo-limit 0 --branch-limit 0 "
        "--module-limit 0 --persist`.",
        "Run targeted `odoo-osi index-source` jobs for high-priority repositories and "
        "Odoo versions.",
        "Use `discovered_not_indexed` MCP results as leads and run their indexing guidance "
        "before coding from them.",
    ]


def _percent(part: int, total: int) -> float | None:
    if total <= 0:
        return None
    return round((part / total) * 100, 2)
