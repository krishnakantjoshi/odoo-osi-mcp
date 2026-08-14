You can keep it appreciative and frame MCP as an idea for the future, rather than suggesting that OCA should build it.

Something like:

This is really amazing work by the OCA community. Congratulations to everyone involved in building and maintaining such a valuable open-source ecosystem. 👏

One thought for the future: I wonder if an MCP server for the OCA Apps Store could take this even further.

Imagine an AI coding agent being able to understand a requirement, discover relevant OCA modules, inspect their capabilities, and directly use or recommend the appropriate open-source modules while developing a solution.

It could significantly reduce reinventing the wheel, accelerate implementation, and make the incredible work of the OCA community even more accessible to developers and consultants.

Just a thought — but I think the combination of OCA + open source + MCP + AI-assisted development could be extremely powerful. 🚀

Congratulations again on this initiative!

Also OCA has its Git Repo.. Can we check that too? so Instead of asking him we can build it on our own

Yes. In fact, I think we should investigate this ourselves before asking OCA for anything.

I checked the OCA GitHub organization. It is public and currently exposes 260 repositories, covering the OCA ecosystem. The OCA/apps-store repository itself exists and is essentially the repository behind the Apps Store catalog; its README says the catalog is generated using OCA tooling.

More importantly, the individual OCA repositories contain the actual module source code and metadata. For example, OCA/web contains web-client addons, while OCA/helpdesk exposes individual modules with versions and descriptions.

So I would change our idea

Instead of:

"Ask OCA to build an MCP server."

We can investigate building:

An OCA MCP Server / Odoo Community MCP

that indexes the public OCA repositories and makes them AI-searchable.

The architecture could be:

                 OCA GitHub
                     │
         ┌───────────┴───────────┐
         │                       │
    260+ repositories       apps-store
         │                       │
         └───────────┬───────────┘
                     ↓
              Indexer / Crawler
                     ↓
             Module Knowledge DB
                     ↓
             MCP Server
                     ↓
       ┌─────────────┼─────────────┐
       ↓             ↓             ↓
    Claude        Cursor        ChatGPT/
    /Agents       /VS Code      AI Agents
                     │
                     ↓
               Odoo Developer

And the MCP could expose tools such as:

search_oca_modules

"Find OCA modules for advanced purchase approval."

Returns:

repository
module
Odoo version
description
dependencies
license
GitHub URL
installation information
inspect_oca_module

"Explain sale_order_type and tell me what models/views it modifies."

The MCP can inspect the actual source.

find_oca_modules_for_requirement

This is the interesting one.

Developer says:

"I need a customer portal where customers can see their invoices and download documents."

MCP searches OCA repositories and returns relevant modules.

find_existing_solution

This could explicitly tell the AI:

Before writing custom code, check OCA.

That could be extremely useful for Odoo developers.

And we can go further

The MCP shouldn't only search module names/descriptions.

We can index:

README

__manifest__.py

Python

XML

JS

models

views

dependencies

version

license

issues/PR information

Then the AI can answer questions like:

"Is there an OCA module that adds approval workflows to purchase orders?"

or:

"Which OCA modules modify sale.order?"

or even:

"I'm implementing Odoo 18 manufacturing. Before writing anything, find existing OCA modules that address subcontracting, quality control and production reporting."

That is much more powerful than simply making the Apps Store searchable.

One important issue

We need to be careful with licenses.

The OCA GitHub organization is open source, but individual repositories/modules can have different licenses. The apps-store repository itself is AGPL-3.0, and its README explicitly says individual modules can have different licenses and that the module's __manifest__.py is authoritative.

So our MCP should always expose the module license and ideally warn the AI:

"Check the module's license before incorporating, modifying, redistributing or combining it with proprietary code."

That's important if we eventually use this commercially.

I think this is actually a good project for you

And it aligns very well with the Odoo/AI work you've already been exploring.

I would not start by building a huge MCP server.

I'd build V1 like this:

V1

Input:

Natural-language requirement

Engine:

OCA GitHub crawler → module metadata + source indexing → vector/full-text search

Output:

Requirement
     ↓
AI
     ↓
OCA MCP
     ↓
Relevant repositories
     ↓
Relevant modules
     ↓
Source inspection
     ↓
Dependencies
     ↓
License
     ↓
Recommendation

Then V2 could allow an AI coding agent to retrieve the actual module source and use it as development context.

And V3 could potentially understand:

"Install/use this existing OCA module and customize only the missing 20%."

That is where this becomes genuinely valuable.

