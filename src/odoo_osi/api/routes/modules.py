from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from odoo_osi.db.models import Dependency, Module, Repository, SourceFile, Symbol
from odoo_osi.db.session import get_session

router = APIRouter(prefix="/modules", tags=["modules"])
SessionDep = Annotated[AsyncSession, Depends(get_session)]


class DependencyResponse(BaseModel):
    dependency_name: str
    dependency_type: str
    is_external: bool
    source: str


class SourceFileResponse(BaseModel):
    path: str
    file_type: str
    language: str | None
    size: int
    sha: str | None
    content_hash: str | None


class SymbolResponse(BaseModel):
    path: str
    symbol_type: str
    name: str | None
    odoo_model: str | None
    inherited_model: str | None
    xml_id: str | None
    parent_xml_id: str | None
    line_start: int | None
    line_end: int | None


class ModuleListItem(BaseModel):
    id: int
    repository: str
    technical_name: str
    display_name: str | None
    summary: str | None
    odoo_version: str | None
    module_version: str | None
    license: str | None
    source_url: str | None


class ModuleListResponse(BaseModel):
    modules: list[ModuleListItem]


class ModuleDetailResponse(ModuleListItem):
    description: str | None
    category: str | None
    license_source: str | None
    author: str | None
    maintainers: list[str] | None
    website: str | None
    path: str
    manifest_path: str | None
    installable: bool
    application: bool
    auto_install: bool
    dependencies: list[DependencyResponse]
    source_files: list[SourceFileResponse]
    symbols: list[SymbolResponse]


@router.get("", response_model=ModuleListResponse)
async def list_modules(
    session: SessionDep,
    repository: str | None = None,
    odoo_version: str | None = None,
    license: str | None = None,
) -> ModuleListResponse:
    statement = (
        select(Module)
        .join(Repository, Repository.id == Module.repository_id)
        .options(selectinload(Module.repository))
        .order_by(Repository.full_name.asc(), Module.technical_name.asc())
    )
    if repository is not None:
        statement = statement.where(Repository.name == repository)
    if odoo_version is not None:
        statement = statement.where(Module.odoo_version == odoo_version)
    if license is not None:
        statement = statement.where(Module.license == license)

    result = await session.execute(statement)
    modules = result.scalars().all()
    return ModuleListResponse(modules=[_module_list_item(module) for module in modules])


@router.get("/{module_id}", response_model=ModuleDetailResponse)
async def get_module(module_id: int, session: SessionDep) -> ModuleDetailResponse:
    result = await session.execute(
        select(Module)
        .where(Module.id == module_id)
        .options(
            selectinload(Module.repository),
            selectinload(Module.dependencies),
            selectinload(Module.source_files).selectinload(SourceFile.symbols),
        )
    )
    module = result.scalar_one_or_none()
    if module is None:
        raise HTTPException(status_code=404, detail="Module not found")

    return ModuleDetailResponse(
        **_module_list_item(module).model_dump(),
        description=module.description,
        category=module.category,
        license_source=module.license_source,
        author=module.author,
        maintainers=module.maintainers,
        website=module.website,
        path=module.path,
        manifest_path=module.manifest_path,
        installable=module.installable,
        application=module.application,
        auto_install=module.auto_install,
        dependencies=[_dependency_response(dependency) for dependency in module.dependencies],
        source_files=[_source_file_response(source_file) for source_file in module.source_files],
        symbols=[
            _symbol_response(source_file, symbol)
            for source_file in module.source_files
            for symbol in source_file.symbols
        ],
    )


@router.get("/{module_id}/dependencies", response_model=list[DependencyResponse])
async def get_module_dependencies(
    module_id: int,
    session: SessionDep,
) -> list[DependencyResponse]:
    result = await session.execute(
        select(Module)
        .where(Module.id == module_id)
        .options(selectinload(Module.dependencies))
    )
    module = result.scalar_one_or_none()
    if module is None:
        raise HTTPException(status_code=404, detail="Module not found")

    return [_dependency_response(dependency) for dependency in module.dependencies]


def _module_list_item(module: Module) -> ModuleListItem:
    return ModuleListItem(
        id=module.id,
        repository=module.repository.full_name,
        technical_name=module.technical_name,
        display_name=module.display_name,
        summary=module.summary,
        odoo_version=module.odoo_version,
        module_version=module.module_version,
        license=module.license,
        source_url=module.source_url,
    )


def _dependency_response(dependency: Dependency) -> DependencyResponse:
    return DependencyResponse(
        dependency_name=dependency.dependency_name,
        dependency_type=dependency.dependency_type,
        is_external=dependency.is_external,
        source=dependency.source,
    )


def _source_file_response(source_file: SourceFile) -> SourceFileResponse:
    return SourceFileResponse(
        path=source_file.path,
        file_type=source_file.file_type,
        language=source_file.language,
        size=source_file.size,
        sha=source_file.sha,
        content_hash=source_file.content_hash,
    )


def _symbol_response(source_file: SourceFile, symbol: Symbol) -> SymbolResponse:
    return SymbolResponse(
        path=source_file.path,
        symbol_type=symbol.symbol_type,
        name=symbol.name,
        odoo_model=symbol.odoo_model,
        inherited_model=symbol.inherited_model,
        xml_id=symbol.xml_id,
        parent_xml_id=symbol.parent_xml_id,
        line_start=symbol.line_start,
        line_end=symbol.line_end,
    )
