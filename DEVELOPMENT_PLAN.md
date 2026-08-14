# Odoo Open Source Intelligence - Development Plan

## 1. Product Definition

### Working Name

**Odoo Open Source Intelligence**  
Short name: **Odoo OSI**

### Technical Interface

**Odoo Community MCP**

### Product Goal

Build an enterprise-grade platform that helps Odoo developers, consultants, implementation teams, and AI coding agents discover, evaluate, compare, and use existing open-source Odoo modules before writing custom code.

The platform should answer:

> Before we build this custom Odoo feature, does the open-source ecosystem already provide a useful solution?

### Core Principle

Every recommendation must be traceable to source repositories, module manifests, source files, documentation, version branches, dependencies, and license metadata.

The system must never guess module licenses or compatibility.

## 2. Target Users

### Primary Users

- Odoo developers
- Odoo consultants
- Odoo implementation companies
- Internal enterprise Odoo teams
- AI coding agents

### Secondary Users

- Solution architects
- Technical project managers
- Compliance reviewers
- Open-source maintainers

## 3. Core Use Cases

### Requirement Discovery

User asks:

> I need a multi-level purchase approval flow in Odoo 18.

System returns relevant open-source modules, ranked by fit, version compatibility, dependencies, license, maintenance signal, and source evidence.

### Existing Solution Check

Before custom code is generated, an AI agent calls the MCP server to check whether OCA or another trusted open-source source already has a solution.

### Module Analysis

User asks:

> Explain what this module does and what models/views it modifies.

System analyzes manifests, README files, Python models, XML views, security files, controllers, wizards, reports, tests, and migrations.

### Code Pattern Search

User asks:

> Which modules extend sale.order?

System searches source code, XML inheritance, model definitions, and metadata.

### Module Comparison

User compares multiple modules for the same business requirement. System explains differences, dependencies, license implications, architecture, maturity, and recommendation.

### Implementation Recommendation

System recommends one of:

- Use existing module
- Use existing module plus light customization
- Combine multiple modules
- Configure standard Odoo
- Build custom module

## 4. Enterprise Product Scope

### Platform Capabilities

1. Repository ingestion
2. Module metadata extraction
3. Odoo-specific source understanding
4. Knowledge graph
5. Hybrid search
6. AI recommendation engine
7. MCP server
8. Web application
9. API layer
10. License and compliance layer
11. Version compatibility engine
12. Maintenance health scoring
13. Team workflows
14. Observability and auditability
15. Enterprise deployment

### Initial Source Scope

Start with:

- OCA GitHub organization
- OCA Apps Store repository as a catalog reference, not the source of truth
- OCA maintainer-tools

Later extend to:

- Other trusted open-source Odoo repositories
- Customer-approved private repositories
- Internal custom module repositories
- Odoo core references where licensing and access permit

## 5. System Architecture

```text
                    Public Git Sources
                  OCA + trusted repositories
                              |
                              v
                    Repository Ingestion
                 GitHub API + incremental sync
                              |
                              v
                      Odoo-Aware Parser
       manifests, README, Python, XML, JS, CSV, tests, migrations
                              |
                              v
                         Knowledge DB
    repositories, branches, modules, versions, dependencies, files, symbols
                              |
             +----------------+----------------+
             |                                 |
             v                                 v
      Full-Text Search                  Vector Search
             |                                 |
             +----------------+----------------+
                              |
                              v
                     Ranking + Reasoning
                              |
        +---------------------+----------------------+
        |                     |                      |
        v                     v                      v
   Web Application          REST API              MCP Server
        |                                            |
        v                                            v
 Human Odoo teams                          AI coding agents
```

## 6. Core Data Model

### Repository

- id
- provider
- owner
- name
- full_name
- url
- default_branch
- description
- stars
- forks
- open_issues
- license
- last_commit_sha
- last_commit_at
- last_indexed_at
- archived
- visibility

### Branch

- id
- repository_id
- name
- odoo_version
- commit_sha
- last_indexed_at
- is_odoo_version_branch

### Module

- id
- repository_id
- branch_id
- technical_name
- display_name
- summary
- description
- odoo_version
- module_version
- category
- license
- license_source
- author
- maintainers
- website
- path
- installable
- application
- auto_install
- source_url
- readme_path
- manifest_path
- last_commit_sha

### Dependency

- id
- module_id
- dependency_name
- dependency_type
- is_external
- source

### Source File