I would call the concept something like:

OCA MCP

or

Odoo Community MCP

or, if you want it independent of OCA branding:

Odoo Open Source MCP

The third option is probably safer from a branding/organizational standpoint if we're building it independently.

And yes — I think we should first inspect the OCA GitHub structure and repositories programmatically, determine how modules are organized across Odoo versions, and design the indexer around that structure. We don't need OCA's permission just to build a tool that consumes publicly available repositories, although we would need to respect GitHub/OCA terms, licenses, attribution, rate limits, and any applicable API requirements.

OCA GitHub Organization

OCA Apps Store Repository

OCA MCP

DO the research and lets plan this development of MCP server

Yes. I did the research, and I think OCA MCP is a genuinely useful project, not just an interesting experiment.

The key is that we should not build an "OCA Apps Store search API." We should build an MCP server that lets an AI agent reason over the actual OCA ecosystem: repositories → versions → modules → manifests → dependencies → source code → documentation → maintenance signals.

1. What I found

The OCA GitHub organization is much larger than just the Apps Store. GitHub currently shows about 260 public repositories, including repositories such as web, storage, rest-framework, field-service, product-variant, maintainer-tools, oca-github-bot, OCB, etc.

The Apps Store repository is particularly interesting because it is generated from OCA repositories. Its README explicitly says that its contents are replaced by the oca-gen-addons-table script from OCA/maintainer-tools.

That means:

We should treat GitHub as the source of truth, not scrape the Apps Store.

The Apps Store is essentially a catalog/view over the ecosystem.

Also, OCA repositories are versioned. For example, OCA/product-variant currently exposes Odoo 18 module versions such as 18.0.1.0.0, etc.

And there's an important licensing point: the repository license does not necessarily tell us the license of every module. OCA explicitly says the individual module's __manifest__.py contains the authoritative license value.

That's something our MCP should expose prominently.

2. What OCA MCP should actually do

Imagine you're using Claude Code/Cursor/another coding agent while developing Odoo.

You say:

"I need a purchase approval workflow in Odoo 18."

Instead of the AI immediately writing custom code:

AI
 ↓
OCA MCP
 ↓
Search OCA ecosystem
 ↓
Find relevant repositories
 ↓
Find relevant modules
 ↓
Inspect manifests
 ↓
Inspect dependencies
 ↓
Inspect source
 ↓
Compare alternatives
 ↓
Return recommendation

The AI could answer:

I found three OCA modules that appear relevant.

Module A

Odoo 18
Repository: purchase-workflow
License: AGPL-3
Dependencies: purchase
Adds configurable approval workflow

Module B

Odoo 18
Repository: ...

I recommend A because...

That is the product.

3. The fundamental principle

I would put this instruction at the heart of OCA MCP:

Before generating custom Odoo code, search the OCA ecosystem for an existing solution.

This is potentially extremely valuable for:

Odoo developers
Odoo implementation companies
AI coding agents
Odoo consultants
internal Odoo teams
system integrators
4. Architecture I recommend

Don't make the MCP server itself responsible for crawling GitHub on every request.

Instead:

                 OCA GitHub
                     │
                     ▼
              ┌──────────────┐
              │ OCA Crawler  │
              └──────┬───────┘
                     │
                     ▼
              ┌──────────────┐
              │   Parser     │
              │              │
              │ Manifest     │
              │ README       │
              │ Python       │
              │ XML          │
              │ JS           │
              │ CSV          │
              └──────┬───────┘
                     │
                     ▼
              ┌──────────────┐
              │ Index / DB   │
              └──────┬───────┘
                     │
            ┌────────┴────────┐
            │                 │
            ▼                 ▼
      Keyword Search     Semantic Search
            │                 │
            └────────┬────────┘
                     ▼
                OCA MCP
                     │
       ┌─────────────┼─────────────┐
       ▼             ▼             ▼
    Claude          Cursor       AI Agent

This separation is important.

5. We should NOT initially clone all 260 repositories

This is one place where I'd deliberately keep V1 small.

First, discover:

Repository metadata
repository
name
description
default branch
available Odoo branches
license
stars
forks
last commit
open issues
contributors

Then identify Odoo versions.

For example:

OCA/product-variant

18.0
17.0
16.0
15.0
...

Then index modules.

6. Module-level data model

I'd create something like:

OCAModule

id
technical_name
repository
repository_url

odoo_version

name
summary
description

author
maintainers

license

category

depends[]
external_dependencies[]

installable
application

version

website

readme

path

last_commit

