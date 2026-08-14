from dataclasses import dataclass
from typing import Any

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from odoo_osi.db.models import Module, Repository, SourceFile
from odoo_osi.search.modules import ModuleSearchMatch, ModuleSearchQuery, ModuleSearchService
from odoo_osi.search.solutions import (
    SolutionCandidate,
    SolutionService,
    _candidate_from_match,
    _source_evidence_payload,
)


@dataclass(frozen=True)
class ModuleComparisonSpec:
    repository: str
    module: str
    owner: str = "OCA"
    odoo_version: str | None = None


class ModuleComparisonService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def compare(
        self,
        requirement: str,
        target_odoo_version: str | None = None,
        candidates: list[ModuleComparisonSpec] | None = None,
        limit: int = 5,
    ) -> dict[str, Any]:
        if candidates:
            solution_candidates = await self._explicit_candidates(
                requirement=requirement,
                target_odoo_version=target_odoo_version,
                candidates=candidates,
            )
        else:
            result = await SolutionService(self._session).find_solution(
                requirement=requirement,
                odoo_version=target_odoo_version,
                limit=limit,
            )
            solution_candidates = result.candidates

        compared = [
            _comparison_candidate_payload(candidate) for candidate in solution_candidates[:limit]
        ]
        compared = sorted(compared, key=lambda candidate: candidate["score"], reverse=True)
        recommendation = _overall_recommendation(compared)

        return {
            "requirement": requirement,
            "target_odoo_version": target_odoo_version,
            "recommendation": recommendation,
            "candidates": compared,
        }

    async def _explicit_candidates(
        self,
        requirement: str,
        target_odoo_version: str | None,
        candidates: list[ModuleComparisonSpec],
    ) -> list[SolutionCandidate]:
        modules = await self._load_modules(candidates)
        search_confidence = await self._search_confidence(requirement)
        solution_candidates = []
        for module in modules:
            key = (module.repository.full_name, module.technical_name, module.odoo_version)
            match = ModuleSearchMatch(
                repository=module.repository.full_name,
                module=module.technical_name,
                odoo_version=module.odoo_version,
                summary=module.summary,
                license=module.license,
                source_url=module.source_url,
                dependencies=sorted(
                    {dependency.dependency_name for dependency in module.dependencies}
                ),
                why_matched=search_confidence.get(key, {}).get(
                    "why_matched",
                    ["selected for comparison"],
                ),
                confidence=search_confidence.get(key, {}).get("confidence", 0.5),
            )
            solution_candidates.append(
                _candidate_from_match(
                    match,
                    module,
                    target_odoo_version=target_odoo_version,
                )
            )
        return solution_candidates

    async def _load_modules(self, candidates: list[ModuleComparisonSpec]) -> list[Module]:
        conditions = []
        for candidate in candidates:
            repository_name = candidate.repository.rsplit("/", 1)[-1]
            condition = (
                (Repository.owner == candidate.owner)
                & (Repository.name == repository_name)
                & (Module.technical_name == candidate.module)
            )
            if candidate.odoo_version is not None:
                condition = condition & (Module.odoo_version == candidate.odoo_version)
            conditions.append(condition)

        result = await self._session.execute(
            select(Module)
            .join(Repository, Repository.id == Module.repository_id)
            .where(or_(*conditions))
            .options(
                selectinload(Module.repository),
                selectinload(Module.dependencies),
                selectinload(Module.source_files).selectinload(SourceFile.symbols),
                selectinload(Module.search_documents),
            )
        )
        return list(result.scalars().unique().all())

    async def _search_confidence(self, requirement: str) -> dict[tuple[str, str, str | None], dict]:
        matches = await ModuleSearchService(self._session).search(
            ModuleSearchQuery(query=requirement, limit=100)
        )
        return {
            (match.repository, match.module, match.odoo_version): {
                "confidence": match.confidence,
                "why_matched": match.why_matched,
            }
            for match in matches
        }


