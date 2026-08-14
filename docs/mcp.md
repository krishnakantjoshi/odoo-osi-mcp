# Odoo Community MCP

The MCP server exposes the indexed Odoo OSI knowledge base to AI coding agents.

## Run With stdio

```bash
odoo-osi run-mcp
```

For this workspace:

```bash
.venv/bin/odoo-osi run-mcp
```

## Run With Streamable HTTP

```bash
odoo-osi run-mcp --transport streamable-http --host 127.0.0.1 --port 8765
```

## Tools

- `search_oca_modules`
- `find_solution`
- `search_oca_code`
- `get_oca_module`
- `get_module_dependencies`

## Smoke Test

Run a real stdio MCP client against the local server:

```bash
.venv/bin/odoo-osi mcp-smoke \
  --requirement "prevent negative inventory" \
  --odoo-version 18.0
```

Expected result: the tool list includes `find_solution`, and the returned candidates include `stock_no_negative` when that module has been indexed.

`find_solution` is version-aware. When a target Odoo version is provided, exact version
matches are ranked first, but strong candidates from other Odoo versions are still returned
with fields such as:

- `evidence_level`
- `version_status`
- `migration_effort`
- `migration_guidance`
- `indexing_guidance`
- `target_odoo_version`

For example, an Odoo 15 module that satisfies an Odoo 18 requirement can be returned as an
`older_version_migration_candidate` so an AI agent can use it as source evidence for a
migration or enhancement instead of starting from scratch.

`find_solution` is also index-first with a live GitHub/OCA fallback. If local indexed
results are missing or weak, it searches OCA module manifests on GitHub and returns likely
modules as `evidence_level=discovered_not_indexed`. These fallback results include
`indexing_guidance` and should be treated as discovery leads until the module is indexed for
source-backed evidence.

Users do not need to ask for fallback explicitly. A plain request such as:

```text
I need account reconcilation feature. I am using Odoo Community version 18.
```

should call `find_solution` with `odoo_version=18.0`. The service normalizes common Odoo
domain terms and misspellings, searches the local index first, and automatically falls back
to live GitHub/OCA discovery when indexed results are weak or missing.

Add `--full` to print the complete raw MCP tool response:

```bash
.venv/bin/odoo-osi mcp-smoke \
  --requirement "prevent negative inventory" \
  --odoo-version 18.0 \
  --full
```

## Client Configuration

Most MCP clients accept a stdio server configuration similar to this:

```json
{
  "mcpServers": {
    "odoo-community": {
      "command": "/Users/krishna/LiveWorkSpace/ocamcp/.venv/bin/odoo-osi",
      "args": ["run-mcp"],
      "cwd": "/Users/krishna/LiveWorkSpace/ocamcp"
    }
  }
}
```

Keep `.env` in the project directory so the MCP server can read the database URL and GitHub token.

The same example is available in [../mcp.json.example](../mcp.json.example).

## Test From Another AI Tool

Use stdio MCP for the first local test. The API server does not need to be running for stdio
MCP, but PostgreSQL must be running because the MCP server reads the indexed knowledge base.

1. Confirm local services are up:

```bash
docker compose up -d postgres redis
```

2. Confirm the MCP server works from this workspace:

```bash
.venv/bin/odoo-osi mcp-smoke \
  --requirement "prevent negative inventory" \
  --odoo-version 18.0
```

3. In the other AI tool's MCP settings, add this server:

```json
{
  "mcpServers": {
    "odoo-community": {
      "command": "/Users/krishna/LiveWorkSpace/ocamcp/.venv/bin/odoo-osi",
      "args": ["run-mcp"],
      "cwd": "/Users/krishna/LiveWorkSpace/ocamcp"
    }
  }
}
```

4. Restart or reload the AI tool.

5. Ask the AI tool:

```text
Use the odoo-community MCP server. For Odoo 18, check if there is an existing open-source
module for preventing negative inventory. Include exact-version matches and older-version
migration candidates.
```

Expected behavior: the tool should call `find_solution` and return `stock_no_negative`.
If Odoo 15 data is indexed, it should also show the 15.0 module as an
`older_version_migration_candidate`.

## Prompt

- `check_before_custom_development`

## Development Briefs

After MCP finds, partially finds, or does not find a module, use
[AI Development Brief Guide](./ai-development-brief-guide.md) to prepare the prompt package
for the coding AI.

## Example Tool Inputs

```json
{
  "requirement": "prevent negative inventory",
  "odoo_version": "18.0",
  "limit": 5
}
```

```json
{
  "repository": "stock-logistics-workflow",
  "module": "stock_no_negative",
  "owner": "OCA",
  "odoo_version": "18.0"
}
```
