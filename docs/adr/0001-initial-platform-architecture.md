# ADR 0001: Initial Platform Architecture

## Status

Accepted

## Context

Odoo OSI needs to serve both human users and AI coding agents. The highest-risk part of the system is reliable understanding of the open-source Odoo ecosystem: repositories, version branches, modules, manifests, dependencies, source files, symbols, licenses, and maintenance signals.

## Decision

Use a Python backend with:

- FastAPI for the HTTP API
- MCP Python SDK for the AI-agent interface
- SQLAlchemy and Alembic for persistence
- PostgreSQL as the primary database
- PostgreSQL full-text search and pgvector for hybrid search
- Redis for background queue/cache support
- GitHub API for repository ingestion

The first production boundary is read-only. The platform may search, inspect, analyze, and recommend, but it must not modify repositories, create pull requests, install Odoo modules, or write into Odoo databases.

## Consequences

- The same indexed data can power the web app, REST API, and MCP server.
- Module-level license and version compatibility can be enforced consistently.
- The MCP layer remains thin and depends on trusted indexed evidence.
- Write-capable automation can be considered later as a separate security decision.