- id
- module_id
- path
- file_type
- language
- size
- sha
- content_hash
- indexed_at

### Symbol

- id
- module_id
- source_file_id
- symbol_type
- name
- odoo_model
- inherited_model
- xml_id
- parent_xml_id
- line_start
- line_end
- metadata

### Search Document

- id
- module_id
- source_file_id
- document_type
- title
- body
- metadata
- embedding
- tsvector

### Evaluation

- id
- team_id
- user_id
- requirement
- odoo_version
- recommended_module_ids
- decision
- notes
- created_at

## 7. Odoo-Aware Parsing

### Manifest Parser

Parse `__manifest__.py` as the authoritative source for:

- name
- summary
- description
- version
- license
- depends
- external_dependencies
- data
- demo
- assets
- installable
- application
- auto_install
- author
- website
- maintainers

### Python Parser

Extract:

- Odoo models
- `_name`
- `_inherit`
- `_inherits`
- fields
- compute methods
- constraints
- onchange methods
- actions
- controllers
- wizards
- reports
- service classes

### XML Parser

Extract:

- views
- inherited views
- `inherit_id`
- menus
- actions
- records
- templates
- reports
- security groups
- access rules
- data files

### CSV Parser

Extract:

- model access rules
- imported records
- security declarations

### README Parser

Extract section-based chunks:

- overview
- usage
- configuration
- known issues
- roadmap
- bug tracker
- credits
- maintainers

## 8. Search And Ranking

### Search Types

1. Exact search
   - module names
   - technical names
   - Odoo model names
   - XML ids
   - dependency names

2. Full-text search
   - manifests
   - README files
   - source code
   - XML views
   - security files

3. Semantic search
   - natural-language requirements
   - README sections
   - manifest descriptions
   - source-level chunks

### Ranking Factors

- Odoo version match
- semantic relevance
- exact technical match
- manifest relevance
- README relevance
- source evidence
- dependency fit
- license compatibility
- maintenance signal
- documentation quality
- test presence
- branch freshness
- repository activity

### Result Requirements

Every result must include:

- repository
- module
- Odoo version
- summary
- why it matched
- dependencies
- license
- license source
- source URL
- confidence
- warnings

## 9. License And Compliance

### Rules

- Module license comes from `__manifest__.py`.
- Repository license is supplemental only.
- If license is missing, mark as unknown.
- Do not infer compatibility silently.
- Always show source attribution.
- Always warn when AGPL or unclear license terms may matter.

### Compliance Output

For each module:

- license
- license source
- repository URL
- manifest URL
- attribution
- risk notes

## 10. MCP Server

### Tool Surface

#### `search_oca_modules`

Search modules by query, version, license, category, repository, or dependency.

#### `find_solution`

High-level requirement-to-recommendation tool.

#### `get_oca_module`

Return complete module metadata.

#### `get_module_dependencies`

Return direct and transitive dependency information.

#### `search_oca_code`

Search Odoo source patterns such as `_inherit = "sale.order"` or XML view inheritance.

#### `get_module_source`

Retrieve selected source files or file summaries.

#### `compare_modules`

Compare candidate modules for a requirement.

#### `get_repository_info`

Return repository-level metadata and health signals.

### Resources

Examples:

- `odoo-osi://repository/OCA/purchase-workflow`
- `odoo-osi://module/OCA/purchase-workflow/purchase_request/18.0`
- `odoo-osi://module/OCA/purchase-workflow/purchase_request/18.0/manifest`
- `odoo-osi://module/OCA/purchase-workflow/purchase_request/18.0/readme`
- `odoo-osi://module/OCA/purchase-workflow/purchase_request/18.0/source/models/purchase_request.py`

### Prompts

- `find_existing_open_source_solution`
- `analyze_odoo_module`
- `compare_odoo_modules`
- `plan_odoo_customization`
- `check_before_custom_development`

## 11. Web Application

### Main Areas

1. Global search
2. Module detail page
3. Repository detail page
4. Requirement analysis workspace
5. Module comparison workspace
6. Dependency graph
7. Source explorer
8. License and compliance view
9. Team evaluations
10. Admin/indexing dashboard

### Enterprise Features

- Login
- Organizations and teams
- Role-based access
- API keys
- Saved searches
- Saved evaluations
- Audit logs
- Indexing status
- Data freshness indicators
- Exportable reports

## 12. API

### Public Internal API

