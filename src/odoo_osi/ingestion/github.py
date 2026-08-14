from typing import Any

import httpx

from odoo_osi.ingestion.contracts import (
    GitHubBranch,
    GitHubCodeSearchItem,
    GitHubRepository,
    GitHubTreeEntry,
)


class GitHubClient:
    """Small GitHub REST client for public repository indexing."""

    def __init__(
        self,
        token: str | None = None,
        base_url: str = "https://api.github.com",
        timeout: float = 30.0,
    ) -> None:
        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "odoo-osi-indexer",
        }
        if token:
            headers["Authorization"] = f"Bearer {token}"

        self._client = httpx.AsyncClient(base_url=base_url, headers=headers, timeout=timeout)

    async def close(self) -> None:
        await self._client.aclose()

    async def get_repository(self, owner: str, repo: str) -> GitHubRepository:
        response = await self._client.get(f"/repos/{owner}/{repo}")
        response.raise_for_status()
        return self._parse_repository(response.json())

    async def list_org_repositories(
        self, owner: str, per_page: int = 100
    ) -> list[GitHubRepository]:
        repositories: list[GitHubRepository] = []
        page = 1

        while True:
            response = await self._client.get(
                f"/orgs/{owner}/repos",
                params={"type": "public", "sort": "full_name", "per_page": per_page, "page": page},
            )
            response.raise_for_status()
            payload = response.json()
            if not payload:
                break

            repositories.extend(self._parse_repository(item) for item in payload)
            page += 1

        return repositories

    async def list_branches(self, owner: str, repo: str, per_page: int = 100) -> list[GitHubBranch]:
        branches: list[GitHubBranch] = []
        page = 1

        while True:
            response = await self._client.get(
                f"/repos/{owner}/{repo}/branches",
                params={"per_page": per_page, "page": page},
            )
            response.raise_for_status()
            payload = response.json()
            if not payload:
                break

            branches.extend(
                GitHubBranch(name=item["name"], commit_sha=item["commit"]["sha"])
                for item in payload
            )
            page += 1

        return branches

    async def get_tree(
        self, owner: str, repo: str, ref: str, recursive: bool = True
    ) -> list[GitHubTreeEntry]:
        response = await self._client.get(
            f"/repos/{owner}/{repo}/git/trees/{ref}",
            params={"recursive": "1" if recursive else "0"},
        )
        response.raise_for_status()
        payload = response.json()
        return [
            GitHubTreeEntry(
                path=item["path"],
                type=item["type"],
                sha=item["sha"],
                size=item.get("size"),
            )
            for item in payload.get("tree", [])
        ]

    async def get_file_text(self, owner: str, repo: str, ref: str, path: str) -> str:
        response = await self._client.get(
            f"/repos/{owner}/{repo}/contents/{path}",
            params={"ref": ref},
            headers={"Accept": "application/vnd.github.raw"},
        )
        response.raise_for_status()
        return response.text

    async def search_code(self, query: str, per_page: int = 10) -> list[GitHubCodeSearchItem]:
        response = await self._client.get(
            "/search/code",
            params={"q": query, "per_page": per_page},
        )
        response.raise_for_status()
        return [
            GitHubCodeSearchItem(
                repository_owner=item["repository"]["owner"]["login"],
                repository_name=item["repository"]["name"],
                repository_full_name=item["repository"]["full_name"],
                path=item["path"],
                html_url=item["html_url"],
            )
            for item in response.json().get("items", [])
        ]

    def _parse_repository(self, item: dict[str, Any]) -> GitHubRepository:
        owner = item["owner"]["login"]
        license_payload = item.get("license") or {}
        return GitHubRepository(
            owner=owner,
            name=item["name"],
            full_name=item["full_name"],
            url=item["html_url"],
            default_branch=item["default_branch"],
            description=item.get("description"),
            stars=item.get("stargazers_count", 0),
            forks=item.get("forks_count", 0),
            open_issues=item.get("open_issues_count", 0),
            license=license_payload.get("spdx_id"),
            archived=item.get("archived", False),
            visibility=item.get("visibility", "public"),
        )
