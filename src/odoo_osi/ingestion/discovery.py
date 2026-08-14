from dataclasses import dataclass, field
from typing import Protocol

from odoo_osi.ingestion.contracts import GitHubBranch, GitHubRepository, GitHubTreeEntry
from odoo_osi.ingestion.module_discovery import discover_module_candidates
from odoo_osi.ingestion.odoo_versions import odoo_version_sort_key, parse_odoo_version_branch
from odoo_osi.parsers.manifest import ManifestParseError, ParsedManifest, parse_manifest


class RepositorySource(Protocol):
    async def get_repository(self, owner: str, repo: str) -> GitHubRepository:
        ...

    async def list_org_repositories(
        self, owner: str, per_page: int = 100
    ) -> list[GitHubRepository]:
        ...

    async def list_branches(self, owner: str, repo: str, per_page: int = 100) -> list[GitHubBranch]:
        ...

    async def get_tree(
        self, owner: str, repo: str, ref: str, recursive: bool = True
    ) -> list[GitHubTreeEntry]:
        ...

    async def get_file_text(self, owner: str, repo: str, ref: str, path: str) -> str:
        ...


@dataclass(frozen=True)
class DiscoveryOptions:
    owner: str = "OCA"
    repository: str | None = None
    repo_limit: int | None = None
    branch_limit_per_repo: int | None = None
    module_limit_per_branch: int | None = None
    odoo_version: str | None = None
    include_archived: bool = False
    parse_manifests: bool = True


@dataclass(frozen=True)
class DiscoveredModule:
    repository: GitHubRepository
    branch: GitHubBranch
    odoo_version: str
    technical_name: str
    path: str
    manifest_path: str
    manifest: ParsedManifest | None
    parse_error: str | None = None


@dataclass(frozen=True)
class DiscoveredBranch:
    repository: GitHubRepository
    branch: GitHubBranch
    odoo_version: str
    modules: list[DiscoveredModule] = field(default_factory=list)


@dataclass(frozen=True)
class DiscoveryError:
    scope: str
    message: str


@dataclass(frozen=True)
class DiscoveryReport:
    owner: str
    repositories_seen: int
    repositories_indexed: int
    branches_indexed: int
    modules_seen: int
    modules_parsed: int
    branches: list[DiscoveredBranch]
    errors: list[DiscoveryError] = field(default_factory=list)


class OcaDiscoveryService:
    def __init__(self, source: RepositorySource) -> None:
        self._source = source

    async def discover(self, options: DiscoveryOptions) -> DiscoveryReport:
        if options.repository is not None:
            try:
                repositories = [
                    await self._source.get_repository(options.owner, options.repository)
                ]
            except Exception as exc:
                return DiscoveryReport(
                    owner=options.owner,
                    repositories_seen=0,
                    repositories_indexed=0,
                    branches_indexed=0,
                    modules_seen=0,
                    modules_parsed=0,
                    branches=[],
                    errors=[
                        DiscoveryError(
                            scope=f"{options.owner}/{options.repository}",
                            message=str(exc),
                        )
                    ],
                )
        else:
            repositories = await self._source.list_org_repositories(options.owner)

        eligible_repositories = [
            repository
            for repository in repositories
            if options.include_archived or not repository.archived
        ]
        if options.repo_limit is not None:
            eligible_repositories = eligible_repositories[: options.repo_limit]

        discovered_branches: list[DiscoveredBranch] = []
        errors: list[DiscoveryError] = []
        modules_seen = 0
        modules_parsed = 0

        for repository in eligible_repositories:
            try:
                branches = await self._source.list_branches(repository.owner, repository.name)
            except Exception as exc:  # pragma: no cover - network edge
                errors.append(DiscoveryError(scope=repository.full_name, message=str(exc)))
                continue

            version_branches = [
                (branch, version)
                for branch in branches
                if (version := parse_odoo_version_branch(branch.name)) is not None
            ]
            if options.odoo_version is not None:
                version_branches = [
                    (branch, version)
                    for branch, version in version_branches
                    if version == options.odoo_version
                ]
            else:
                version_branches = sorted(
                    version_branches,
                    key=lambda item: odoo_version_sort_key(item[1]),
                    reverse=True,
                )

            if options.branch_limit_per_repo is not None:
                version_branches = version_branches[: options.branch_limit_per_repo]

            for branch, odoo_version in version_branches:
                try:
                    tree = await self._source.get_tree(
                        repository.owner, repository.name, branch.commit_sha
                    )
                except Exception as exc:  # pragma: no cover
                    errors.append(
                        DiscoveryError(
                            scope=f"{repository.full_name}:{branch.name}",
                            message=str(exc),
                        )
                    )
                    continue

                candidates = discover_module_candidates(tree)
                if options.module_limit_per_branch is not None:
                    candidates = candidates[: options.module_limit_per_branch]

                modules: list[DiscoveredModule] = []
                for candidate in candidates:
                    modules_seen += 1
                    manifest = None
                    parse_error = None

                    if options.parse_manifests:
                        try:
                            content = await self._source.get_file_text(
                                repository.owner,
                                repository.name,
                                branch.commit_sha,
                                candidate.manifest_path,
                            )
                            manifest = parse_manifest(content)
                            modules_parsed += 1
                        except (ManifestParseError, Exception) as exc:
                            parse_error = str(exc)

                    modules.append(
                        DiscoveredModule(
                            repository=repository,
                            branch=branch,
                            odoo_version=odoo_version,
                            technical_name=candidate.technical_name,
                            path=candidate.path,
                            manifest_path=candidate.manifest_path,
                            manifest=manifest,
                            parse_error=parse_error,
                        )
                    )

                discovered_branches.append(
                    DiscoveredBranch(
                        repository=repository,
                        branch=branch,
                        odoo_version=odoo_version,
                        modules=modules,
                    )
                )

        return DiscoveryReport(
            owner=options.owner,
            repositories_seen=len(repositories),
            repositories_indexed=len(eligible_repositories),
            branches_indexed=len(discovered_branches),
            modules_seen=modules_seen,
            modules_parsed=modules_parsed,
            branches=discovered_branches,
            errors=errors,
        )
