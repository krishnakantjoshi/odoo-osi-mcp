import unittest

from odoo_osi.mcp.server import create_mcp_server
from odoo_osi.mcp.services import _license_warnings


class McpServerTests(unittest.TestCase):
    def test_create_mcp_server_registers_expected_tools(self) -> None:
        server = create_mcp_server()

        tool_names = {tool.name for tool in server._tool_manager.list_tools()}

        self.assertIn("search_oca_modules", tool_names)
        self.assertIn("find_solution", tool_names)
        self.assertIn("search_oca_code", tool_names)
        self.assertIn("get_oca_module", tool_names)
        self.assertIn("get_module_dependencies", tool_names)
        self.assertIn("get_coverage_report", tool_names)

    def test_license_warnings_include_agpl_notice(self) -> None:
        warnings = _license_warnings("AGPL-3")

        self.assertEqual(len(warnings), 1)
        self.assertIn("AGPL", warnings[0])

    def test_license_warnings_include_missing_license_notice(self) -> None:
        warnings = _license_warnings(None)

        self.assertEqual(len(warnings), 1)
        self.assertIn("missing", warnings[0])
