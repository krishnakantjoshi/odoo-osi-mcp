import re
from dataclasses import dataclass, field
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from odoo_osi.db.models import Module, Repository, SourceFile
from odoo_osi.ingestion.odoo_versions import odoo_version_sort_key
from odoo_osi.search.fallback import DiscoveredModuleCandidate, GitHubModuleFallback
from odoo_osi.search.modules import ModuleSearchMatch, ModuleSearchQuery, ModuleSearchService


@dataclass(frozen=True)
class EvidenceSymbol:
    path: str
    symbol_type: str
    name: str | None
    odoo_model: str | None
    inherited_model: str | None
    xml_id: str | None
    parent_xml_id: str | None


@dataclass(frozen=True)
class SourceEvidence:
    indexed_source_files: int
    indexed_symbols: int
    indexed_search_documents: int
    readme_sections: int
    security_access_rules: int
    odoo_models: list[str] = field(default_factory=list)
    inherited_models: list[str] = field(default_factory=list)
    xml_records: list[str] = field(default_factory=list)
    readme_section_titles: list[str] = field(default_factory=list)
    sample_symbols: list[EvidenceSymbol] = field(default_factory=list)


@dataclass(frozen=True)
class SolutionCandidate:
    repository: str
    module: str
    odoo_version: str | None
    evidence_level: str
    summary: str | None
    license: str | None
    dependencies: list[str]
    source_url: str | None
    target_odoo_version: str | None
    version_status: str
    migration_effort: str | None
    migration_guidance: list[str]
    indexing_guidance: list[str]
    confidence: float
    why_matched: list[str]
    warnings: list[str]
    evidence: SourceEvidence


@dataclass(frozen=True)
class SolutionResult:
    requirement: str
    recommendation: str
    candidates: list[SolutionCandidate]


class SolutionService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def find_solution(
        self,
        requirement: str,
        odoo_version: str | None = None,
        limit: int = 8,
    ) -> SolutionResult:
        matches = await self._version_aware_matches(requirement, odoo_version, limit)
        modules_by_key = await self._load_modules(matches)
        candidates = [
            _candidate_from_match(
                match,
                modules_by_key.get((match.repository, match.module, match.odoo_version)),
                target_odoo_version=odoo_version,
            )
            for match in matches
        ]
        if _needs_live_fallback(candidates, requirement):
            discovered = await GitHubModuleFallback().discover(
                requirement=requirement,
                odoo_version=odoo_version,
                limit=limit,
            )
            candidates.extend(
                _candidate_from_discovered(
                    candidate,
                    target_odoo_version=odoo_version,
                )
                for candidate in discovered
                if not _already_present(candidates, candidate)
            )
        candidates = sorted(candidates, key=lambda candidate: candidate.confidence, reverse=True)
        selected_candidates = _select_candidates(
            candidates,
            limit,
            target_odoo_version=odoo_version,
        )
        return SolutionResult(
            requirement=requirement,
            recommendation=(
                "evaluate_existing_modules" if candidates else "no_indexed_candidate_found"
            ),
            candidates=selected_candidates,
        )

    async def _version_aware_matches(
        self,
        requirement: str,
        odoo_version: str | None,
        limit: int,
    ) -> list[ModuleSearchMatch]:
        search = ModuleSearchService(self._session)
        exact_matches: list[ModuleSearchMatch] = []
        if odoo_version is not None:
            exact_matches = await search.search(
                ModuleSearchQuery(query=requirement, odoo_version=odoo_version, limit=limit)
            )

        broad_matches = await search.search(
            ModuleSearchQuery(query=requirement, odoo_version=None, limit=max(limit * 3, 20))
        )
        return _merge_matches([*exact_matches, *broad_matches])

    async def _load_modules(
        self,
        matches: list[ModuleSearchMatch],
    ) -> dict[tuple[str, str, str | None], Module]:
        if not matches:
            return {}

        module_names = {match.module for match in matches}
        repository_names = {match.repository for match in matches}

        result = await self._session.execute(
            select(Module)
            .join(Repository, Repository.id == Module.repository_id)
            .where(
                Module.technical_name.in_(module_names),
                Repository.full_name.in_(repository_names),
            )
            .options(
                selectinload(Module.repository),
                selectinload(Module.source_files).selectinload(SourceFile.symbols),
                selectinload(Module.search_documents),
            )
        )
        modules = result.scalars().all()
        return {
            (module.repository.full_name, module.technical_name, module.odoo_version): module
            for module in modules
        }


