from datetime import UTC, datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from odoo_osi.db.models import IndexingJob


class IndexingJobRecorder:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def start(
        self,
        job_type: str,
        *,
        owner: str | None = None,
        repository: str | None = None,
        module: str | None = None,
        odoo_version: str | None = None,
        parameters: dict[str, Any] | None = None,
    ) -> IndexingJob:
        now = datetime.now(UTC)
        job = IndexingJob(
            job_type=job_type,
            status="running",
            owner=owner,
            repository=repository,
            module=module,
            odoo_version=odoo_version,
            parameters=parameters or {},
            counters={},
            errors=[],
            started_at=now,
        )
        self._session.add(job)
        await self._session.commit()
        return job

    async def succeed(
        self,
        job: IndexingJob,
        *,
        counters: dict[str, Any] | None = None,
        errors: list[Any] | None = None,
    ) -> None:
        await self._finish(job, status="succeeded", counters=counters, errors=errors)

    async def fail(
        self,
        job: IndexingJob,
        *,
        error: str,
        counters: dict[str, Any] | None = None,
        errors: list[Any] | None = None,
    ) -> None:
        merged_errors = list(errors or [])
        merged_errors.append(error)
        await self._finish(job, status="failed", counters=counters, errors=merged_errors)

    async def _finish(
        self,
        job: IndexingJob,
        *,
        status: str,
        counters: dict[str, Any] | None,
        errors: list[Any] | None,
    ) -> None:
        job.status = status
        job.counters = counters or {}
        job.errors = errors or []
        job.finished_at = datetime.now(UTC)
        await self._session.commit()
