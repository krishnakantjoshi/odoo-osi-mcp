import asyncio
import json
import sys

import typer

from odoo_osi.core.config import get_settings
from odoo_osi.db.session import AsyncSessionFactory
from odoo_osi.ingestion.discovery import DiscoveryOptions, OcaDiscoveryService
from odoo_osi.ingestion.github import GitHubClient
from odoo_osi.ingestion.jobs import IndexingJobRecorder
from odoo_osi.ingestion.persistence import IndexWriter
from odoo_osi.ingestion.source_indexer import SourceIndexer, SourceIndexOptions
from odoo_osi.mcp.server import create_mcp_server

app = typer.Typer(help="Odoo Open Source Intelligence command line tools.")


@app.command()
def settings() -> None:
    """Print the active runtime environment."""
    current_settings = get_settings()
    typer.echo(f"environment={current_settings.env}")


@app.command("run-mcp")
def run_mcp(
    transport: str = typer.Option(
        "stdio",
        help="MCP transport: stdio, sse, or streamable-http.",
    ),
    host: str = typer.Option("127.0.0.1", help="Host for HTTP transports."),
    port: int = typer.Option(8765, help="Port for HTTP transports."),
) -> None:
    """Run the Odoo Community MCP server."""
    if transport not in {"stdio", "sse", "streamable-http"}:
        raise typer.BadParameter("transport must be stdio, sse, or streamable-http")

    server = create_mcp_server()
    if transport == "stdio":
        server.run(transport="stdio")
    else:
        server.run(transport=transport, host=host, port=port)


@app.command("mcp-smoke")
def mcp_smoke(
    requirement: str = typer.Option(
        "prevent negative inventory",
        help="Requirement to send to the MCP find_solution tool.",
    ),
    odoo_version: str = typer.Option("18.0", help="Odoo version for the smoke test."),
    full: bool = typer.Option(False, help="Print the full MCP tool result payload."),
) -> None:
    """Spawn the MCP server over stdio and call it as a real MCP client."""
    asyncio.run(_mcp_smoke(requirement=requirement, odoo_version=odoo_version, full=full))


async def _mcp_smoke(requirement: str, odoo_version: str, full: bool) -> None:
    from mcp.client.session import ClientSession
    from mcp.client.stdio import StdioServerParameters, stdio_client

    server_parameters = StdioServerParameters(
        command=sys.argv[0],
        args=["run-mcp"],
    )

    async with stdio_client(server_parameters) as streams:
        async with ClientSession(*streams, read_timeout_seconds=30) as session:
            await session.initialize()
            tools_result = await session.list_tools()
            tool_names = [tool.name for tool in tools_result.tools]
            solution_result = await session.call_tool(
                "find_solution",
                {
                    "requirement": requirement,
                    "odoo_version": odoo_version,
                    "limit": 5,
                },
            )

    solution_payload = solution_result.model_dump(mode="json")
    if full:
        payload = {
            "tools": tool_names,
            "find_solution": solution_payload,
        }
    else:
        payload = _mcp_smoke_summary(
            tool_names=tool_names,
            requirement=requirement,
            odoo_version=odoo_version,
            solution_payload=solution_payload,
        )

    typer.echo(json.dumps(payload, indent=2, sort_keys=True))


def _mcp_smoke_summary(
    tool_names: list[str],
    requirement: str,
    odoo_version: str,
    solution_payload: dict,
) -> dict:
    candidates = _mcp_text_payload(solution_payload).get("candidates", [])
    top_candidates = []
    for candidate in candidates[:5]:
        evidence = candidate.get("evidence", {})
        top_candidates.append(
            {
                "module": candidate.get("module"),
                "repository": candidate.get("repository"),
                "confidence": candidate.get("confidence"),
                "evidence_level": candidate.get("evidence_level"),
                "odoo_version": candidate.get("odoo_version"),
                "target_odoo_version": candidate.get("target_odoo_version"),
                "version_status": candidate.get("version_status"),
                "migration_effort": candidate.get("migration_effort"),
                "migration_guidance": candidate.get("migration_guidance", [])[:2],
                "indexing_guidance": candidate.get("indexing_guidance", [])[:2],
                "indexed_source_files": evidence.get("indexed_source_files", 0),
                "indexed_symbols": evidence.get("indexed_symbols", 0),
                "indexed_search_documents": evidence.get("indexed_search_documents", 0),
                "readme_sections": evidence.get("readme_sections", 0),
                "security_access_rules": evidence.get("security_access_rules", 0),
                "odoo_models": evidence.get("odoo_models", [])[:3],
                "inherited_models": evidence.get("inherited_models", [])[:3],
                "readme_section_titles": evidence.get("readme_section_titles", [])[:3],
                "warnings": candidate.get("warnings", []),
            }
        )

    return {
        "tools": tool_names,
        "find_solution": {
            "requirement": requirement,
            "odoo_version": odoo_version,
            "candidate_count": len(candidates),
            "top_candidates": top_candidates,
        },
    }


