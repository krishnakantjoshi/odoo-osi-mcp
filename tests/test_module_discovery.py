import unittest

from odoo_osi.ingestion.contracts import GitHubTreeEntry
from odoo_osi.ingestion.module_discovery import discover_module_candidates
from odoo_osi.ingestion.source_files import discover_source_file_candidates


class ModuleDiscoveryTests(unittest.TestCase):
    def test_discover_module_candidates_from_manifest_files(self) -> None:
        tree = [
            GitHubTreeEntry(path="purchase_request/__manifest__.py", type="blob", sha="1"),
            GitHubTreeEntry(
                path="purchase_request/models/purchase_request.py",
                type="blob",
                sha="2",
            ),
            GitHubTreeEntry(path="README.md", type="blob", sha="3"),
            GitHubTreeEntry(path="setup/_metapackage/__manifest__.py", type="blob", sha="4"),
        ]

        candidates = discover_module_candidates(tree)

        self.assertEqual(
            [candidate.technical_name for candidate in candidates],
            ["purchase_request", "_metapackage"],
        )
        self.assertEqual(candidates[0].manifest_path, "purchase_request/__manifest__.py")

    def test_discover_source_file_candidates_limits_to_known_source_types(self) -> None:
        tree = [
            GitHubTreeEntry(path="purchase_request/__manifest__.py", type="blob", sha="1"),
            GitHubTreeEntry(
                path="purchase_request/models/purchase_request.py",
                type="blob",
                sha="2",
            ),
            GitHubTreeEntry(
                path="purchase_request/views/purchase_request.xml",
                type="blob",
                sha="3",
            ),
            GitHubTreeEntry(path="purchase_request/static/icon.png", type="blob", sha="4"),
            GitHubTreeEntry(path="other_module/models/other.py", type="blob", sha="5"),
        ]

        candidates = discover_source_file_candidates(tree, "purchase_request")

        self.assertEqual(
            [candidate.path for candidate in candidates],
            [
                "purchase_request/__manifest__.py",
                "purchase_request/models/purchase_request.py",
                "purchase_request/views/purchase_request.xml",
            ],
        )
