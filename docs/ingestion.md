# Ingestion Notes

## GitHub Token

Each user should provide their own GitHub personal access token. Do not share a common token
across developers, MCP clients, or deployments.

Set `ODOO_OSI_GITHUB_TOKEN` for practical indexing runs. Unauthenticated GitHub API calls hit
rate limits quickly, especially during source-file indexing.

```bash
export ODOO_OSI_GITHUB_TOKEN=YOUR_GITHUB_TOKEN
```

The token only needs read access to public repositories for OCA indexing. Keep real tokens in
your local shell environment, your local `.env`, or your private MCP client settings. Never commit
real tokens to the repository.

## Discover Modules

Target a specific repository and Odoo version:

```bash
odoo-osi discover-oca \
  --repository purchase-workflow \
  --odoo-version 18.0 \
  --branch-limit 1 \
  --module-limit 20 \
  --persist
```

Dry-run without database writes:

```bash
odoo-osi discover-oca \
  --repository stock-logistics-workflow \
  --odoo-version 18.0 \
  --module-limit 10
```

## Index Source

After modules are persisted, index source files, parsed Odoo symbols, README sections, and
security access rules:

```bash
odoo-osi index-source \
  --repository purchase-workflow \
  --odoo-version 18.0 \
  --module-limit 10 \
  --file-limit 30
```

The source indexer currently extracts:

- Python Odoo models and inheritance signals
- XML records, views, actions, menus, and security records
- CSV access rules from `security/ir.model.access.csv`
- README sections from `.md` and `.rst` files

Persistent runs create an indexing job record. Check the latest counts and job status with:

```bash
curl http://127.0.0.1:8000/indexing/status
```

## Coverage Report

Use the coverage report to answer whether the local index covers the OCA ecosystem broadly
or only a targeted subset:

```bash
odoo-osi coverage
```

The API exposes the same report:

```bash
curl http://127.0.0.1:8000/indexing/coverage
```

The report separates:

- exact local indexed counts for repositories, version branches, modules, source files,
  symbols, and search documents
- evidence depth, including modules with indexed source, README evidence, and security rules
- the latest discovery and source-indexing job counters
- rough gap estimates against the latest full GitHub discovery job and the configured external
  module catalog estimate

Use `0` for discovery limits when intentionally running broad owner discovery:

```bash
odoo-osi discover-oca \
  --repo-limit 0 \
  --branch-limit 0 \
  --module-limit 0 \
  --persist
```

Large runs need a GitHub token and can take time. Treat `discovered_not_indexed` results as leads
until their source evidence is indexed.

## Useful API Endpoints

```text
GET  /indexing/status
GET  /indexing/coverage
GET  /repositories
GET  /repositories/OCA/purchase-workflow
GET  /modules?repository=purchase-workflow&odoo_version=18.0
GET  /modules/{id}
POST /search
POST /search/code
```
