from datetime import datetime
from typing import Annotated, Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from odoo_osi.core.config import get_settings
from odoo_osi.db.models import (
    Branch,
    IndexingJob,
    Module,
    Repository,
    SearchDocument,
    SourceFile,
    Symbol,
)
from odoo_osi.db.session import get_session
from odoo_osi.search.coverage import coverage_report_payload

router = APIRouter(prefix="/indexing", tags=["indexing"])
SessionDep = Annotated[AsyncSession, Depends(get_session)]


class IndexingStatusResponse(BaseModel):
    repositories: int
    branches: int
    modules: int
    source_files: int
    symbols: int
    search_documents: int
    jobs: dict[str, int]
    recent_jobs: list["IndexingJobSummary"]


class IndexingJobSummary(BaseModel):
    id: int
    job_type: str
    status: str
    owner: str | None
    repository: str | None
    module: str | None
    odoo_version: str | None
    counters: dict[str, Any]
    error_count: int
    started_at: datetime | None
    finished_at: datetime | None


class CoverageReportResponse(BaseModel):
    owner: str
    status: str
    local_index: dict[str, Any]
    evidence_depth: dict[str, Any]
    latest_discovery_job: dict[str, Any] | None
    latest_source_index_job: dict[str, Any] | None
    benchmarks: dict[str, Any]
    limitations: list[str]
    next_steps: list[str]


@router.get("/status", response_model=IndexingStatusResponse)
async def indexing_status(
    session: SessionDep,
) -> IndexingStatusResponse:
    return IndexingStatusResponse(
        repositories=await _count(session, Repository),
        branches=await _count(session, Branch),
        modules=await _count(session, Module),
        source_files=await _count(session, SourceFile),
        symbols=await _count(session, Symbol),
        search_documents=await _count(session, SearchDocument),
        jobs=await _job_counts(session),
        recent_jobs=await _recent_jobs(session),
    )


@router.get("/coverage", response_model=CoverageReportResponse)
async def indexing_coverage(
    session: SessionDep,
    owner: str | None = None,
) -> CoverageReportResponse:
    settings = get_settings()
    payload = await coverage_report_payload(
        session=session,
        owner=owner or settings.github_owner,
        catalog_module_estimate=settings.oca_apps_module_estimate,
    )
    return CoverageReportResponse(**payload)


async def _count(session: AsyncSession, model: type) -> int:
    result = await session.execute(select(func.count()).select_from(model))
    return int(result.scalar_one())


async def _job_counts(session: AsyncSession) -> dict[str, int]:
    result = await session.execute(
        select(IndexingJob.status, func.count())
        .select_from(IndexingJob)
        .group_by(IndexingJob.status)
    )
    return {status: int(count) for status, count in result.all()}


async def _recent_jobs(session: AsyncSession) -> list[IndexingJobSummary]:
    result = await session.execute(
        select(IndexingJob).order_by(IndexingJob.created_at.desc()).limit(10)
    )
    jobs = result.scalars().all()
    return [
        IndexingJobSummary(
            id=job.id,
            job_type=job.job_type,
            status=job.status,
            owner=job.owner,
            repository=job.repository,
            module=job.module,
            odoo_version=job.odoo_version,
            counters=job.counters or {},
            error_count=len(job.errors or []),
            started_at=job.started_at,
            finished_at=job.finished_at,
        )
        for job in jobs
    ]