stars
forks

source_url

Then a separate table:

OCAModuleDependency

module_id
dependency_name
dependency_type

And:

OCARepository

name
url
description

branches[]
license

last_commit

stars
forks

open_issues
7. But the really interesting part is source-code indexing

Don't stop at the manifest.

Suppose we have:

purchase_request

The AI should be able to understand:

Models
purchase.request
purchase.request.line
Views
purchase_request_views.xml
purchase_request_line_views.xml
Security
ir.model.access.csv
security.xml
Dependencies
purchase
stock
mail
Python classes

etc.

Then the AI can answer:

"Which OCA modules extend purchase.order?"

That is far more powerful than traditional app-store search.

8. Search should be hybrid

I wouldn't use vector search alone.

We need three layers.

Layer 1 — Exact search

For:

purchase.order
sale.order
stock.move
res.partner

and technical module names.

Layer 2 — Full-text search

Search:

README
manifest description
source
XML
documentation
Layer 3 — Semantic search

This handles:

"I need a mechanism to prevent negative inventory."

Even if the module description doesn't literally contain those words.

So:

Query
 ↓
Exact search
 +
Full-text
 +
Semantic
 ↓
Ranking
9. Ranking will be extremely important

Suppose the MCP finds 25 modules.

We shouldn't dump all 25 into the LLM.

Rank them.

Something like:

Score =
    Odoo version match
  + semantic relevance
  + manifest relevance
  + dependency compatibility
  + maintenance activity
  + documentation quality
  + community signals

For example:

Odoo 18 exact match

should score significantly higher than:

Odoo 16 module

even if the semantic similarity is higher.

10. The MCP tools

For V1, I would expose only around 6–8 tools.

search_oca_modules

Input:

query
odoo_version
category
license
limit

Example:

Find Odoo 18 modules for purchase approvals.

get_oca_module

Input:

repository
module
odoo_version

Returns complete metadata.

get_module_source

Input:

repository
module
path

Returns source.

get_module_dependencies

Input:

repository
module
odoo_version

Returns dependency tree.

search_oca_code

Example:

Find OCA modules that inherit sale.order.

This could search:

_inherit = "sale.order"

and:

inherit_id="sale.view_order_form"

etc.

This is very valuable to developers.

find_solution

This is the high-level AI tool.

Input:

"I need multi-level purchase approval in Odoo 18."

It performs the search/ranking process internally.

Returns:

Best candidates
Why they match
Dependencies
License
Version
Repository
Confidence
compare_modules

Example:

Compare these three OCA modules.

get_repository_info

Useful for repository-level questions.

11. MCP Resources

The current MCP specification supports Tools, Resources and Prompts as separate primitives. Tools are model-controlled, resources provide contextual data, and prompts provide reusable interaction patterns.

We should use all three.

Resources

Something like:

oca://repository/purchase-workflow
oca://module/purchase_request/18.0
oca://module/purchase_request/18.0/manifest
oca://module/purchase_request/18.0/readme
oca://module/purchase_request/18.0/source/models/purchase_request.py

This gives AI agents precise access to information.

12. MCP Prompts

We can eventually provide prompts like:

find_existing_oca_solution

Before developing a custom Odoo module, search the OCA ecosystem and determine whether an existing module can satisfy the requirement.

analyze_oca_module

Analyze this OCA module and explain its architecture, dependencies, models, views and extension points.

plan_customization

Determine whether the requirement can be fulfilled by configuration, an OCA module, or custom development.

That last one is particularly interesting.

13. The killer feature: "Don't reinvent the wheel"

I think this should become the identity of OCA MCP.

The AI receives:

"Create a custom module for X."

Before generating code:

┌──────────────────────────┐
│ Is there an OCA solution?│
└────────────┬─────────────┘
             │
       ┌─────┴─────┐
       │           │
      YES          NO
       │           │
       ▼           ▼
 Recommend       Proceed to
 existing        custom design
 module

And perhaps:

OCA MCP found a 92% match. Do not create a new module until this module has been evaluated.

That's a meaningful AI-development workflow.

14. GitHub ingestion

We should use GitHub's APIs rather than scraping HTML.

The OCA organization is public and has a large repository set.

Crawler flow:

GitHub API
     ↓
List OCA repositories
     ↓
Filter relevant repositories
     ↓
Get branches
     ↓
Find Odoo version branches
     ↓
Get tree
     ↓
Identify modules
     ↓
Read __manifest__.py
     ↓
Read README
     ↓
Index source

We should also track commits.