- `GET /repositories`
- `GET /repositories/{owner}/{name}`
- `GET /modules`
- `GET /modules/{id}`
- `GET /modules/{id}/dependencies`
- `GET /modules/{id}/source`
- `POST /search`
- `POST /solutions/find`
- `POST /modules/compare`
- `GET /indexing/jobs`

### Admin API

- trigger repository sync
- trigger branch sync
- re-index module
- inspect indexing errors
- manage source allowlist
- manage API keys

## 13. Technology Stack

### Backend

- Python
- FastAPI
- MCP Python SDK
- SQLAlchemy
- Alembic
- Pydantic
- Celery or Dramatiq for background jobs

### Database And Search

- PostgreSQL
- pgvector
- PostgreSQL full-text search
- Redis for queues/cache

### Frontend

- React or Next.js
- TypeScript
- Tailwind or a component system chosen during UI planning

### Infrastructure

- Docker
- Docker Compose for local development
- Kubernetes-ready containers later
- GitHub Actions
- OpenTelemetry
- Prometheus/Grafana or equivalent

### External Services

- GitHub API
- Embedding provider
- Optional hosted LLM provider for recommendations

## 14. Security

### V1 Security Boundary

The first production version is read-only:

- no pushing code
- no repository modification
- no Odoo database modification
- no module installation
- no PR creation

### Enterprise Security

- OAuth or SSO-ready auth
- role-based access control
- encrypted secrets
- API key rotation
- audit logs
- tenant isolation
- rate limiting
- request tracing
- dependency scanning
- container scanning

## 15. Development Milestones

### Milestone 0 - Project Foundation

Deliverables:

- repository initialized
- Python project structure
- backend service skeleton
- Docker Compose
- PostgreSQL and Redis
- initial CI
- linting and formatting
- architecture decision records
- environment configuration

Exit criteria:

- app boots locally
- tests run in CI
- database migrations run
- basic health endpoint works

### Milestone 1 - OCA Discovery Research

Deliverables:

- study OCA repository structure
- study OCA maintainer-tools
- study Apps Store generation flow
- document branch conventions
- document module discovery rules
- document manifest conventions
- document license conventions

Exit criteria:

- crawler rules are documented
- module detection is proven on at least 5 representative OCA repositories

### Milestone 2 - Repository Ingestion

Deliverables:

- GitHub API client
- repository discovery
- branch discovery
- Odoo version branch detection
- commit tracking
- incremental sync metadata
- indexing job framework

Exit criteria:

- system can discover OCA repositories and version branches
- sync state is persisted
- repeated syncs avoid unnecessary work

### Milestone 3 - Module Parser

Deliverables:

- module folder detection
- manifest parser
- README parser
- dependency extraction
- license extraction
- module metadata persistence
- parser error reporting

Exit criteria:

- modules are detected across representative repositories
- module-level licenses are extracted from manifests
- dependencies are stored accurately

### Milestone 4 - Source Understanding

Deliverables:

- Python parser
- XML parser
- CSV parser
- JS asset indexing
- Odoo model extraction
- view inheritance extraction
- symbol table
- source document chunking

Exit criteria:

- system can answer source-backed questions like "which modules extend sale.order?"
- extracted symbols link back to source files

### Milestone 5 - Search

Deliverables:

- exact search
- PostgreSQL full-text search
- embedding pipeline
- pgvector search
- hybrid ranking
- version-aware filtering
- license-aware filtering

Exit criteria:

- natural-language requirements return useful candidate modules
- exact model/source searches return source-backed matches
- search results include evidence

### Milestone 6 - Recommendation Engine

Deliverables:

- requirement analysis pipeline
- candidate ranking
- result explanations
- confidence scoring
- compatibility warnings
- license warnings
- compare modules logic

Exit criteria:

- system can recommend existing modules, partial-fit modules, or custom development
- recommendations are traceable to indexed evidence

### Milestone 7 - MCP Server

Deliverables:

- MCP server
- tools
- resources
- prompts
- local stdio transport
- HTTP transport
- agent integration documentation

Exit criteria:

- Claude/Cursor/compatible agents can search, inspect, and compare modules through MCP
- MCP responses include source links, licenses, and evidence

### Milestone 8 - Web Application

Deliverables:

- search UI
- module detail page
- repository detail page
- requirement analysis workspace
- comparison workspace
- dependency graph
- source explorer
- license view
- admin indexing dashboard

Exit criteria:

