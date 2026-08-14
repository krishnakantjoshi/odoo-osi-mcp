from dataclasses import dataclass


@dataclass(frozen=True)
class GitHubRepository:
    owner: str
    name: str
    full_name: str
    url: str
    default_branch: str
    description: str | None
    stars: int
    forks: int
    open_issues: int
    license: str | None
    archived: bool
    visibility: str


@dataclass(frozen=True)
class GitHubBranch:
    name: str
    commit_sha: str


@dataclass(frozen=True)
class GitHubTreeEntry:
    path: str
    type: str
    sha: str
    size: int | None = None


@dataclass(frozen=True)
class GitHubCodeSearchItem:
    repository_owner: str
    repository_name: str
    repository_full_name: str
    path: str
    html_url: str
