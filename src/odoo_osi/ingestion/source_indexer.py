from dataclasses import dataclass
from hashlib import sha256

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from odoo_osi.db.models import Module, Repository, SearchDocument, SourceFile, Symbol
from odoo_osi.ingestion.github import GitHubClient
from odoo_osi.ingestion.source_files import SourceFileCandidate, discover_source_file_candidates
from odoo_osi.parsers.csv_security import parse_access_rules
from odoo_osi.parsers.python_symbols import parse_python_symbols
from odoo_osi.parsers.readme import parse_readme_sections
from odoo_osi.parsers.xml_symbols import parse_xml_symbols


@dataclass(frozen=True)
class SourceIndexOptions:
    owner: str = "OCA"
    repository: str | None = None
    module: str | None = None
    odoo_version: str | None = None
    module_limit: int | None = None
    file_limit_per_module: int = 20


@dataclass(frozen=True)
class SourceIndexReport:
    modules_seen: int
    files_indexed: int
    symbols_indexed: int
    errors: list[str]


class SourceIndexer:
    def __init__(self, session: AsyncSession, github: GitHubClient) -> None:
        self._session = session
        self._github = github

    async def index(self, options: SourceIndexOptions) -> SourceIndexReport:
        modules = await self._load_modules(options)
        files_indexed = 0
        symbols_indexed = 0
        errors: list[str] = []

        for module in modules:
            repository = module.repository
            branch_name = module.branch.name

            try:
                tree = await self._github.get_tree(
                    repository.owner,
                    repository.name,
                    branch_name,
                )
            except Exception as exc:  # pragma: no cover - network edge
                errors.append(f"{repository.full_name}/{branch_name}: {exc}")
                continue

            candidates = discover_source_file_candidates(
                tree,
                module.path,
                limit=options.file_limit_per_module,
            )

            for candidate in candidates:
                try:
                    content = await self._github.get_file_text(
                        repository.owner,
                        repository.name,
                        branch_name,
                        candidate.path,
                    )
                    source_file = await self._upsert_source_file(module, candidate, content)
                    count = await self._replace_symbols(
                        module,
                        source_file,
                        candidate.path,
                        content,
                    )
                    await self._replace_search_documents(
                        module,
                        source_file,
                        candidate.path,
                        content,
                    )
                    files_indexed += 1
                    symbols_indexed += count
                except Exception as exc:  # pragma: no cover - network/parser edge
                    errors.append(f"{repository.full_name}/{branch_name}/{candidate.path}: {exc}")

        await self._session.commit()
        return SourceIndexReport(
            modules_seen=len(modules),
            files_indexed=files_indexed,
            symbols_indexed=symbols_indexed,
            errors=errors,
        )

    async def _load_modules(self, options: SourceIndexOptions) -> list[Module]:
        statement = (
            select(Module)
            .join(Repository, Repository.id == Module.repository_id)
            .options(selectinload(Module.repository), selectinload(Module.branch))
            .where(Repository.owner == options.owner)
            .order_by(Repository.full_name.asc(), Module.technical_name.asc())
        )

        if options.repository is not None:
            statement = statement.where(Repository.name == options.repository)
        if options.module is not None:
            statement = statement.where(Module.technical_name == options.module)
        if options.odoo_version is not None:
            statement = statement.where(Module.odoo_version == options.odoo_version)
        if options.module_limit is not None:
            statement = statement.limit(options.module_limit)

        result = await self._session.execute(statement)
        return list(result.scalars().all())

    async def _upsert_source_file(
        self,
        module: Module,
        candidate: SourceFileCandidate,
        content: str,
    ) -> SourceFile:
        result = await self._session.execute(
            select(SourceFile).where(
                SourceFile.module_id == module.id,
                SourceFile.path == candidate.path,
            )
        )
        source_file = result.scalar_one_or_none()

        if source_file is None:
            source_file = SourceFile(module_id=module.id, path=candidate.path)
            self._session.add(source_file)

        source_file.file_type = candidate.file_type
        source_file.language = candidate.language
        source_file.size = candidate.size
        source_file.sha = candidate.sha
        source_file.content_hash = sha256(content.encode("utf-8")).hexdigest()

        await self._session.flush()
        return source_file

    async def _replace_symbols(
        self,
        module: Module,
        source_file: SourceFile,
        path: str,
        content: str,
    ) -> int:
        await self._session.execute(
            Symbol.__table__.delete().where(Symbol.source_file_id == source_file.id)
        )

        if path.endswith(".py"):
            symbols = [
                Symbol(
                    module_id=module.id,
                    source_file_id=source_file.id,
                    symbol_type=symbol.symbol_type,
                    name=symbol.name,
                    odoo_model=symbol.odoo_model,
                    inherited_model=symbol.inherited_model,
                    line_start=symbol.line_start,
                    line_end=symbol.line_end,
                    extra=symbol.metadata,
                )
                for symbol in parse_python_symbols(content)
            ]
        elif path.endswith(".xml"):
            symbols = [
                Symbol(
                    module_id=module.id,
                    source_file_id=source_file.id,
                    symbol_type=symbol.symbol_type,
                    name=symbol.name,
                    odoo_model=symbol.odoo_model,
                    xml_id=symbol.xml_id,
                    parent_xml_id=symbol.parent_xml_id,
                    extra=symbol.metadata,
                )
                for symbol in parse_xml_symbols(content)
            ]
        elif path.endswith(".csv"):
            symbols = [
                Symbol(
                    module_id=module.id,
                    source_file_id=source_file.id,
                    symbol_type="access_rule",
                    name=symbol.name,
                    odoo_model=symbol.odoo_model,
                    xml_id=symbol.xml_id,
                    extra=symbol.metadata,
                )
                for symbol in parse_access_rules(content)
            ]
        else:
            symbols = []

        self._session.add_all(symbols)
        await self._session.flush()
        return len(symbols)

    async def _replace_search_documents(
        self,
        module: Module,
        source_file: SourceFile,
        path: str,
        content: str,
    ) -> int:
        await self._session.execute(
            SearchDocument.__table__.delete().where(
                SearchDocument.source_file_id == source_file.id
            )
        )

        documents = []
        filename = path.rsplit("/", 1)[-1].lower()
        if filename.startswith("readme") and (path.endswith(".md") or path.endswith(".rst")):
            documents = [
                SearchDocument(
                    module_id=module.id,
                    source_file_id=source_file.id,
                    document_type=f"readme_{section.section_type}",
                    title=section.title,
                    body=section.body,
                    extra={"path": path, "section_type": section.section_type},
                )
                for section in parse_readme_sections(content)
            ]
        elif path.endswith(".csv") and filename == "ir.model.access.csv":
            documents = [
                SearchDocument(
                    module_id=module.id,
                    source_file_id=source_file.id,
                    document_type="security_access_rule",
                    title=symbol.name,
                    body=_access_rule_body(symbol),
                    extra=symbol.metadata,
                )
                for symbol in parse_access_rules(content)
            ]

        self._session.add_all(documents)
        await self._session.flush()
        return len(documents)


def _access_rule_body(symbol) -> str:
    permissions = ", ".join(
        permission for permission, allowed in symbol.permissions.items() if allowed
    )
    return (
        f"Access rule {symbol.name or symbol.xml_id or 'unnamed'} "
        f"for model {symbol.odoo_model or 'unknown'} "
        f"group {symbol.group_xml_id or 'all users'} "
        f"permissions {permissions or 'none'}."
    )