- human users can complete discovery, analysis, comparison, and evaluation workflows in the UI

### Milestone 9 - Enterprise Layer

Deliverables:

- authentication
- organizations
- teams
- roles
- API keys
- saved evaluations
- audit logs
- rate limiting
- observability
- backup strategy

Exit criteria:

- app is ready for controlled team usage
- operational and security events are observable

### Milestone 10 - Production Release

Deliverables:

- deployment guide
- Docker images
- CI/CD
- monitoring
- alerting
- seeded demo data
- public documentation
- versioned API docs
- MCP installation docs

Exit criteria:

- app can be deployed repeatably
- users can connect web UI and MCP clients
- indexing can run incrementally in production

## 16. Acceptance Test Suite

### Functional Tests

1. Requirement: "I need purchase requisitions in Odoo 18."
   - Expected: relevant purchase workflow modules are returned.

2. Requirement: "I need to prevent negative inventory."
   - Expected: relevant stock modules are returned.

3. Query: "Find modules that extend sale.order."
   - Expected: source-backed modules with `_inherit = "sale.order"` or related XML inheritance are returned.

4. Query: "Find Odoo 18 modules for product variants."
   - Expected: relevant Odoo 18 product variant modules are returned.

5. Query: "Compare purchase request and purchase approval options."
   - Expected: comparison includes dependencies, fit, license, and implementation notes.

6. Query: "Can I use this module in proprietary work?"
   - Expected: system shows license, source, and compliance warning without making unsupported legal claims.

### Non-Functional Tests

- indexing can resume after interruption
- repeated sync is incremental
- parser errors do not stop whole indexing jobs
- search results include evidence
- MCP responses remain bounded and structured
- API requests are authenticated where required
- audit logs capture enterprise actions

## 17. Development Order

Recommended execution order:

1. Project foundation
2. OCA discovery research
3. repository ingestion
4. manifest and README parsing
5. database schema
6. exact and full-text search
7. source understanding
8. vector search
9. recommendation engine
10. MCP server
11. web application
12. enterprise layer
13. production hardening

The reason for this order is simple: the data layer is the hardest and riskiest part. Once repository ingestion and module understanding are reliable, MCP and UI become product surfaces over trustworthy data.

## 18. Immediate Next Actions

### Current Build Status

Completed or substantially working:

1. Milestone 0 - project foundation, local services, app boot, migrations, linting, tests.
2. Milestone 1 - OCA discovery rules proven against representative repositories.
3. Milestone 2 - GitHub repository and branch discovery, version filtering, persisted sync state.
4. Milestone 3 - module detection, manifest parsing, dependency/license extraction, metadata persistence.
5. Milestone 4 - source understanding for Python, XML, CSV security, and README sections.
6. Milestone 5 - first search layer for modules, parsed source symbols, and indexed README/security documents.
7. Milestone 6 - first recommendation layer with confidence, license warnings, source evidence, cross-version migration/backport guidance, and live GitHub/OCA fallback for unindexed modules.
8. Milestone 7 - initial MCP server with stdio and HTTP transports, tools, prompt, docs, and smoke test.
9. Enterprise operations foundation - persisted indexing job ledger with status, counters, errors, and recent job visibility.

Still to build for the enterprise-grade target:

1. Broader source parsing: JS/assets, tests, migrations, controllers, reports, and source chunking.
2. True hybrid search: PostgreSQL full-text search, pgvector embeddings, ranking evaluation, and query diagnostics.
3. Comparison workflows: side-by-side module comparison, dependency graphing, compatibility reasoning, and implementation recommendation categories.
4. Web application: search, module detail, requirement workspace, comparison workspace, source explorer, and admin indexing dashboard.
5. Enterprise layer: auth, organizations, roles, API keys, saved evaluations, audit logs, rate limiting, and observability.
6. Production hardening: background indexing jobs, incremental sync, retries, monitoring, CI/CD, deployment docs, and seeded demo data.

### Next Execution Block

1. Expand ingestion coverage across the priority OCA repositories using the GitHub token in `.env`.
2. Replace simple token scoring with PostgreSQL full-text search and ranked evidence documents.
3. Add `compare_modules` to the API and MCP surface.
4. Start the web application with the requirement analysis workspace as the first screen.
5. Move indexing execution into background jobs with queue workers, retry policy, cancellation, and scheduling.
6. Add deeper migration analysis that compares manifests, dependencies, models, views, security rules, and tests across Odoo versions.