def _comparison_candidate_payload(candidate: SolutionCandidate) -> dict[str, Any]:
    evidence = _source_evidence_payload(candidate.evidence)
    license_risk = _license_risk(candidate.license)
    score = _comparison_score(candidate, license_risk)
    return {
        "repository": candidate.repository,
        "module": candidate.module,
        "odoo_version": candidate.odoo_version,
        "target_odoo_version": candidate.target_odoo_version,
        "summary": candidate.summary,
        "license": candidate.license,
        "license_risk": license_risk,
        "dependencies": candidate.dependencies,
        "dependency_count": len(candidate.dependencies),
        "source_url": candidate.source_url,
        "version_status": candidate.version_status,
        "migration_effort": candidate.migration_effort,
        "migration_guidance": candidate.migration_guidance,
        "confidence": candidate.confidence,
        "score": score,
        "strengths": _strengths(candidate, evidence),
        "cautions": _cautions(candidate, evidence, license_risk),
        "why_matched": candidate.why_matched,
        "warnings": candidate.warnings,
        "evidence": evidence,
        "recommended_action": _recommended_action(candidate, license_risk),
    }


def _comparison_score(candidate: SolutionCandidate, license_risk: str) -> float:
    score = candidate.confidence
    if candidate.version_status == "exact_match":
        score += 0.08
    elif candidate.version_status == "older_version_migration_candidate":
        score -= 0.02
    elif candidate.version_status == "newer_version_backport_candidate":
        score -= 0.04

    if candidate.evidence.indexed_symbols:
        score += 0.04
    if candidate.evidence.readme_sections:
        score += 0.03
    if candidate.evidence.security_access_rules:
        score += 0.02
    if license_risk == "review_required":
        score -= 0.05
    if license_risk == "unknown":
        score -= 0.08

    return round(max(min(score, 0.99), 0.01), 2)


def _license_risk(license_name: str | None) -> str:
    if license_name is None:
        return "unknown"
    if "AGPL" in license_name.upper():
        return "review_required"
    return "low"


def _strengths(candidate: SolutionCandidate, evidence: dict[str, Any]) -> list[str]:
    strengths = []
    if candidate.version_status == "exact_match":
        strengths.append("Matches the target Odoo version.")
    if candidate.version_status == "older_version_migration_candidate":
        strengths.append("Existing older-version implementation can guide migration.")
    if evidence["indexed_symbols"]:
        strengths.append("Has indexed source symbols for implementation review.")
    if evidence["readme_sections"]:
        strengths.append("Has indexed README documentation.")
    if evidence["security_access_rules"]:
        strengths.append("Includes indexed security access rules.")
    if candidate.dependencies:
        strengths.append("Dependencies are explicitly captured.")
    return strengths or ["Candidate is indexed with manifest metadata."]


def _cautions(
    candidate: SolutionCandidate,
    evidence: dict[str, Any],
    license_risk: str,
) -> list[str]:
    cautions = list(candidate.warnings)
    if not evidence["indexed_symbols"]:
        cautions.append("Source symbols are not indexed yet; inspect source before adoption.")
    if not evidence["readme_sections"]:
        cautions.append("README evidence is not indexed yet.")
    if license_risk == "unknown":
        cautions.append("License is unknown; verify manifest license before use.")
    return list(dict.fromkeys(cautions))


def _recommended_action(candidate: SolutionCandidate, license_risk: str) -> str:
    if candidate.version_status == "exact_match" and license_risk == "low":
        return "use_existing_module"
    if candidate.version_status == "exact_match":
        return "evaluate_existing_module_with_compliance_review"
    if candidate.version_status == "older_version_migration_candidate":
        return "migrate_or_enhance_existing_module"
    if candidate.version_status == "newer_version_backport_candidate":
        return "backport_or_adapt_existing_module"
    return "manual_review"


def _overall_recommendation(candidates: list[dict[str, Any]]) -> dict[str, Any]:
    if not candidates:
        return {
            "decision": "no_candidates",
            "module": None,
            "repository": None,
            "rationale": "No indexed candidates were available to compare.",
        }

    top = candidates[0]
    if top["recommended_action"] == "use_existing_module":
        decision = "use_existing_module"
    elif top["version_status"] != "exact_match":
        decision = "migrate_or_adapt_existing_module"
    else:
        decision = "evaluate_existing_module"

    return {
        "decision": decision,
        "module": top["module"],
        "repository": top["repository"],
        "odoo_version": top["odoo_version"],
        "score": top["score"],
        "rationale": top["strengths"][:3],
    }
