import unittest

from odoo_osi.search.fallback import _candidate_terms
from odoo_osi.search.modules import _query_tokens


class FallbackTermTests(unittest.TestCase):
    def test_candidate_terms_normalize_account_reconcilation_request(self) -> None:
        terms = _candidate_terms(
            "i need account reconcilation feature. i am using odoo community version 18"
        )

        self.assertIn("account_reconcile_oca", terms)
        self.assertIn("account_reconcile", terms)
        self.assertIn("reconcile", terms)

    def test_query_tokens_expand_reconcilation_typo(self) -> None:
        tokens = _query_tokens("account reconcilation")

        self.assertIn("reconciliation", tokens)
        self.assertIn("reconcile", tokens)
        self.assertIn("reconcile_oca", tokens)
