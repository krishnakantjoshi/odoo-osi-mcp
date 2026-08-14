from dataclasses import dataclass

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from odoo_osi.db.models import Module, Repository, SourceFile, Symbol


@dataclass(frozen=True)
class CodeSearchQuery:
    query: str
    odoo_version: str | None = None
    limit: int = 20


@dataclass(frozen=True)
class CodeSearchMatch:
    repository: str
    module: str
    odoo_version: str | None
    path: str
    symbol_type: str
    name: str | None
    odoo_model: str | None
    inherited_model: str | None
    xml_id: str | None
    parent_xml_id: str | None


class CodeSearchService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def search(self, query: CodeSearchQuery) -> list[CodeSearchMatch]:
        normalized_query = query.query.strip()
        pattern = f"%{normalized_query}%"

        statement = (
            select(Symbol, SourceFile, Module, Repository)
            .join(SourceFile, SourceFile.id == Symbol.source_file_id)
            .join(Module, Module.id == Symbol.module_id)
            .join(Repository, Repository.id == Module.repository_id)
            .where(
                or_(
                    Symbol.name.ilike(pattern),
                    Symbol.odoo_model.ilike(pattern),
                    Symbol.inherited_model.ilike(pattern),
                    Symbol.xml_id.ilike(pattern),
                    Symbol.parent_xml_id.ilike(pattern),
                )
            )
            .order_by(
                Repository.full_name.asc(),
                Module.technical_name.asc(),
                SourceFile.path.asc(),
            )
            .limit(query.limit)
        )

        if query.odoo_version is not None:
            statement = statement.where(Module.odoo_version == query.odoo_version)

        rows = await self._session.execute(statement)
        return [
            CodeSearchMatch(
                repository=repository.full_name,
                module=module.technical_name,
                odoo_version=module.odoo_version,
                path=source_file.path,
                symbol_type=symbol.symbol_type,
                name=symbol.name,
                odoo_model=symbol.odoo_model,
                inherited_model=symbol.inherited_model,
                xml_id=symbol.xml_id,
                parent_xml_id=symbol.parent_xml_id,
            )
            for symbol, source_file, module, repository in rows.all()
        ]
