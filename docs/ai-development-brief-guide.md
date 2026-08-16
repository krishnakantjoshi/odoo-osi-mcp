# AI Development Brief Guide For Odoo OSI

This guide explains what developers should ask an AI coding tool after Odoo OSI / Odoo
Community MCP finds, partially finds, or does not find an existing open-source Odoo module.

The goal is simple:

Before custom development starts, convert MCP search results into a clear development brief
with version rules, branding rules, exact files, and minimal tests.

## Core Workflow

1. Ask MCP to find an existing module.
2. Review whether the result is:
   - `indexed`
   - `discovered_not_indexed`
   - no good candidate found
3. Decide the development route:
   - use existing module
   - migrate existing module
   - enhance existing module
   - build custom module
4. Give the AI coding tool a structured development brief.
5. Require a file plan before code.
6. Require minimal tests for the target Odoo version.

## Coverage Check

Before treating "no good candidate found" as proof that no OCA solution exists, check local
index coverage.

Use the MCP tool:

```text
Call get_coverage_report on the odoo-osi MCP server.

Return:
1. indexed repositories
2. indexed Odoo version branches
3. indexed modules
4. source-indexed modules
5. README-indexed modules
6. security-rule-indexed modules
7. latest discovery job counters
8. latest source-indexing job counters
9. GitHub discovery gap estimate
10. external module catalog gap estimate
11. limitations
12. next indexing steps
```

Or use the local CLI/API:

```bash
odoo-osi coverage
curl http://127.0.0.1:8000/indexing/coverage
```

Interpretation:

- low indexed-module coverage means search results are useful but incomplete
- `discovered_not_indexed` means "lead found, source not parsed yet"
- broad OCA claims such as 20,000+ modules are catalog-scale signals, not proof that this
  local database has parsed every module
- before coding from an unindexed lead, run the returned `indexing_guidance`

## Prompt 1: Find Existing Solution

Use this first.

```text
Use the odoo-osi MCP server.

I am developing on Odoo <ODOO_VERSION> <EDITION>.

Requirement:
<REQUIREMENT>

Before writing custom code, check whether an existing open-source Odoo/OCA module satisfies
this requirement.

Return:
1. exact-version matches first
2. older-version migration candidates
3. newer-version backport candidates if relevant
4. discovered-but-not-indexed GitHub/OCA fallback candidates
5. module name
6. repository
7. license warning
8. evidence_level
9. version_status
10. migration_effort
11. source evidence
12. README evidence
13. security access-rule evidence
14. indexing_guidance if the module is not indexed

Do not generate custom code until the MCP result is reviewed.
```

Example:

```text
Use the odoo-osi MCP server.

I am developing on Odoo 18 Community.

Requirement:
I need account reconciliation feature.

Before writing custom code, check whether an existing open-source Odoo/OCA module satisfies
this requirement.
```

## Evidence Levels

### `indexed`

The module exists in the local Odoo OSI database and has parsed evidence.

The AI may use:

- manifest metadata
- dependencies
- license
- README sections
- Python models
- XML views/actions/menus
- security access rules
- source links

### `discovered_not_indexed`

The module was found through live GitHub/OCA fallback, but source evidence has not yet been
parsed locally.

The AI must treat this as a discovery lead, not full implementation evidence.

Before coding, run the `indexing_guidance` commands returned by MCP.

### No Good Candidate

No indexed or live-discovered module confidently satisfies the requirement.

The AI should build custom, but still inspect partial-fit modules and reusable patterns.

## Prompt 2: If A Module Is Found

Use this when MCP returns a strong existing candidate.

```text
Use the MCP result as the primary development reference.

Target:
- Odoo version: <ODOO_VERSION>
- Edition: <EDITION>
- Organization/developer: <ORG_NAME>
- Module technical prefix: <ORG_PREFIX>
- New module technical name: <NEW_MODULE_NAME>
- Reference module: <REFERENCE_MODULE>
- Reference repository: <REFERENCE_REPOSITORY>
- Reference Odoo version: <REFERENCE_ODOO_VERSION>
- Evidence level: <EVIDENCE_LEVEL>
- Version status: <VERSION_STATUS>
- Migration effort: <MIGRATION_EFFORT>

Development route:
<use_existing | migrate_existing | enhance_existing | build_adapter_module>

Instructions:
1. Analyze the reference module's manifest, dependencies, models, views, security rules,
   wizards, reports, data files, assets, README, and tests.
2. Identify what can be reused as-is.
3. Identify what needs migration or enhancement for Odoo <ODOO_VERSION>.
4. Do not invent a new architecture unless the reference module is insufficient.
5. Preserve license and attribution requirements.
6. Do not copy AGPL code into proprietary code without explicit compliance approval.
7. Produce a development brief before writing code.
8. Produce an exact file plan before writing code.
9. Produce minimal tests for Odoo <ODOO_VERSION>.
```

