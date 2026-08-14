import unittest

from odoo_osi.parsers.readme import parse_readme_sections


class ReadmeParserTests(unittest.TestCase):
    def test_parse_markdown_sections(self) -> None:
        sections = parse_readme_sections(
            """
# Purchase Request

Manage internal purchase requests.

## Usage

Create a request and submit it for approval.

## Configuration

Enable validation tiers.
"""
        )

        self.assertEqual(
            [section.title for section in sections],
            ["Purchase Request", "Usage", "Configuration"],
        )
        self.assertEqual(sections[1].section_type, "usage")
        self.assertIn("approval", sections[1].body)

    def test_parse_rst_sections(self) -> None:
        sections = parse_readme_sections(
            """
Known issues
============

No known issues.
"""
        )

        self.assertEqual(sections[0].title, "Known issues")
        self.assertEqual(sections[0].section_type, "known_issues")