That gives us:

last indexed commit SHA

Then future synchronization becomes incremental.

Instead of re-indexing everything:

Current SHA
      ↓
GitHub
      ↓
New commits?
      ↓
NO → nothing
YES
      ↓
Index changed files only
15. OCA's own tooling gives us a useful clue

The Apps Store README specifically points to:

OCA/maintainer-tools

and the oca-gen-addons-table process.

That means we should study the OCA maintainer tooling before implementing our repository/module discovery logic.

We shouldn't duplicate OCA's understanding of its own repository structure unnecessarily.

16. Technology stack

Given your environment and Odoo background, I'd use:

Backend

Python

MCP

Official MCP Python SDK

The current Python SDK is now on the 2.x stable line, supports Python 3.10+, and supports stdio, Streamable HTTP and SSE.

The latest MCP specification is 2026-07-28. It introduced a stateless protocol core and recommends Streamable HTTP for modern server deployments.

So I'd build against:

MCP 2026-07-28

and the current Python SDK.

API

FastAPI/Starlette underneath if needed.

But don't over-engineer the first version.

Database

For V1:

PostgreSQL

because eventually we'll need:

repositories
modules
versions
dependencies
files
symbols
indexing metadata
commits
Search

I'd start with:

PostgreSQL + pgvector

rather than immediately introducing Elasticsearch/OpenSearch.

This keeps the architecture simple.

Later, if scale requires it:

PostgreSQL
+
OpenSearch
Embeddings

We can initially use an embedding model to index:

module descriptions
README
source chunks
model definitions
XML views

But I'd avoid embedding every source line blindly.

We'll design the chunking carefully.

17. Source-code chunking

This is where an Odoo-specific MCP can become much better than generic GitHub search.

Don't create:

chunk = every 500 tokens

Instead understand Odoo.

For Python:

class
method
Odoo model
inherit
fields

For XML:

record
view
template
menu
action
security

For manifests:

manifest as one document

For README:

section-based chunks

Then metadata accompanies every chunk:

repository
module
odoo_version
file
language
model
inherit
license

Now semantic search becomes much more useful.

18. Security

This MCP will mostly be read-only.

That's good.

V1 should have:

NO
pushing code
creating PRs
modifying repositories
installing modules
writing to Odoo

Only:

READ
search
inspect
analyze
retrieve

The MCP specification emphasizes user consent and control around data access and operations.

So keeping V1 read-only substantially reduces the security surface.

19. Licensing

This deserves a dedicated component.

Every result should show:

License: AGPL-3.0
Source: OCA/purchase-workflow

and ideally:

License source:
__manifest__.py

Because OCA explicitly says the individual module manifest is authoritative for the module license.

We should never have the AI guess a license.

20. Version compatibility

This should be a first-class feature.

User:

"I am developing for Odoo 18."

MCP should prioritize:

18.0

Then perhaps show:

17.0
16.0

as alternatives.

It should never casually recommend a 16.0 module as if it were an Odoo 18 solution.

21. Maintenance score

I would add:

OCA Health Score

For example:

Repository activity
Recent commits
Open issues
Recent releases
Number of contributors
Branch availability
Odoo version
CI status

Not an official OCA score — our own technical signal.

Example:

Maintenance signal: High

rather than pretending we know whether the module is "safe."

22. What V1 should look like

Don't build everything.

V1 objective:

Given an Odoo requirement, find relevant OCA modules and explain why they are relevant.

That's it.

V1 components:

GitHub crawler
       ↓
OCA repository discovery
       ↓
Module parser
       ↓
PostgreSQL
       ↓
Full text search
       ↓
Semantic search
       ↓
MCP server
       ↓
Claude/Cursor
23. V1 acceptance test

We should define tests before coding.

For example:

Test 1

"I need purchase requisitions in Odoo 18."

Expected:

Find relevant purchase-workflow modules.

Test 2

"I need to prevent negative stock."

Expected:

Find relevant stock modules.

Test 3

"Find modules that extend sale.order."

Expected:

Return modules whose source actually inherits/extends sale.order.

Test 4

"Find OCA modules compatible with Odoo 18 for product variants."

Expected:

Relevant Odoo 18 modules from product-variant.

Test 5

"Does OCA have a module for X?"

Expected:

Search across repositories, not just the Apps Store catalog.

24. V2

Once V1 works:

Code understanding

The AI can inspect:

models
views
security
controllers
wizards
JS
dependencies

Then answer:

"How would I extend this module?"

25. V3

This is where it gets really interesting.