## Prompt 3: If Module Is Older Than Target Version

Use this when MCP returns `older_version_migration_candidate`.

```text
The reference module satisfies the requirement but is for an older Odoo version.

Target:
- Odoo version: <TARGET_ODOO_VERSION>
- Reference module version: <REFERENCE_ODOO_VERSION>
- Migration effort: <MIGRATION_EFFORT>

Before coding:
1. Compare manifest syntax and dependencies.
2. Check Python model API changes.
3. Check field definitions and decorators.
4. Check XML view inheritance changes.
5. Check action/menu syntax.
6. Check security access rules and record rules.
7. Check renamed models, methods, fields, or external IDs.
8. Check tests or demo flows from the reference module.
9. List migration risks.
10. Propose a migration plan.

Then build the Odoo <TARGET_ODOO_VERSION> module using the reference module as source
evidence, not as blindly copied code.
```

## Prompt 4: If No Module Is Found

Use this when MCP has no strong candidate.

```text
No indexed or live-discovered OCA module confidently satisfies this requirement.

Requirement:
<REQUIREMENT>

Target:
- Odoo version: <ODOO_VERSION>
- Edition: <EDITION>
- Organization/developer: <ORG_NAME>
- Module technical prefix: <ORG_PREFIX>
- New module technical name: <NEW_MODULE_NAME>

Before coding:
1. List nearest partial-fit modules from MCP.
2. Explain why each partial-fit module is insufficient.
3. Identify reusable Odoo patterns from related modules.
4. Create a custom Odoo <ODOO_VERSION> module.
5. Keep the module small and focused.
6. Follow <ORG_NAME> branding and naming rules.
7. Produce an exact file plan before code.
8. Produce minimal tests.
9. Clearly document assumptions and limitations.
```

## Version-Specific Skill Checklist

Ask the AI to produce this before writing code.

```text
Produce an Odoo <ODOO_VERSION> implementation brief.

Include:
1. supported Odoo <ODOO_VERSION> manifest syntax
2. Python model syntax
3. supported field definitions
4. correct use of models.Model and models.TransientModel
5. correct use of @api.depends, @api.constrains, and @api.onchange
6. constraints and validation strategy
7. XML view inheritance syntax
8. action/menu XML syntax
9. security/ir.model.access.csv rules
10. record-rule XML rules if needed
11. data/demo loading rules
12. asset bundle syntax if assets are needed
13. test style for Odoo <ODOO_VERSION>
14. Community Edition limitations
15. known migration risks from reference version to target version

Do not write code until this brief is complete.
```

## Branding Prompt

Use this in every coding request.

```text
Build this as an Odoo <ODOO_VERSION> Community custom module for <ORG_NAME>.

Branding and ownership requirements:
1. Technical module prefix: <ORG_PREFIX>_
2. Module name: <NEW_MODULE_NAME>
3. Author: <ORG_NAME>
4. Website: <ORG_WEBSITE>
5. License: <CHOSEN_LICENSE>
6. Use <ORG_NAME> in README and manifest author metadata.
7. Use business-friendly labels in menus, views, actions, and messages.
8. Do not keep OCA branding in the custom module except attribution where required.
9. If implementation is derived from an OCA module, include attribution in README.
10. Preserve license obligations and flag compliance risks.
```

## File Plan Prompt

Require this before code.

```text
Before generating code, list the exact files to create or modify.

For each file include:
1. path
2. purpose
3. why it is needed
4. whether it is new or modified
5. key classes, records, or tests it will contain

Use standard Odoo structure where applicable:
- __init__.py
- __manifest__.py
- models/__init__.py
- models/*.py
- views/*.xml
- security/ir.model.access.csv
- security/*.xml
- data/*.xml
- wizards/__init__.py
- wizards/*.py
- wizards/*.xml
- reports/*.xml
- static/src/* if assets are required
- tests/__init__.py
- tests/test_*.py
- README.md

Do not create unnecessary files.
```

