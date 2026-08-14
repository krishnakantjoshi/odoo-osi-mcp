from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from odoo_osi.db.session import get_session
from odoo_osi.search.code import CodeSearchQuery, CodeSearchService
from odoo_osi.search.modules import ModuleSearchQuery, ModuleSearchService

router = APIRouter(prefix="/search", tags=["search"])
SessionDep = Annotated[AsyncSession, Depends(get_session)]


class SearchRequest(BaseModel):
    query: str = Field(min_length=1)
    odoo_version: str | None = None
    license: str | None = None
    limit: int = Field(default=10, ge=1, le=50)


class SearchWarning(BaseModel):
    code: str
    message: str


class SearchResult(BaseModel):
    repository: str
    module: str
    odoo_version: str | None
    summary: str | None
    license: str | None
    dependencies: list[str]
    why_matched: list[str]
    confidence: float
    source_url: str | None
    warnings: list[SearchWarning] = []


class SearchResponse(BaseModel):
    query: str
    results: list[SearchResult]


class CodeSearchRequest(BaseModel):
    query: str = Field(min_length=1)
    odoo_version: str | None = None
    limit: int = Field(default=20, ge=1, le=100)


class CodeSearchResult(BaseModel):
    repository: str
    module: str
    odoo_version: str | None
    path: str
    symbol_type: str
    name: str | None
    odoo_model: str | None
    inherited_model: str | None
    xml_id: str | None
    parent_xml_id: str | None


class CodeSearchResponse(BaseModel):
    query: str
    results: list[CodeSearchResult]


@router.post("", response_model=SearchResponse)
async def search_modules(request: SearchRequest, session: SessionDep) -> SearchResponse:
    matches = await ModuleSearchService(session).search(
        ModuleSearchQuery(
            query=request.query,
            odoo_version=request.odoo_version,
            license=request.license,
            limit=request.limit,
        )
    )
    return SearchResponse(
        query=request.query,
        results=[
            SearchResult(
                repository=match.repository,
                module=match.module,
                odoo_version=match.odoo_version,
                summary=match.summary,
                license=match.license,
                dependencies=match.dependencies,
                why_matched=match.why_matched,
                confidence=match.confidence,
                source_url=match.source_url,
            )
            for match in matches
        ],
    )


@router.post("/code", response_model=CodeSearchResponse)
async def search_code(request: CodeSearchRequest, session: SessionDep) -> CodeSearchResponse:
    matches = await CodeSearchService(session).search(
        CodeSearchQuery(
            query=request.query,
            odoo_version=request.odoo_version,
            limit=request.limit,
        )
    )
    return CodeSearchResponse(
        query=request.query,
        results=[
            CodeSearchResult(
                repository=match.repository,
                module=match.module,
                odoo_version=match.odoo_version,
                path=match.path,
                symbol_type=match.symbol_type,
                name=match.name,
                odoo_model=match.odoo_model,
                inherited_model=match.inherited_model,
                xml_id=match.xml_id,
                parent_xml_id=match.parent_xml_id,
            )
            for match in matches
        ],
    )
