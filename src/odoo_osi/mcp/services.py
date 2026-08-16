from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from odoo_osi.db.models import Module, Repository, SourceFile
from odoo_osi.search.code import CodeSearchQuery, CodeSearchService
from odoo_osi.search.coverage import coverage_report_payload
from odoo_osi.search.modules import ModuleSearchQuery, ModuleSearchService
from odoo_osi.search.solutions import SolutionService, solution_result_payload


async def search_modules_payload(
    session: AsyncSession,
    query: str,
    odoo_version: str | None = None,
    license: str | None = None,
    limit: int = 10,
) -> dict[str, Any]:
    matches = await ModuleSearchService(session).search(
        ModuleSearchQuery(
            query=query,
            odoo_version=odoo_version,
            license=license,
            limit=limit,
        )
    )
    return {
        "query": query,
        "results": [
            {
                "repository": match.repository,
                "module": match.module,
                "odoo_version": match.odoo_version,
                "summary": match.summary,
                "license": match.license,
                "dependencies": match.dependencies,
                "why_matched": match.why_matched,
                "confidence": match.confidence,
                "source_url": match.source_url,
                "warnings": _license_warnings(match.license),
            }
            for match in matches
        ],
    }


async def find_solution_payload(
    session: AsyncSession,
    requirement: str,
    odoo_version: str | None = None,
    limit: int = 8,
) -> dict[str, Any]:
    result = await SolutionService(session).find_solution(
        requirement=requirement,
        odoo_version=odoo_version,
        limit=limit,
    )
    return solution_result_payload(result)


async def search_code_payload(
    session: AsyncSession,
    query: str,
    odoo_version: str | None = None,
    limit: int = 20,
) -> dict[str, Any]:
    matches = await CodeSearchService(session).search(
        CodeSearchQuery(query=query, odoo_version=odoo_version, limit=limit)
    )
    return {
        "query": query,
        "results": [
            {
                "repository": match.repository,
                "module": match.module,
                "odoo_version": match.odoo_version,
                "path": match.path,
                "symbol_type": match.symbol_type,
                "name": match.name,
                "odoo_model": match.odoo_model,
                "inherited_model": match.inherited_model,
                "xml_id": match.xml_id,
                "parent_xml_id": match.parent_xml_id,
            }
            for match in matches
        ],
    }


async def get_module_payload(
    session: AsyncSession,
    repository: str,
    module: str,
    owner: str = "OCA",
    odoo_version: str | None = None,
) -> dict[str, Any]:
    statement = (
        select(Module)
        .join(Repository, Repository.id == Module.repository_id)
        .where(
            Repository.owner == owner,
            Repository.name == repository,
            Module.technical_name == module,
        )
        .options(
            selectinload(Module.repository),
            selectinload(Module.dependencies),
            selectinload(Module.source_files).selectinload(SourceFile.symbols),
        )
    )
    if odoo_version is not None:
        statement = statement.where(Module.odoo_version == odoo_version)

    result = await session.execute(statement)
    indexed_module = result.scalar_one_or_none()
    if indexed_module is None:
        return {
            "found": False,
            "owner": owner,
            "repository": repository,
            "module": module,
            "odoo_version": odoo_version,
        }

    return {
        "found": True,
        "repository": indexed_module.repository.full_name,
        "module": indexed_module.technical_name,
        "display_name": indexed_module.display_name,
        "summary": indexed_module.summary,
        "description": indexed_module.description,
        "odoo_version": indexed_module.odoo_version,
        "module_version": indexed_module.module_version,
        "license": indexed_module.license,
        "license_source": indexed_module.license_source,
        "dependencies": _dependencies_payload(indexed_module),
        "source_url": indexed_module.source_url,
        "manifest_path": indexed_module.manifest_path,
        "source_files": [
            {
                "path": source_file.path,
                "file_type": source_file.file_type,
                "language": source_file.language,
                "symbol_count": len(source_file.symbols),
            }
            for source_file in indexed_module.source_files
        ],
        "symbols": [
            {
                "path": source_file.path,
                "symbol_type": symbol.symbol_type,
                "name": symbol.name,
                "odoo_model": symbol.odoo_model,
                "inherited_model": symbol.inherited_model,
                "xml_id": symbol.xml_id,
                "parent_xml_id": symbol.parent_xml_id,
            }
            for source_file in indexed_module.source_files
            for symbol in source_file.symbols
        ],
        "warnings": _license_warnings(indexed_module.license),
    }


async def get_module_dependencies_payload(
    session: AsyncSession,
    repository: str,
    module: str,
    owner: str = "OCA",
    odoo_version: str | None = None,
) -> dict[str, Any]:
    module_payload = await get_module_payload(
        session=session,
        owner=owner,
        repository=repository,
        module=module,
        odoo_version=odoo_version,
    )
    if not module_payload["found"]:
        return module_payload
    return {
        "found": True,
        "repository": module_payload["repository"],
        "module": module_payload["module"],
        "odoo_version": module_payload["odoo_version"],
        "dependencies": module_payload["dependencies"],
    }


async def get_coverage_report_payload(
    session: AsyncSession,
    owner: str = "OCA",
    catalog_module_estimate: int | None = 20000,
) -> dict[str, Any]:
    return await coverage_report_payload(
        session=session,
        owner=owner,
        catalog_module_estimate=catalog_module_estimate,
    )


def _dependencies_payload(module: Module) -> list[dict[str, Any]]:
    return [
        {
            "dependency_name": dependency.dependency_name,
            "dependency_type": dependency.dependency_type,
            "is_external": dependency.is_external,
            "source": dependency.source,
        }
        for dependency in module.dependencies
    ]


def _license_warnings(license_name: str | None) -> list[str]:
    if license_name is None:
        return ["Module license is missing; inspect __manifest__.py before use."]
    if "AGPL" in license_name.upper():
        return [
            "AGPL module: review obligations before proprietary redistribution or modification."
        ]
    return []
