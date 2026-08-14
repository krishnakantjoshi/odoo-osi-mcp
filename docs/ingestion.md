# Ingestion Notes

## GitHub Token

Set `ODOO_OSI_GITHUB_TOKEN` for practical indexing runs. Unauthenticated GitHub API calls hit rate limits quickly, especially during source-file indexing.

```bash
export ODOO_OSI_GITHUB_TOKEN=ghp_your_token
```

The token only needs read access to public repositories for OCA indexing.

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

## Useful API Endpoints

```text
GET  /indexing/status
GET  /repositories
GET  /repositories/OCA/purchase-workflow
GET  /modules?repository=purchase-workflow&odoo_version=18.0
GET  /modules/{id}
POST /search
POST /search/code
```
