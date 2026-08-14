import unittest

from odoo_osi.parsers.python_symbols import parse_python_symbols


class PythonSymbolTests(unittest.TestCase):
    def test_parse_python_symbols_extracts_odoo_model_and_inherit(self) -> None:
        symbols = parse_python_symbols(
            '''
from odoo import models


class PurchaseRequest(models.Model):
    _name = "purchase.request"
    _description = "Purchase Request"


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"
'''
        )

        self.assertEqual(len(symbols), 2)
        self.assertEqual(symbols[0].name, "PurchaseRequest")
        self.assertEqual(symbols[0].odoo_model, "purchase.request")
        self.assertEqual(symbols[1].inherited_model, "purchase.order")
