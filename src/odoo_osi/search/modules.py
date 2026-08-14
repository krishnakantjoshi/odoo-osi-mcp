import re
from dataclasses import dataclass, field

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from odoo_osi.db.models import Dependency, Module, Repository, SearchDocument


@dataclass(frozen=True)
class ModuleSearchQuery:
    query: str
    odoo_version: str | None = None
    license: str | None = None
    limit: int = 10


@dataclass(frozen=True)
class ModuleSearchMatch:
    repository: str
    module: str
    odoo_version: str | None
    summary: str | None
    license: str | None
    source_url: str | None
    dependencies: list[str] = field(default_factory=list)
    why_matched: list[str] = field(default_factory=list)
    confidence: float = 0.5


class ModuleSearchService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def search(self, query: ModuleSearchQuery) -> list[ModuleSearchMatch]:
        normalized_query = query.query.strip()
        tokens = _query_tokens(normalized_query)
        patterns = [f"%{token}%" for token in tokens] or [f"%{normalized_query}%"]

        statement = (
            select(Module)
            .join(Repository, Repository.id == Module.repository_id)
            .outerjoin(SearchDocument, SearchDocument.module_id == Module.id)
            .options(
                selectinload(Module.repository),
                selectinload(Module.dependencies),
                selectinload(Module.search_documents),
            )
            .where(
                or_(
                    *[
                        field.ilike(pattern)
                        for pattern in patterns
                        for field in (
                            Module.technical_name,
                            Module.display_name,
                            Module.summary,
                            Module.description,
                        )
                    ],
                    *[
                        field.ilike(pattern)
                        for pattern in patterns
                        for field in (
                            SearchDocument.title,
                            SearchDocument.body,
                        )
                    ],
                )
            )
            .order_by(Module.odoo_version.desc(), Module.technical_name.asc())
            .limit(max(query.limit * 20, 200))
        )

        if query.odoo_version is not None:
            statement = statement.where(Module.odoo_version == query.odoo_version)
        if query.license is not None:
            statement = statement.where(Module.license == query.license)

        result = await self._session.execute(statement)
        modules = result.scalars().unique().all()
        matches = [_to_match(module, normalized_query, tokens) for module in modules]
        return sorted(matches, key=lambda match: match.confidence, reverse=True)[: query.limit]


def _to_match(module: Module, query: str, tokens: list[str]) -> ModuleSearchMatch:
    why_matched = _why_matched(module, query, tokens)
    confidence = _confidence(module, query, tokens, why_matched)

    return ModuleSearchMatch(
        repository=module.repository.full_name,
        module=module.technical_name,
        odoo_version=module.odoo_version,
        summary=module.summary,
        license=module.license,
        source_url=module.source_url,
        dependencies=_dependency_names(module.dependencies),
        why_matched=why_matched,
        confidence=confidence,
    )


def _why_matched(module: Module, query: str, tokens: list[str]) -> list[str]:
    query_lower = query.lower()
    reasons: list[str] = []

    fields = {
        "technical_name": module.technical_name,
        "display_name": module.display_name,
        "summary": module.summary,
        "description": module.description,
    }
    for field_name, value in fields.items():
        if value and query_lower in value.lower():
            reasons.append(f"{field_name} contains query")
            continue
        matched_tokens = [token for token in tokens if value and token in value.lower()]
        if matched_tokens:
            reasons.append(f"{field_name} contains tokens: {', '.join(matched_tokens)}")

    document_reasons = _document_reasons(module.search_documents, query_lower, tokens)
    reasons.extend(document_reasons)

    return reasons or ["database text match"]


def _confidence(
    module: Module,
    query: str,
    tokens: list[str],
    why_matched: list[str],
) -> float:
    searchable = " ".join(
        value or ""
        for value in (
            module.technical_name,
            module.display_name,
            module.summary,
            module.description,
        )
    ).lower()
    document_searchable = " ".join(
        f"{document.title or ''} {document.body}" for document in module.search_documents
    ).lower()
    query_lower = query.lower()
    token_hits = sum(1 for token in tokens if token in searchable)
    document_token_hits = sum(1 for token in tokens if token in document_searchable)

    score = 0.4
    if query_lower in searchable:
        score += 0.25
    if tokens:
        score += min(token_hits / len(tokens), 1.0) * 0.25
    if any(reason.startswith("technical_name") for reason in why_matched):
        score += 0.1
    if query_lower in document_searchable:
        score += 0.15
    if tokens:
        score += min(document_token_hits / len(tokens), 1.0) * 0.15

    return round(min(score, 0.95), 2)


def _dependency_names(dependencies: list[Dependency]) -> list[str]:
    return sorted({dependency.dependency_name for dependency in dependencies})


def _query_tokens(query: str) -> list[str]:
    query = _normalize_domain_terms(query)
    base_tokens = [
        token for token in re.split(r"[^a-zA-Z0-9_.]+", query.lower()) if len(token) > 2
    ]
    expanded_tokens: list[str] = []
    for token in base_tokens:
        expanded_tokens.append(token)
        expanded_tokens.extend(_TOKEN_SYNONYMS.get(token, []))
    return list(dict.fromkeys(expanded_tokens))


def _document_reasons(
    documents: list[SearchDocument],
    query_lower: str,
    tokens: list[str],
) -> list[str]:
    reasons: list[str] = []
    for document in documents:
        searchable = f"{document.title or ''} {document.body}".lower()
        if query_lower in searchable:
            reasons.append(f"{document.document_type} contains query")
            continue
        matched_tokens = [token for token in tokens if token in searchable]
        if matched_tokens:
            reasons.append(
                f"{document.document_type} contains tokens: {', '.join(matched_tokens[:5])}"
            )
    return list(dict.fromkeys(reasons))[:5]


_TOKEN_SYNONYMS = {
    "approval": ["approve", "approved", "validation", "tier"],
    "approve": ["approval", "approved", "validation", "tier"],
    "approved": ["approval", "approve", "validation", "tier"],
    "reconcilation": ["reconciliation", "reconcile", "reconcile_oca"],
    "reconciliation": ["reconcile", "reconciled", "reconcile_oca"],
    "reconcile": ["reconciliation", "reconciled", "reconcile_oca"],
    "reconciled": ["reconcile", "reconciliation"],
    "workflow": ["validation", "tier", "exception"],
    "request": ["requisition"],
    "requisition": ["request"],
}


def _normalize_domain_terms(value: str) -> str:
    normalized = value.lower()
    for source, target in _NORMALIZED_TERMS.items():
        normalized = re.sub(rf"\b{re.escape(source)}\b", target, normalized)
    return normalized


_NORMALIZED_TERMS = {
    "reconcilation": "reconciliation",
    "reconcilliation": "reconciliation",
    "reconcillation": "reconciliation",
}
