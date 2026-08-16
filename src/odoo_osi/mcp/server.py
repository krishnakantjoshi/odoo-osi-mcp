from __future__ import annotations

from typing import Any

from odoo_osi.core.config import get_settings
from odoo_osi.db.session import AsyncSessionFactory
from odoo_osi.mcp.services import (
    find_solution_payload,
    get_coverage_report_payload,
    get_module_dependencies_payload,
    get_module_payload,
    search_code_payload,
    search_modules_payload,
)


def create_mcp_server() -> Any:
    """Create the Odoo OSI MCP server.

    The concrete MCP tool registration will be added after the search services are wired.
    Keeping this factory isolated lets the HTTP API and MCP transport evolve independently.
    """
    try:
        from mcp.server.mcpserver.server import MCPServer
    except ImportError as exc:  # pragma: no cover - depends on optional extra
        raise RuntimeError("Install the 'mcp' optional dependency to run the MCP server") from exc

    server = MCPServer(
        name="odoo-osi-mcp",
        title="Odoo OSI MCP",
        description=(
            "Unofficial search and inspection server for indexed OCA and "
            "open-source Odoo modules."
        ),
        version="0.1.0",
    )

    @server.tool(description="Search indexed OCA modules by requirement or keywords.")
    async def search_oca_modules(
        query: str,
        odoo_version: str | None = None,
        license: str | None = None,
        limit: int = 10,
    ) -> dict[str, Any]:
        async with AsyncSessionFactory() as session:
            return await search_modules_payload(
                session=session,
                query=query,
                odoo_version=odoo_version,
                license=license,
                limit=limit,
            )

    @server.tool(description="Find existing OCA modules that may satisfy an Odoo requirement.")
    async def find_solution(
        requirement: str,
        odoo_version: str | None = None,
        limit: int = 8,
    ) -> dict[str, Any]:
        async with AsyncSessionFactory() as session:
            return await find_solution_payload(
                session=session,
                requirement=requirement,
                odoo_version=odoo_version,
                limit=limit,
            )

    @server.tool(description="Search parsed Odoo source symbols such as models and XML views.")
    async def search_oca_code(
        query: str,
        odoo_version: str | None = None,
        limit: int = 20,
    ) -> dict[str, Any]:
        async with AsyncSessionFactory() as session:
            return await search_code_payload(
                session=session,
                query=query,
                odoo_version=odoo_version,
                limit=limit,
            )

    @server.tool(
        description="Inspect an indexed OCA module with metadata, dependencies, and symbols."
    )
    async def get_oca_module(
        repository: str,
        module: str,
        owner: str = "OCA",
        odoo_version: str | None = None,
    ) -> dict[str, Any]:
        async with AsyncSessionFactory() as session:
            return await get_module_payload(
                session=session,
                owner=owner,
                repository=repository,
                module=module,
                odoo_version=odoo_version,
            )

    @server.tool(description="Return direct dependencies for an indexed OCA module.")
    async def get_module_dependencies(
        repository: str,
        module: str,
        owner: str = "OCA",
        odoo_version: str | None = None,
    ) -> dict[str, Any]:
        async with AsyncSessionFactory() as session:
            return await get_module_dependencies_payload(
                session=session,
                owner=owner,
                repository=repository,
                module=module,
                odoo_version=odoo_version,
            )

    @server.tool(description="Report local OCA index coverage, evidence depth, and catalog gaps.")
    async def get_coverage_report(owner: str | None = None) -> dict[str, Any]:
        settings = get_settings()
        async with AsyncSessionFactory() as session:
            return await get_coverage_report_payload(
                session=session,
                owner=owner or settings.github_owner,
                catalog_module_estimate=settings.oca_apps_module_estimate,
            )

    @server.prompt(description="Check the indexed OCA ecosystem before custom Odoo development.")
    def check_before_custom_development(requirement: str, odoo_version: str = "18.0") -> str:
        return (
            "Before generating custom Odoo code, call find_solution with "
            f"requirement={requirement!r} and odoo_version={odoo_version!r}. "
            "Evaluate candidate licenses, dependencies, source evidence, and version compatibility."
        )

    return server