## Minimal Test Prompt

Use for every module.

```text
Create minimal tests for Odoo <ODOO_VERSION>.

Tests must cover:
1. module installs successfully
2. main business flow works
3. required security access exists
4. validation errors are raised correctly
5. important computed fields or constraints work
6. wizard flow works if a wizard is added
7. XML external IDs referenced by actions/views are valid where practical

Use the appropriate Odoo <ODOO_VERSION> test style, such as TransactionCase or SavepointCase.
Keep tests minimal but meaningful.
```

## Validation Prompt

Use this before accepting generated code.

```text
Review the generated Odoo module.

Check:
1. manifest is valid for Odoo <ODOO_VERSION>
2. dependencies are correct and minimal
3. imports are valid
4. models are registered through __init__.py
5. XML files are listed in manifest data/assets correctly
6. security access rules cover new models
7. constraints prevent invalid data
8. user-facing errors are clear
9. no dead files are created
10. tests match the business requirement
11. license and attribution are correct
12. code follows Odoo conventions

Return:
- blocking issues
- non-blocking improvements
- exact files to fix
- final recommendation
```

## Full Prompt Template: Module Found

Copy this into the AI coding tool after MCP finds a module.

```text
Use the odoo-osi MCP result below as the primary reference.

MCP result:
<PASTE_MCP_RESULT>

Requirement:
<REQUIREMENT>

Target:
- Odoo version: <ODOO_VERSION>
- Edition: <EDITION>
- Organization/developer: <ORG_NAME>
- Website: <ORG_WEBSITE>
- Technical module prefix: <ORG_PREFIX>
- New module technical name: <NEW_MODULE_NAME>
- License policy: <LICENSE_POLICY>

Instructions:
1. Decide whether to use, migrate, enhance, adapt, or build custom.
2. Explain the decision using MCP evidence.
3. Produce an Odoo <ODOO_VERSION> skill/syntax/limitations brief.
4. Produce a branding brief for <ORG_NAME>.
5. Produce an exact file plan.
6. Produce minimal test cases.
7. Only after the brief and file plan are approved, generate code.

Important:
- If evidence_level is discovered_not_indexed, do not treat it as source-backed evidence yet.
- If version_status is older_version_migration_candidate, produce a migration plan.
- If license is AGPL, flag compliance review before proprietary redistribution or copying code.
- Do not create unnecessary files.
```

## Full Prompt Template: Module Not Found

Copy this into the AI coding tool when MCP finds no good module.

```text
The odoo-osi MCP server did not find a strong existing module.

MCP result:
<PASTE_MCP_RESULT>

Requirement:
<REQUIREMENT>

Target:
- Odoo version: <ODOO_VERSION>
- Edition: <EDITION>
- Organization/developer: <ORG_NAME>
- Website: <ORG_WEBSITE>
- Technical module prefix: <ORG_PREFIX>
- New module technical name: <NEW_MODULE_NAME>
- License policy: <LICENSE_POLICY>

Instructions:
1. List the nearest partial-fit modules and why they are insufficient.
2. Identify reusable Odoo patterns from related modules.
3. Produce an Odoo <ODOO_VERSION> skill/syntax/limitations brief.
4. Produce a branding brief for <ORG_NAME>.
5. Produce an exact file plan.
6. Produce minimal test cases.
7. Build the smallest custom module that satisfies the requirement.
8. Clearly document assumptions and limitations.

Do not generate code until the development brief and file plan are complete.
```

## Recommended MCP Tool To Add Next

Future tool:

```text
prepare_development_brief
```

Suggested input:

```json
{
  "requirement": "I need account reconciliation feature",
  "odoo_version": "18.0",
  "edition": "community",
  "organization": "Your Org",
  "organization_website": "https://example.com",
  "module_prefix": "your_org",
  "new_module_name": "your_org_account_reconcile",
  "license_policy": "proprietary_with_oca_review"
}
```

Suggested output:

- recommendation status
- reference modules
- evidence level
- version status
- migration/backport guidance
- Odoo version syntax checklist
- Community Edition limitations
- branding instructions
- exact file plan
- minimal test plan
- final prompt for the coding AI
