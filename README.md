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

See [docs/mcp.md](docs/mcp.md) for the Odoo OSI MCP server commands and tools.

## Project Status And Notices

- This project is unofficial; see [NOTICE.md](NOTICE.md).
- Contributions are welcome; see [CONTRIBUTING.md](CONTRIBUTING.md).
- Security reporting and credential guidance are in [SECURITY.md](SECURITY.md).
- Privacy and hosted deployment notes are in [PRIVACY.md](PRIVACY.md).
