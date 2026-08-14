import unittest

from odoo_osi.parsers.manifest import ManifestParseError, parse_manifest


class ManifestParserTests(unittest.TestCase):
    def test_parse_manifest_extracts_authoritative_module_metadata(self) -> None:
        manifest = parse_manifest(
            """
{
    "name": "Purchase Request",
    "summary": "Use this module to have notification of requirements of materials.",
    "version": "18.0.1.0.0",
    "license": "AGPL-3",
    "depends": ["purchase", "mail"],
    "external_dependencies": {"python": ["openpyxl"]},
    "maintainers": ["maintainer-a"],
    "installable": True,
}
"""
        )

        self.assertEqual(manifest.name, "Purchase Request")
        self.assertEqual(manifest.version, "18.0.1.0.0")
        self.assertEqual(manifest.license, "AGPL-3")
        self.assertEqual(manifest.depends, ["purchase", "mail"])
        self.assertEqual(manifest.external_dependencies, {"python": ["openpyxl"]})
        self.assertEqual(manifest.maintainers, ["maintainer-a"])
        self.assertTrue(manifest.installable)

    def test_parse_manifest_rejects_non_literal_python(self) -> None:
        with self.assertRaises(ManifestParseError):
            parse_manifest("dict(name='not allowed here')")
