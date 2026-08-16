# Odoo Open Source Intelligence

Odoo Open Source Intelligence, or Odoo OSI, is an enterprise-grade platform for discovering, evaluating, comparing, and recommending open-source Odoo modules before teams write custom code.

The AI-facing interface is **Odoo OSI MCP**, an unofficial MCP server that lets coding
agents search and inspect indexed OCA and trusted open-source Odoo repositories.

Odoo OSI is not affiliated with, endorsed by, or sponsored by the Odoo Community
Association (OCA) or Odoo S.A. OCA and Odoo names are used only to identify public
open-source repositories and ecosystem references.

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

## Quick Start

Follow these steps to run Odoo OSI locally from a fresh clone.

### 1. Prerequisites

Install:

- Python 3.11 or newer
- Docker and Docker Compose
- Git
- A GitHub personal access token for practical indexing and fallback search

### 2. Clone The Repository

```bash
git clone https://github.com/krishnakantjoshi/odoo-osi-mcp.git
cd odoo-osi-mcp
```

### 3. Create Local Configuration

```bash
cp .env.example .env
```

Open `.env` and set your own GitHub token:

```bash
ODOO_OSI_GITHUB_TOKEN=YOUR_GITHUB_TOKEN
```

`.env` is ignored by git. Do not commit real tokens.

### 4. Start PostgreSQL And Redis

```bash
docker compose up -d postgres redis
```

### 5. Create A Python Environment

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev,mcp]"
```

On Windows PowerShell, activate the virtual environment with:

```powershell
.\.venv\Scripts\Activate.ps1
```

### 6. Run Database Migrations

```bash
alembic upgrade head
```

### 7. Start The API Server

```bash
uvicorn odoo_osi.api.app:create_app --factory --reload
```

Check the API:

```bash
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:8000/indexing/status
```

### 8. Discover And Index A Small Sample

In another terminal, activate the virtual environment again:

```bash
source .venv/bin/activate
```

Discover module manifests from one OCA repository:

```bash
odoo-osi discover-oca \
  --repository purchase-workflow \
  --odoo-version 18.0 \
  --branch-limit 1 \
  --module-limit 20 \
  --persist
```

Index source evidence for a small set of modules:

```bash
odoo-osi index-source \
  --repository purchase-workflow \
  --odoo-version 18.0 \
  --module-limit 10 \
  --file-limit 30
```

Check coverage:

```bash
odoo-osi coverage
curl http://127.0.0.1:8000/indexing/coverage
```

### 9. Search For Modules

```bash
curl -X POST http://127.0.0.1:8000/solutions/find \
  -H "Content-Type: application/json" \
  -d '{"requirement":"multi level purchase approval","odoo_version":"18.0","limit":5}'
```

### 10. Run The MCP Server

For a local MCP client, use stdio:

```bash
odoo-osi run-mcp
```

Most MCP clients use a config like this:

```json
{
  "mcpServers": {
    "odoo-osi": {
      "command": "/absolute/path/to/odoo-osi-mcp/.venv/bin/odoo-osi",
      "args": ["run-mcp"],
      "cwd": "/absolute/path/to/odoo-osi-mcp",
      "env": {
        "ODOO_OSI_GITHUB_TOKEN": "REPLACE_WITH_YOUR_OWN_GITHUB_TOKEN"
      }
    }
  }
}
```

The same example is in [mcp.json.example](mcp.json.example). If your MCP client does not support
`env`, put the token in your local `.env` instead.

### 11. Run Tests

```bash
python -m ruff check .
python -m pytest
```

## Troubleshooting

- **Database connection fails**: run `docker compose up -d postgres redis`, then rerun
  `alembic upgrade head`.
- **GitHub rate limits**: set `ODOO_OSI_GITHUB_TOKEN` in `.env`.
- **MCP client cannot find `odoo-osi`**: use the absolute path to `.venv/bin/odoo-osi` in your
  MCP config.
- **Search returns few results**: run discovery and source indexing first. A fresh database has
  no indexed modules.

## Local Credentials

There are two different GitHub credentials you may use:

- **GitHub personal access token**: used by Odoo OSI to call the GitHub API for indexing and
  fallback search.
- **SSH key**: used by git itself when you push or pull repositories over SSH.

### GitHub API Token

Create a fine-grained personal access token in GitHub:

1. Open GitHub.
2. Go to **Settings**.
3. Open **Developer settings**.
4. Open **Personal access tokens**.
5. Choose **Fine-grained tokens**.
6. Generate a new token.
7. Use the minimum access needed. For public OCA indexing, read-only public repository access is
   enough.

Put that token in your local `.env` file:

```bash
ODOO_OSI_GITHUB_TOKEN=YOUR_GITHUB_TOKEN
```

`.env` is ignored by git. If your MCP client uses a private `mcp.json`, that file is ignored too.
Do not put real tokens in `mcp.json.example`, docs, tests, or committed source.

GitHub docs:

- [Managing personal access tokens](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens)

### Git SSH Key

For git push/pull access over SSH, keep your SSH key outside the repo, usually in `~/.ssh`, and
add the public key to your Git hosting provider.

On macOS/Linux:

```bash
ssh-keygen -t ed25519 -C "your_email@example.com"
eval "$(ssh-agent -s)"
ssh-add ~/.ssh/id_ed25519
cat ~/.ssh/id_ed25519.pub
```

Copy the public key output and add it in GitHub under **Settings > SSH and GPG keys > New SSH key**.
Never copy or commit the private key file.

GitHub docs:

- [Generating a new SSH key and adding it to the ssh-agent](https://docs.github.com/en/authentication/connecting-to-github-with-ssh/generating-a-new-ssh-key-and-adding-it-to-the-ssh-agent)

## API Endpoints

The health endpoint:

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

## Roadmap

See [ROADMAP.md](ROADMAP.md).

## Ingestion

See [docs/ingestion.md](docs/ingestion.md) for GitHub token setup and indexing commands.

## MCP

See [docs/mcp.md](docs/mcp.md) for the Odoo OSI MCP server commands and tools.

## Project Status And Notices

- This project is unofficial; see [NOTICE.md](NOTICE.md).
- Contributions are welcome; see [CONTRIBUTING.md](CONTRIBUTING.md).
- Security reporting and credential guidance are in [SECURITY.md](SECURITY.md).
- Privacy and hosted deployment notes are in [PRIVACY.md](PRIVACY.md).
