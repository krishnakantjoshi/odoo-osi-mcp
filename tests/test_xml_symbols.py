import unittest

from odoo_osi.parsers.xml_symbols import parse_xml_symbols


class XmlSymbolTests(unittest.TestCase):
    def test_parse_xml_symbols_extracts_views_and_menus(self) -> None:
        symbols = parse_xml_symbols(
            """
<odoo>
  <record id="purchase_order_form_inherit" model="ir.ui.view">
    <field name="name">purchase.order.form.inherit</field>
    <field name="inherit_id" ref="purchase.purchase_order_form"/>
  </record>
  <menuitem
    id="menu_purchase_request"
    name="Purchase Requests"
    parent="purchase.menu_purchase_root"
  />
</odoo>
"""
        )

        self.assertEqual(symbols[0].symbol_type, "view")
        self.assertEqual(symbols[0].xml_id, "purchase_order_form_inherit")
        self.assertEqual(symbols[0].parent_xml_id, "purchase.purchase_order_form")
        self.assertEqual(symbols[1].symbol_type, "menuitem")
        self.assertEqual(symbols[1].name, "Purchase Requests")
