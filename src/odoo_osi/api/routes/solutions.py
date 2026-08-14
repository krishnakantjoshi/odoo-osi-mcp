from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from odoo_osi.db.session import get_session
from odoo_osi.search.solutions import SolutionService, solution_result_payload

router = APIRouter(prefix="/solutions", tags=["solutions"])
SessionDep = Annotated[AsyncSession, Depends(get_session)]


class FindSolutionRequest(BaseModel):
    requirement: str = Field(min_length=1)
    odoo_version: str | None = None
    limit: int = Field(default=8, ge=1, le=25)


class SolutionCandidate(BaseModel):
    repository: str
    module: str
    odoo_version: str | None
    evidence_level: str
    summary: str | None
    license: str | None
    dependencies: list[str]
    source_url: str | None
    target_odoo_version: str | None
    version_status: str
    migration_effort: str | None
    migration_guidance: list[str]
    indexing_guidance: list[str]
    confidence: float
    why_matched: list[str]
    warnings: list[str]
    evidence: dict


class FindSolutionResponse(BaseModel):
    requirement: str
    recommendation: str
    candidates: list[SolutionCandidate]


@router.post("/find", response_model=FindSolutionResponse)
async def find_solution(
    request: FindSolutionRequest,
    session: SessionDep,
) -> FindSolutionResponse:
    result = await SolutionService(session).find_solution(
        requirement=request.requirement,
        odoo_version=request.odoo_version,
        limit=request.limit,
    )
    return FindSolutionResponse.model_validate(solution_result_payload(result))