def solution_result_payload(result: SolutionResult) -> dict[str, Any]:
    return {
        "requirement": result.requirement,
        "recommendation": result.recommendation,
        "candidates": [
            {
                "repository": candidate.repository,
                "module": candidate.module,
                "odoo_version": candidate.odoo_version,
                "evidence_level": candidate.evidence_level,
                "summary": candidate.summary,
                "license": candidate.license,
                "dependencies": candidate.dependencies,
                "source_url": candidate.source_url,
                "target_odoo_version": candidate.target_odoo_version,
                "version_status": candidate.version_status,
                "migration_effort": candidate.migration_effort,
                "migration_guidance": candidate.migration_guidance,
                "indexing_guidance": candidate.indexing_guidance,
                "confidence": candidate.confidence,
                "why_matched": candidate.why_matched,
                "warnings": candidate.warnings,
                "evidence": _source_evidence_payload(candidate.evidence),
            }
            for candidate in result.candidates
        ],
    }


def _candidate_from_match(
    match: ModuleSearchMatch,
    module: Module | None,
    target_odoo_version: str | None,
) -> SolutionCandidate:
    evidence = _source_evidence(module)
    version_assessment = _version_assessment(match.odoo_version, target_odoo_version)
    confidence = match.confidence
    why_matched = list(match.why_matched)
    if evidence.indexed_symbols:
        confidence = min(confidence + 0.05, 0.95)
        why_matched.append("indexed source symbols available")
    if evidence.indexed_search_documents:
        confidence = min(confidence + 0.05, 0.95)
        why_matched.append("indexed README/security documents available")
    if version_assessment.confidence_adjustment:
        confidence = max(min(confidence + version_assessment.confidence_adjustment, 0.95), 0.05)
    why_matched.extend(version_assessment.why_matched)

    return SolutionCandidate(
        repository=match.repository,
        module=match.module,
        odoo_version=match.odoo_version,
        evidence_level="indexed",
        summary=match.summary,
        license=match.license,
        dependencies=match.dependencies,
        source_url=match.source_url,
        target_odoo_version=target_odoo_version,
        version_status=version_assessment.status,
        migration_effort=version_assessment.migration_effort,
        migration_guidance=version_assessment.guidance,
        indexing_guidance=[],
        confidence=round(confidence, 2),
        why_matched=why_matched,
        warnings=[*_license_warnings(match.license), *version_assessment.warnings],
        evidence=evidence,
    )


def _candidate_from_discovered(
    discovered: DiscoveredModuleCandidate,
    target_odoo_version: str | None,
) -> SolutionCandidate:
    evidence = SourceEvidence(
        indexed_source_files=0,
        indexed_symbols=0,
        indexed_search_documents=0,
        readme_sections=0,
        security_access_rules=0,
    )
    version_assessment = _version_assessment(discovered.odoo_version, target_odoo_version)
    confidence = 0.58
    if discovered.odoo_version == target_odoo_version:
        confidence += 0.08
    confidence = max(min(confidence + version_assessment.confidence_adjustment, 0.86), 0.05)

    not_indexed_warning = (
        "Discovered from live GitHub/OCA fallback but not indexed locally; "
        "run targeted indexing before implementation analysis."
    )
    return SolutionCandidate(
        repository=discovered.repository,
        module=discovered.module,
        odoo_version=discovered.odoo_version,
        evidence_level="discovered_not_indexed",
        summary=discovered.summary,
        license=discovered.license,
        dependencies=discovered.dependencies,
        source_url=discovered.source_url,
        target_odoo_version=target_odoo_version,
        version_status=version_assessment.status,
        migration_effort=version_assessment.migration_effort,
        migration_guidance=version_assessment.guidance,
        indexing_guidance=[
            (
                "Index this module for source-backed evidence: "
                f"odoo-osi discover-oca --repository {discovered.repository_name} "
                f"--odoo-version {discovered.odoo_version or target_odoo_version or '<version>'} "
                "--persist"
            ),
            (
                "Then index source evidence: "
                f"odoo-osi index-source --repository {discovered.repository_name} "
                f"--module {discovered.module} "
                f"--odoo-version {discovered.odoo_version or target_odoo_version or '<version>'}"
            ),
        ],
        confidence=round(confidence, 2),
        why_matched=[
            *discovered.why_matched,
            "candidate is from live GitHub/OCA fallback",
            *version_assessment.why_matched,
        ],
        warnings=[
            *_license_warnings(discovered.license),
            not_indexed_warning,
            *version_assessment.warnings,
        ],
        evidence=evidence,
    )


