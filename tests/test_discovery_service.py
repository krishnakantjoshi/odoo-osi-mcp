import unittest

from odoo_osi.ingestion.contracts import GitHubBranch, GitHubRepository, GitHubTreeEntry
from odoo_osi.ingestion.discovery import DiscoveryOptions, OcaDiscoveryService


class FakeSource:
    async def get_repository(self, owner: str, repo: str) -> GitHubRepository:
        if repo != "purchase-workflow":
            raise ValueError("not found")
        return _purchase_workflow_repository(owner)

    async def list_org_repositories(
        self, owner: str, per_page: int = 100
    ) -> list[GitHubRepository]:
        return [_purchase_workflow_repository(owner)]

    async def list_branches(
        self, owner: str, repo: str, per_page: int = 100
    ) -> list[GitHubBranch]:
        return [
            GitHubBranch(name="18.0", commit_sha="abc"),
            GitHubBranch(name="main", commit_sha="def"),
        ]

    async def get_tree(
        self, owner: str, repo: str, ref: str, recursive: bool = True
    ) -> list[GitHubTreeEntry]:
        return [
            GitHubTreeEntry(path="purchase_request/__manifest__.py", type="blob", sha="1"),
            GitHubTreeEntry(
                path="purchase_request/models/purchase_request.py",
                type="blob",
                sha="2",
            ),
        ]

    async def get_file_text(self, owner: str, repo: str, ref: str, path: str) -> str:
        return """
{
    "name": "Purchase Request",
    "version": "18.0.1.0.0",
    "license": "AGPL-3",
    "depends": ["purchase", "mail"],
}
"""


class DiscoveryServiceTests(unittest.IsolatedAsyncioTestCase):
    async def test_discovery_finds_version_branch_modules_and_parses_manifest(self) -> None:
        service = OcaDiscoveryService(FakeSource())

        report = await service.discover(DiscoveryOptions(owner="OCA"))

        self.assertEqual(report.repositories_seen, 1)
        self.assertEqual(report.repositories_indexed, 1)
        self.assertEqual(report.branches_indexed, 1)
        self.assertEqual(report.modules_seen, 1)
        self.assertEqual(report.modules_parsed, 1)
        self.assertEqual(report.branches[0].odoo_version, "18.0")
        self.assertEqual(report.branches[0].modules[0].technical_name, "purchase_request")
        self.assertEqual(report.branches[0].modules[0].manifest.license, "AGPL-3")

    async def test_discovery_can_target_repository(self) -> None:
        service = OcaDiscoveryService(FakeSource())

        report = await service.discover(
            DiscoveryOptions(owner="OCA", repository="purchase-workflow")
        )

        self.assertEqual(report.repositories_indexed, 1)
        self.assertEqual(report.branches[0].repository.name, "purchase-workflow")

    async def test_discovery_target_repository_can_miss(self) -> None:
        service = OcaDiscoveryService(FakeSource())

        report = await service.discover(
            DiscoveryOptions(owner="OCA", repository="stock-logistics-workflow")
        )

        self.assertEqual(report.repositories_seen, 0)
        self.assertEqual(report.repositories_indexed, 0)
        self.assertEqual(report.branches_indexed, 0)
        self.assertEqual(report.errors[0].scope, "OCA/stock-logistics-workflow")


def _purchase_workflow_repository(owner: str) -> GitHubRepository:
    return GitHubRepository(
        owner=owner,
        name="purchase-workflow",
        full_name=f"{owner}/purchase-workflow",
        url="https://github.com/OCA/purchase-workflow",
        default_branch="18.0",
        description="Purchase workflow addons",
        stars=100,
        forks=50,
        open_issues=10,
        license="AGPL-3.0",
        archived=False,
        visibility="public",
    )