def _mcp_text_payload(solution_payload: dict) -> dict:
    content = solution_payload.get("content", [])
    if not content:
        return {}

    first_content = content[0]
    if first_content.get("type") != "text":
        return {}

    try:
        return json.loads(first_content.get("text") or "{}")
    except json.JSONDecodeError:
        return {}


@app.command("discover-oca")
def discover_oca(
    owner: str = typer.Option(None, help="GitHub organization or owner to inspect."),
    repository: str | None = typer.Option(
        None,
        help="Only inspect this repository, for example purchase-workflow.",
    ),
    repo_limit: int | None = typer.Option(3, min=1, help="Maximum repositories to inspect."),
    branch_limit: int | None = typer.Option(1, min=1, help="Maximum version branches per repo."),
    module_limit: int | None = typer.Option(10, min=1, help="Maximum modules per branch."),
    odoo_version: str | None = typer.Option(None, help="Only inspect this Odoo version branch."),
    include_archived: bool = typer.Option(False, help="Include archived repositories."),
    skip_manifest_parse: bool = typer.Option(False, help="Only discover manifest paths."),
    persist: bool = typer.Option(False, help="Persist discovered records to the database."),
    summary: bool = typer.Option(False, help="Print only aggregate counts and module names."),
) -> None:
    """Discover OCA repositories, Odoo version branches, and module manifests."""
    asyncio.run(
        _discover_oca(
            owner=owner,
            repository=repository,
            repo_limit=repo_limit,
            branch_limit=branch_limit,
            module_limit=module_limit,
            odoo_version=odoo_version,
            include_archived=include_archived,
            skip_manifest_parse=skip_manifest_parse,
            persist=persist,
            summary=summary,
        )
    )


async def _discover_oca(
    owner: str | None,
    repository: str | None,
    repo_limit: int | None,
    branch_limit: int | None,
    module_limit: int | None,
    odoo_version: str | None,
    include_archived: bool,
    skip_manifest_parse: bool,
    persist: bool,
    summary: bool,
) -> None:
    settings = get_settings()
    client = GitHubClient(token=settings.github_token)
    service = OcaDiscoveryService(client)
    job_id = None

    try:
        options = DiscoveryOptions(
            owner=owner or settings.github_owner,
            repository=repository,
            repo_limit=repo_limit,
            branch_limit_per_repo=branch_limit,
            module_limit_per_branch=module_limit,
            odoo_version=odoo_version,
            include_archived=include_archived,
            parse_manifests=not skip_manifest_parse,
        )
        if persist:
            async with AsyncSessionFactory() as session:
                recorder = IndexingJobRecorder(session)
                job = await recorder.start(
                    "discover_oca",
                    owner=options.owner,
                    repository=repository,
                    odoo_version=odoo_version,
                    parameters={
                        "repo_limit": repo_limit,
                        "branch_limit_per_repo": branch_limit,
                        "module_limit_per_branch": module_limit,
                        "include_archived": include_archived,
                        "parse_manifests": not skip_manifest_parse,
                    },
                )
                job_id = job.id
                try:
                    report = await service.discover(options)
                    await IndexWriter(session).persist_report(report)
                    await recorder.succeed(
                        job,
                        counters={
                            "repositories_seen": report.repositories_seen,
                            "repositories_indexed": report.repositories_indexed,
                            "branches_indexed": report.branches_indexed,
                            "modules_seen": report.modules_seen,
                            "modules_parsed": report.modules_parsed,
                        },
                        errors=[error.__dict__ for error in report.errors],
                    )
                except Exception as exc:
                    await session.rollback()
                    await recorder.fail(job, error=str(exc))
                    raise
        else:
            report = await service.discover(options)
    finally:
        await client.close()

    payload = _discovery_payload(
        report=report,
        job_id=job_id,
        repository_filter=repository,
        odoo_version=odoo_version,
        persisted=persist,
        summary=summary,
    )
    typer.echo(json.dumps(payload, indent=2, sort_keys=True))