@dataclass(frozen=True)
class VersionAssessment:
    status: str
    migration_effort: str | None
    confidence_adjustment: float
    why_matched: list[str]
    guidance: list[str]
    warnings: list[str]


def _version_assessment(
    candidate_odoo_version: str | None,
    target_odoo_version: str | None,
) -> VersionAssessment:
    if target_odoo_version is None:
        return VersionAssessment(
            status="not_evaluated",
            migration_effort=None,
            confidence_adjustment=0,
            why_matched=[],
            guidance=[],
            warnings=[],
        )

    if candidate_odoo_version is None:
        unknown_warning = (
            f"Version unknown: target is Odoo {target_odoo_version}; treat as a "
            "migration candidate, not a drop-in module."
        )
        return VersionAssessment(
            status="unknown_version",
            migration_effort="unknown",
            confidence_adjustment=-0.08,
            why_matched=["candidate has unknown Odoo version"],
            guidance=[
                "Inspect the manifest, branch, dependencies, and source APIs before migration."
            ],
            warnings=[unknown_warning],
        )

    if candidate_odoo_version == target_odoo_version:
        return VersionAssessment(
            status="exact_match",
            migration_effort=None,
            confidence_adjustment=0.05,
            why_matched=[f"matches target Odoo version {target_odoo_version}"],
            guidance=[],
            warnings=[],
        )

    try:
        candidate_major, _ = odoo_version_sort_key(candidate_odoo_version)
        target_major, _ = odoo_version_sort_key(target_odoo_version)
    except ValueError:
        mismatch_warning = (
            f"Version mismatch: candidate is {candidate_odoo_version}, "
            f"target is {target_odoo_version}."
        )
        return VersionAssessment(
            status="unparsed_version_gap",
            migration_effort="unknown",
            confidence_adjustment=-0.08,
            why_matched=["candidate version needs manual compatibility review"],
            guidance=[
                "Compare manifests, dependencies, data files, security rules, "
                "and Odoo API changes manually."
            ],
            warnings=[mismatch_warning],
        )

    version_gap = abs(target_major - candidate_major)
    migration_effort = _migration_effort(version_gap)
    if candidate_major < target_major:
        migration_reason = (
            f"available for older Odoo version {candidate_odoo_version}; "
            f"can be migrated to {target_odoo_version}"
        )
        migration_use = (
            f"Use this as source evidence for an Odoo {target_odoo_version} "
            "migration or enhancement."
        )
        migration_review = (
            "Review manifest version, dependencies, model API changes, XML view "
            "inheritance, security access rules, and tests."
        )
        migration_warning = (
            f"Version gap: module is indexed for Odoo {candidate_odoo_version}, "
            f"target is Odoo {target_odoo_version}; not a drop-in install."
        )
        return VersionAssessment(
            status="older_version_migration_candidate",
            migration_effort=migration_effort,
            confidence_adjustment=-min(0.03 * version_gap, 0.18),
            why_matched=[migration_reason],
            guidance=[
                migration_use,
                migration_review,
                "Have the AI propose a migration patch rather than generating "
                "the feature from scratch.",
            ],
            warnings=[migration_warning],
        )

    backport_reason = (
        f"available for newer Odoo version {candidate_odoo_version}; "
        f"can inform a {target_odoo_version} backport"
    )
    backport_use = (
        f"Use this as source evidence for an Odoo {target_odoo_version} "
        "backport or custom adaptation."
    )
    backport_warning = (
        f"Version gap: module is indexed for Odoo {candidate_odoo_version}, "
        f"target is Odoo {target_odoo_version}; backport review required."
    )
    return VersionAssessment(
        status="newer_version_backport_candidate",
        migration_effort=migration_effort,
        confidence_adjustment=-min(0.04 * version_gap, 0.2),
        why_matched=[backport_reason],
        guidance=[
            backport_use,
            "Review forward-version APIs carefully before applying patterns to the target version.",
        ],
        warnings=[backport_warning],
    )


def _migration_effort(version_gap: int) -> str:
    if version_gap <= 1:
        return "low"
    if version_gap <= 3:
        return "medium"
    return "high"


def _merge_matches(matches: list[ModuleSearchMatch]) -> list[ModuleSearchMatch]:
    unique_matches: dict[tuple[str, str, str | None], ModuleSearchMatch] = {}
    for match in matches:
        unique_matches.setdefault((match.repository, match.module, match.odoo_version), match)
    return list(unique_matches.values())


