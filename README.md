# Odoo Open Source Intelligence

Odoo Open Source Intelligence, or Odoo OSI, is an enterprise-grade platform for discovering, evaluating, comparing, and recommending open-source Odoo modules before teams write custom code.

The AI-facing interface is **Odoo Community MCP**, an MCP server that lets coding agents search and inspect indexed OCA and trusted open-source Odoo repositories.

## Current Build Stage

This repository now has the first working backend and MCP vertical slice:

- FastAPI API for health, repositories, modules, search, code search, and solution finding
- PostgreSQL schema and Alembic migration for repositories, branches, modules, dependencies, source files, and symbols
- GitHub/OCA ingestion for repositories, Odoo version branches, manifests, metadata, dependencies, and selected source files
- Odoo-aware Python, XML, CSV security, and README extraction
- requirement-to-module search with version, license, manifest, and indexed document signals
- source-backed recommendation evidence
- cross-version recommendation candidates with migration/backport guidance
- live GitHub/OCA fallback for likely modules that are not indexed yet
- MCP server with search, solution, code, module, and dependency tools
- persisted indexing job ledger surfaced through `/indexing/status`
- local PostgreSQL and Redis configuration
- linting and test coverage

## Local Development

```bash
cp .env.example .env
# edit .env and set ODOO_OSI_GITHUB_TOKEN to your own GitHub token
docker compose up -d postgres redis
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev,mcp]"
alembic upgrade head
uvicorn odoo_osi.api.app:create_app --factory --reload
```

The health endpoint is available at:

```text
GET /health
```

Key working endpoints:

```text
GET /repositories
GET /modules
POST /search
POST /search/code
POST /solutions/find
```

## Product Plan

See [DEVELOPMENT_PLAN.md](DEVELOPMENT_PLAN.md).

## Ingestion

See [docs/ingestion.md](docs/ingestion.md) for GitHub token setup and indexing commands.

## MCP

See [docs/mcp.md](docs/mcp.md) for the Odoo Community MCP server commands and tools.