def _discovery_payload(
    report,
    job_id: int | None,
    repository_filter: str | None,
    odoo_version: str | None,
    persisted: bool,
    summary: bool,
) -> dict:
    payload = {
        "owner": report.owner,
        "repository_filter": repository_filter,
        "repositories_seen": report.repositories_seen,
        "repositories_indexed": report.repositories_indexed,
        "branches_indexed": report.branches_indexed,
        "modules_seen": report.modules_seen,
        "modules_parsed": report.modules_parsed,
        "odoo_version_filter": odoo_version,
        "persisted": persisted,
        "indexing_job_id": job_id,
        "errors": [error.__dict__ for error in report.errors],
    }

    if summary:
        payload["branches"] = [
            {
                "repository": branch.repository.full_name,
                "branch": branch.branch.name,
                "odoo_version": branch.odoo_version,
                "module_count": len(branch.modules),
                "modules": [module.technical_name for module in branch.modules],
            }
            for branch in report.branches
        ]
        return payload

    payload["branches"] = [
        {
            "repository": branch.repository.full_name,
            "branch": branch.branch.name,
            "odoo_version": branch.odoo_version,
            "module_count": len(branch.modules),
            "modules": [
                {
                    "technical_name": module.technical_name,
                    "path": module.path,
                    "manifest_path": module.manifest_path,
                    "name": module.manifest.name if module.manifest else None,
                    "version": module.manifest.version if module.manifest else None,
                    "license": module.manifest.license if module.manifest else None,
                    "depends": module.manifest.depends if module.manifest else [],
                    "parse_error": module.parse_error,
                }
                for module in branch.modules
            ],
        }
        for branch in report.branches
    ]
    return payload


@app.command("index-source")
def index_source(
    owner: str = typer.Option(None, help="GitHub organization or owner."),
    repository: str | None = typer.Option(
        None,
        help="Repository name, for example account-analytic.",
    ),
    module: str | None = typer.Option(
        None,
        help="Technical module name, for example purchase_request.",
    ),
    odoo_version: str | None = typer.Option(None, help="Only index modules for this Odoo version."),
    module_limit: int | None = typer.Option(5, min=1, help="Maximum modules to index."),
    file_limit: int = typer.Option(20, min=1, help="Maximum files to index per module."),
) -> None:
    """Index source files and Odoo symbols for modules already stored in the database."""
    asyncio.run(
        _index_source(
            owner=owner,
            repository=repository,
            module=module,
            odoo_version=odoo_version,
            module_limit=module_limit,
            file_limit=file_limit,
        )
    )


async def _index_source(
    owner: str | None,
    repository: str | None,
    module: str | None,
    odoo_version: str | None,
    module_limit: int | None,
    file_limit: int,
) -> None:
    settings = get_settings()
    client = GitHubClient(token=settings.github_token)
    job_id = None

    try:
        async with AsyncSessionFactory() as session:
            options = SourceIndexOptions(
                owner=owner or settings.github_owner,
                repository=repository,
                module=module,
                odoo_version=odoo_version,
                module_limit=module_limit,
                file_limit_per_module=file_limit,
            )
            recorder = IndexingJobRecorder(session)
            job = await recorder.start(
                "index_source",
                owner=options.owner,
                repository=repository,
                module=module,
                odoo_version=odoo_version,
                parameters={
                    "module_limit": module_limit,
                    "file_limit_per_module": file_limit,
                },
            )
            job_id = job.id
            try:
                report = await SourceIndexer(session, client).index(options)
                await recorder.succeed(
                    job,
                    counters={
                        "modules_seen": report.modules_seen,
                        "files_indexed": report.files_indexed,
                        "symbols_indexed": report.symbols_indexed,
                    },
                    errors=report.errors,
                )
            except Exception as exc:
                await session.rollback()
                await recorder.fail(job, error=str(exc))
                raise
    finally:
        await client.close()

    typer.echo(
        json.dumps(
            {
                "indexing_job_id": job_id,
                "modules_seen": report.modules_seen,
                "files_indexed": report.files_indexed,
                "symbols_indexed": report.symbols_indexed,
                "errors": report.errors,
            },
            indent=2,
            sort_keys=True,
        )
    )
