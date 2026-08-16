# Contributing

Thanks for helping improve Odoo OSI.

## Local Setup

```bash
cp .env.example .env
# edit .env and set ODOO_OSI_GITHUB_TOKEN to your own GitHub token
docker compose up -d postgres redis
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev,mcp]"
alembic upgrade head
```

Run checks before opening a pull request:

```bash
python -m ruff check .
python -m pytest
```

## Guidelines

- Keep this project unofficial and avoid wording that implies OCA or Odoo S.A. endorsement.
- Do not commit real tokens, `.env` files, private databases, or customer code.
- Preserve source URLs, module license metadata, and attribution for indexed third-party modules.
- Do not vendor OCA module source code into this repository unless license obligations are reviewed.
- Keep new indexing behavior respectful of GitHub API rate limits.