def _needs_live_fallback(candidates: list[SolutionCandidate], requirement: str) -> bool:
    if not candidates:
        return True
    if candidates[0].confidence < 0.7:
        return True

    candidate_modules = {candidate.module for candidate in candidates}
    module_like_terms = _module_like_terms(requirement)
    return any(term not in candidate_modules for term in module_like_terms)


def _already_present(
    candidates: list[SolutionCandidate],
    discovered: DiscoveredModuleCandidate,
) -> bool:
    return any(
        candidate.repository == discovered.repository
        and candidate.module == discovered.module
        and candidate.odoo_version == discovered.odoo_version
        for candidate in candidates
    )


def _module_like_terms(requirement: str) -> list[str]:
    raw_tokens = [token for token in re.split(r"[^a-zA-Z0-9_]+", requirement.lower()) if token]
    terms = [token for token in raw_tokens if "_" in token and len(token) > 4]
    return list(dict.fromkeys(terms))


def _select_candidates(
    candidates: list[SolutionCandidate],
    limit: int,
    target_odoo_version: str | None,
) -> list[SolutionCandidate]:
    selected = candidates[:limit]
    if target_odoo_version is None or len(selected) < limit:
        return selected

    has_cross_version = any(candidate.version_status != "exact_match" for candidate in selected)
    if has_cross_version:
        return selected

    migration_candidate = next(
        (candidate for candidate in candidates if candidate.version_status != "exact_match"),
        None,
    )
    if migration_candidate is None:
        return selected

    return [*selected[:-1], migration_candidate]


def _source_evidence(module: Module | None) -> SourceEvidence:
    if module is None:
        return SourceEvidence(
            indexed_source_files=0,
            indexed_symbols=0,
            indexed_search_documents=0,
            readme_sections=0,
            security_access_rules=0,
        )

    symbols = [
        (source_file, symbol)
        for source_file in module.source_files
        for symbol in source_file.symbols
    ]
    readme_documents = [
        document
        for document in module.search_documents
        if document.document_type.startswith("readme_")
    ]
    return SourceEvidence(
        indexed_source_files=len(module.source_files),
        indexed_symbols=len(symbols),
        indexed_search_documents=len(module.search_documents),
        readme_sections=len(readme_documents),
        security_access_rules=sum(
            1 for _, symbol in symbols if symbol.symbol_type == "access_rule"
        ),
        odoo_models=_unique_limited(symbol.odoo_model for _, symbol in symbols),
        inherited_models=_unique_limited(symbol.inherited_model for _, symbol in symbols),
        xml_records=_unique_limited(symbol.xml_id for _, symbol in symbols),
        readme_section_titles=_unique_limited(document.title for document in readme_documents),
        sample_symbols=[
            EvidenceSymbol(
                path=source_file.path,
                symbol_type=symbol.symbol_type,
                name=symbol.name,
                odoo_model=symbol.odoo_model,
                inherited_model=symbol.inherited_model,
                xml_id=symbol.xml_id,
                parent_xml_id=symbol.parent_xml_id,
            )
            for source_file, symbol in symbols[:10]
        ],
    )


def _source_evidence_payload(evidence: SourceEvidence) -> dict[str, Any]:
    return {
        "indexed_source_files": evidence.indexed_source_files,
        "indexed_symbols": evidence.indexed_symbols,
        "indexed_search_documents": evidence.indexed_search_documents,
        "readme_sections": evidence.readme_sections,
        "security_access_rules": evidence.security_access_rules,
        "odoo_models": evidence.odoo_models,
        "inherited_models": evidence.inherited_models,
        "xml_records": evidence.xml_records,
        "readme_section_titles": evidence.readme_section_titles,
        "sample_symbols": [
            {
                "path": symbol.path,
                "symbol_type": symbol.symbol_type,
                "name": symbol.name,
                "odoo_model": symbol.odoo_model,
                "inherited_model": symbol.inherited_model,
                "xml_id": symbol.xml_id,
                "parent_xml_id": symbol.parent_xml_id,
            }
            for symbol in evidence.sample_symbols
        ],
    }


def _license_warnings(license_name: str | None) -> list[str]:
    if license_name is None:
        return ["Module license is missing; inspect __manifest__.py before use."]
    if "AGPL" in license_name.upper():
        return [
            "AGPL module: review obligations before proprietary redistribution or modification."
        ]
    return []


def _unique_limited(values, limit: int = 12) -> list[str]:
    unique_values = []
    for value in values:
        if value and value not in unique_values:
            unique_values.append(value)
        if len(unique_values) >= limit:
            break
    return unique_values
