import re
from dataclasses import dataclass

from odoo_osi.core.config import get_settings
from odoo_osi.ingestion.contracts import GitHubCodeSearchItem
from odoo_osi.ingestion.github import GitHubClient
from odoo_osi.ingestion.odoo_versions import odoo_version_sort_key, parse_odoo_version_branch
from odoo_osi.parsers.manifest import ManifestParseError, ParsedManifest, parse_manifest


@dataclass(frozen=True)
class DiscoveredModuleCandidate:
    repository: str
    owner: str
    repository_name: str
    module: str
    odoo_version: str | None
    summary: str | None
    license: str | None
    dependencies: list[str]
    source_url: str
    manifest_path: str
    why_matched: list[str]


class GitHubModuleFallback:
    def __init__(self, client: GitHubClient | None = None) -> None:
        self._client = client

    async def discover(
        self,
        requirement: str,
        odoo_version: str | None = None,
        limit: int = 5,
    ) -> list[DiscoveredModuleCandidate]:
        settings = get_settings()
        owns_client = self._client is None
        client = self._client or GitHubClient(token=settings.github_token)
        try:
            terms = _candidate_terms(requirement)
            if not terms:
                return []
            results = await self._search_manifest_hits(client, settings.github_owner, terms)
            candidates = []
            seen: set[tuple[str, str, str | None]] = set()
            for result in results:
                candidate = await self._candidate_from_search_result(
                    client,
                    result,
                    target_odoo_version=odoo_version,
                    terms=terms,
                )
                if candidate is None:
                    continue
                key = (candidate.repository, candidate.module, candidate.odoo_version)
                if key in seen:
                    continue
                seen.add(key)
                candidates.append(candidate)
                if len(candidates) >= limit:
                    break
            return candidates
        finally:
            if owns_client:
                await client.close()

    async def _search_manifest_hits(
        self,
        client: GitHubClient,
        owner: str,
        terms: list[str],
    ) -> list[GitHubCodeSearchItem]:
        hits: list[GitHubCodeSearchItem] = []
        seen: set[tuple[str, str]] = set()
        for term in terms[:4]:
            query = f"org:{owner} filename:__manifest__.py {term}"
            try:
                results = await client.search_code(query, per_page=10)
            except Exception:
                continue
            for result in results:
                key = (result.repository_full_name, result.path)
                if key in seen:
                    continue
                seen.add(key)
                hits.append(result)
        return hits

    async def _candidate_from_search_result(
        self,
        client: GitHubClient,
        result: GitHubCodeSearchItem,
        target_odoo_version: str | None,
        terms: list[str],
    ) -> DiscoveredModuleCandidate | None:
        module = result.path.split("/", maxsplit=1)[0]
        if module.startswith(".") or result.path.count("/") != 1:
            return None

        try:
            branch_name = await _best_branch(
                client,
                result.repository_owner,
                result.repository_name,
                target_odoo_version,
            )
            manifest_text = await client.get_file_text(
                result.repository_owner,
                result.repository_name,
                branch_name,
                result.path,
            )
            manifest = parse_manifest(manifest_text)
        except (ManifestParseError, Exception):
            return None

        odoo_version = parse_odoo_version_branch(branch_name)
        return DiscoveredModuleCandidate(
            repository=result.repository_full_name,
            owner=result.repository_owner,
            repository_name=result.repository_name,
            module=module,
            odoo_version=odoo_version,
            summary=manifest.summary or manifest.name,
            license=manifest.license,
            dependencies=manifest.depends,
            source_url=_source_url(result, branch_name, module),
            manifest_path=result.path,
            why_matched=_why_discovered(module, manifest, terms),
        )


async def _best_branch(
    client: GitHubClient,
    owner: str,
    repository: str,
    target_odoo_version: str | None,
) -> str:
    branches = await client.list_branches(owner, repository)
    branch_names = [branch.name for branch in branches]
    if target_odoo_version in branch_names:
        return target_odoo_version

    version_branches = [
        version
        for branch_name in branch_names
        if (version := parse_odoo_version_branch(branch_name))
    ]
    if version_branches:
        return sorted(version_branches, key=odoo_version_sort_key, reverse=True)[0]

    repository_payload = await client.get_repository(owner, repository)
    return repository_payload.default_branch


def _candidate_terms(requirement: str) -> list[str]:
    normalized = requirement.strip().lower()
    normalized = _normalize_domain_terms(normalized)
    snake = re.sub(r"[^a-z0-9]+", "_", normalized).strip("_")
    tokens = [token for token in snake.split("_") if len(token) > 2]
    meaningful_tokens = [
        token for token in tokens if token not in _STOPWORDS and not token.isdigit()
    ]
    terms = []
    if "_" in snake and len(snake) <= 80:
        terms.append(snake)
    terms.extend(_domain_phrases(meaningful_tokens))
    terms.extend(meaningful_tokens)
    for token in meaningful_tokens:
        terms.extend(_TOKEN_SYNONYMS.get(token, []))
    return list(dict.fromkeys(term for term in terms if term))


def _normalize_domain_terms(value: str) -> str:
    normalized = value
    for source, target in _NORMALIZED_TERMS.items():
        normalized = re.sub(rf"\b{re.escape(source)}\b", target, normalized)
    return normalized


def _domain_phrases(tokens: list[str]) -> list[str]:
    phrases = []
    if "account" in tokens and "reconciliation" in tokens:
        phrases.extend(["account_reconcile_oca", "account_reconcile", "account reconciliation"])
    if "account" in tokens and "reconcile" in tokens:
        phrases.extend(["account_reconcile_oca", "account_reconcile", "account reconcile"])
    if "bank" in tokens and "statement" in tokens:
        phrases.extend(["bank_statement", "account_statement"])
    return phrases


def _why_discovered(module: str, manifest: ParsedManifest, terms: list[str]) -> list[str]:
    searchable = " ".join(
        value or "" for value in (module, manifest.name, manifest.summary, manifest.description)
    ).lower()
    matched_terms = [
        term for term in terms if term.replace("_", " ") in searchable or term in searchable
    ]
    if matched_terms:
        return [f"live GitHub/OCA fallback matched terms: {', '.join(matched_terms[:5])}"]
    return ["live GitHub/OCA fallback discovered module manifest"]


def _source_url(result: GitHubCodeSearchItem, branch_name: str, module: str) -> str:
    return (
        f"https://github.com/{result.repository_full_name}/tree/"
        f"{branch_name}/{module}"
    )


_NORMALIZED_TERMS = {
    "reconcilation": "reconciliation",
    "reconcilliation": "reconciliation",
    "reconcillation": "reconciliation",
}

_TOKEN_SYNONYMS = {
    "reconciliation": ["reconcile", "reconcile_oca"],
    "reconcile": ["reconciliation", "reconcile_oca"],
}

_STOPWORDS = {
    "and",
    "app",
    "feature",
    "for",
    "have",
    "need",
    "odoo",
    "using",
    "version",
    "with",
}
