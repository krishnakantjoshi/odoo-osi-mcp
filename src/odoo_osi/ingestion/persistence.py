from datetime import UTC, datetime

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from odoo_osi.db.models import Branch, Dependency, Module, Repository
from odoo_osi.ingestion.discovery import DiscoveredBranch, DiscoveredModule, DiscoveryReport


class IndexWriter:
    """Persist discovered repository/module data into the knowledge database."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def persist_report(self, report: DiscoveryReport) -> None:
        for discovered_branch in report.branches:
            repository = await self._upsert_repository(discovered_branch)
            branch = await self._upsert_branch(repository, discovered_branch)

            for discovered_module in discovered_branch.modules:
                module = await self._upsert_module(repository, branch, discovered_module)
                await self._replace_dependencies(module, discovered_module)

        await self._session.commit()

    async def _upsert_repository(self, discovered_branch: DiscoveredBranch) -> Repository:
        source = discovered_branch.repository
        result = await self._session.execute(
            select(Repository).where(
                Repository.provider == "github",
                Repository.owner == source.owner,
                Repository.name == source.name,
            )
        )
        repository = result.scalar_one_or_none()

        if repository is None:
            repository = Repository(
                provider="github",
                owner=source.owner,
                name=source.name,
                full_name=source.full_name,
                url=source.url,
            )
            self._session.add(repository)

        repository.default_branch = source.default_branch
        repository.description = source.description
        repository.stars = source.stars
        repository.forks = source.forks
        repository.open_issues = source.open_issues
        repository.license = source.license
        repository.archived = source.archived
        repository.visibility = source.visibility
        repository.last_indexed_at = datetime.now(UTC)

        await self._session.flush()
        return repository

    async def _upsert_branch(
        self, repository: Repository, discovered_branch: DiscoveredBranch
    ) -> Branch:
        source = discovered_branch.branch
        result = await self._session.execute(
            select(Branch).where(
                Branch.repository_id == repository.id,
                Branch.name == source.name,
            )
        )
        branch = result.scalar_one_or_none()

        if branch is None:
            branch = Branch(repository_id=repository.id, name=source.name)
            self._session.add(branch)

        branch.odoo_version = discovered_branch.odoo_version
        branch.commit_sha = source.commit_sha
        branch.is_odoo_version_branch = True
        branch.last_indexed_at = datetime.now(UTC)

        await self._session.flush()
        return branch

    async def _upsert_module(
        self,
        repository: Repository,
        branch: Branch,
        discovered_module: DiscoveredModule,
    ) -> Module:
        result = await self._session.execute(
            select(Module).where(
                Module.repository_id == repository.id,
                Module.branch_id == branch.id,
                Module.technical_name == discovered_module.technical_name,
            )
        )
        module = result.scalar_one_or_none()

        if module is None:
            module = Module(
                repository_id=repository.id,
                branch_id=branch.id,
                technical_name=discovered_module.technical_name,
                path=discovered_module.path,
            )
            self._session.add(module)

        manifest = discovered_module.manifest
        module.odoo_version = discovered_module.odoo_version
        module.path = discovered_module.path
        module.manifest_path = discovered_module.manifest_path
        module.source_url = (
            f"{repository.url}/tree/{discovered_module.branch.name}/{discovered_module.path}"
        )

        if manifest is not None:
            module.display_name = manifest.name
            module.summary = manifest.summary
            module.description = manifest.description
            module.module_version = manifest.version
            module.category = manifest.category
            module.license = manifest.license
            module.license_source = discovered_module.manifest_path if manifest.license else None
            module.author = manifest.author
            module.maintainers = manifest.maintainers
            module.website = manifest.website
            module.installable = manifest.installable
            module.application = manifest.application
            module.auto_install = manifest.auto_install

        await self._session.flush()
        return module

    async def _replace_dependencies(
        self, module: Module, discovered_module: DiscoveredModule
    ) -> None:
        await self._session.execute(delete(Dependency).where(Dependency.module_id == module.id))

        manifest = discovered_module.manifest
        if manifest is None:
            return

        for dependency_name in manifest.depends:
            self._session.add(
                Dependency(
                    module_id=module.id,
                    dependency_name=dependency_name,
                    dependency_type="odoo",
                    is_external=False,
                    source="__manifest__.py:depends",
                )
            )

        for dependency_type, dependency_names in manifest.external_dependencies.items():
            for dependency_name in dependency_names:
                self._session.add(
                    Dependency(
                        module_id=module.id,
                        dependency_name=dependency_name,
                        dependency_type=dependency_type,
                        is_external=True,
                        source="__manifest__.py:external_dependencies",
                    )
                )