AI-assisted implementation

User:

"I need a three-level purchase approval."

MCP:

OCA search
    ↓
find purchase approval modules
    ↓
inspect source
    ↓
compare
    ↓
recommend

Then the coding agent can say:

"Use module X as the base. It already provides 70% of the requirement. I'll customize the remaining functionality."

Now OCA MCP becomes an AI development accelerator, rather than simply a search engine.

26. V4 — Odoo-aware coding agent

Eventually:

Requirement
     ↓
OCA MCP
     ↓
Existing OCA modules
     ↓
Odoo core
     ↓
Customer custom modules
     ↓
Architecture decision
     ↓
Implementation

That would be very powerful for your own Odoo implementation work.

27. One thing I would NOT do

I wouldn't call it:

OCA Official MCP

unless OCA itself endorses it.

I'd call the project:

OCA MCP

with a clear statement:

"An independent open-source MCP server for discovering and understanding OCA modules."

If we eventually build something genuinely useful, then approach OCA.

That is actually a much stronger conversation:

"We built this, it indexes the public OCA ecosystem, here is the GitHub repository, here are the tools, and we'd like to discuss whether OCA wants to collaborate."

Much better than approaching them with only an idea.

28. Development roadmap

I'd break this into 6 milestones.

Milestone 1 — Discovery
 Study OCA repository structure
 Study maintainer-tools
 Understand oca-gen-addons-table
 Identify Odoo version branch conventions
 Identify module detection rules
 Identify manifest fields
 Study OCA licensing conventions
Milestone 2 — Indexer
 GitHub repository crawler
 Branch discovery
 Module discovery
 Manifest parser
 README parser
 Dependency extraction
 License extraction
 Commit tracking
Milestone 3 — Search engine
 PostgreSQL
 Full-text search
 pgvector
 Embedding pipeline
 Hybrid ranking
 Version filtering
 Dependency filtering
Milestone 4 — MCP
 MCP server
 search_oca_modules
 get_oca_module
 search_oca_code
 get_module_source
 get_module_dependencies
 find_solution
 Resources
 Prompts
Milestone 5 — AI testing

Test with:

Claude
Cursor
Claude Code
other MCP-compatible agents
Milestone 6 — Public release
GitHub repository
documentation
Docker
hosted MCP endpoint
authentication if required
CI/CD
incremental synchronization
monitoring
29. My recommended initial architecture
                    ┌──────────────────┐
                    │   OCA GitHub     │
                    │   260+ repos     │
                    └────────┬─────────┘
                             │
                         GitHub API
                             │
                             ▼
                    ┌──────────────────┐
                    │  OCA Indexer     │
                    │                  │
                    │ repo discovery   │
                    │ branch discovery │
                    │ module parser    │
                    │ manifest parser  │
                    │ source parser    │
                    └────────┬─────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │   PostgreSQL     │
                    │                  │
                    │ metadata         │
                    │ dependencies     │
                    │ files            │
                    │ symbols          │
                    │ embeddings       │
                    └────────┬─────────┘
                             │
                  ┌──────────┴──────────┐
                  ▼                     ▼
           Full Text Search       Vector Search
                  │                     │
                  └──────────┬──────────┘
                             ▼
                    ┌──────────────────┐
                    │    OCA MCP       │
                    │                  │
                    │ Tools             │
                    │ Resources         │
                    │ Prompts           │
                    └────────┬─────────┘
                             │
              ┌──────────────┼──────────────┐
              ▼              ▼              ▼
           Claude          Cursor       AI Agents
30. And I think we should actually build it

Given your Odoo development work, this isn't just a theoretical open-source project. You would be an excellent first user.

Your own workflow becomes:

Customer requirement → AI → OCA MCP → existing OCA solution → customize only what's missing.

That could directly reduce the amount of custom Odoo development you do.

And if we make it good enough, the audience becomes much bigger than YantrAdhigam.

The next practical step should be Milestone 1: inspect the actual OCA GitHub repositories and maintainer-tools in detail, then design the exact database schema and crawler rules before writing the MCP server.

I would not start coding the MCP endpoint yet. The highest-risk part isn't MCP; it's correctly understanding and indexing the OCA ecosystem. Once that data layer is right, the MCP layer is comparatively straightforward. The current official Python SDK supports the required server primitives and Streamable HTTP, and the current MCP specification is mature enough for us to build against it.

Sources
OCA GitHub Organization
OCA Apps Store repository
OCA Maintainer Tools
Official MCP Python SDK
MCP Specification