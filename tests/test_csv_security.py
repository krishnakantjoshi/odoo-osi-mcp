import unittest

from odoo_osi.parsers.csv_security import parse_access_rules


class CsvSecurityParserTests(unittest.TestCase):
    def test_parse_access_rules_extracts_model_group_and_permissions(self) -> None:
        rules = parse_access_rules(
            "id,name,model_id:id,group_id:id,perm_read,perm_write,perm_create,perm_unlink\n"
            "access_purchase_request_user,purchase request user,model_purchase_request,"
            "purchase.group_purchase_user,1,1,1,0\n"
        )

        self.assertEqual(len(rules), 1)
        self.assertEqual(rules[0].xml_id, "access_purchase_request_user")
        self.assertEqual(rules[0].odoo_model, "purchase.request")
        self.assertEqual(rules[0].group_xml_id, "purchase.group_purchase_user")
        self.assertTrue(rules[0].permissions["read"])
        self.assertFalse(rules[0].permissions["unlink"])
