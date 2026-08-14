import unittest

from odoo_osi.ingestion.odoo_versions import (
    is_odoo_version_branch,
    odoo_version_sort_key,
    parse_odoo_version_branch,
)


class OdooVersionTests(unittest.TestCase):
    def test_parse_odoo_version_branch_accepts_oca_version_branches(self) -> None:
        self.assertEqual(parse_odoo_version_branch("18.0"), "18.0")
        self.assertEqual(parse_odoo_version_branch("9.0"), "9.0")
        self.assertTrue(is_odoo_version_branch("17.0"))

    def test_parse_odoo_version_branch_rejects_non_version_branches(self) -> None:
        self.assertIsNone(parse_odoo_version_branch("main"))
        self.assertIsNone(parse_odoo_version_branch("18.0-mig-product"))
        self.assertFalse(is_odoo_version_branch("master"))

    def test_odoo_version_sort_key_orders_numerically(self) -> None:
        versions = ["9.0", "18.0", "16.0"]
        self.assertEqual(sorted(versions, key=odoo_version_sort_key), ["9.0", "16.0", "18.0"])
