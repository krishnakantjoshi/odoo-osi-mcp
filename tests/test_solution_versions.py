import unittest

from odoo_osi.search.solutions import (
    SolutionCandidate,
    SourceEvidence,
    _needs_live_fallback,
    _select_candidates,
    _version_assessment,
)


class SolutionVersionTests(unittest.TestCase):
    def test_older_version_is_migration_candidate(self) -> None:
        assessment = _version_assessment("15.0", "18.0")

        self.assertEqual(assessment.status, "older_version_migration_candidate")
        self.assertEqual(assessment.migration_effort, "medium")
        self.assertLess(assessment.confidence_adjustment, 0)
        self.assertIn("migration", " ".join(assessment.guidance).lower())
        self.assertIn("not a drop-in", assessment.warnings[0])

    def test_exact_version_gets_positive_signal(self) -> None:
        assessment = _version_assessment("18.0", "18.0")

        self.assertEqual(assessment.status, "exact_match")
        self.assertGreater(assessment.confidence_adjustment, 0)
        self.assertEqual(assessment.migration_effort, None)

    def test_selection_keeps_one_cross_version_candidate(self) -> None:
        exact_a = _candidate("exact_a", "exact_match", 0.9)
        exact_b = _candidate("exact_b", "exact_match", 0.8)
        migration = _candidate("migration", "older_version_migration_candidate", 0.4)

        selected = _select_candidates(
            [exact_a, exact_b, migration],
            limit=2,
            target_odoo_version="18.0",
        )

        self.assertEqual([candidate.module for candidate in selected], ["exact_a", "migration"])

    def test_weak_local_result_needs_live_fallback(self) -> None:
        candidate = _candidate("nearby_module", "exact_match", 0.6)

        self.assertTrue(_needs_live_fallback([candidate], "Account Reconcile Oca"))


def _candidate(module: str, version_status: str, confidence: float) -> SolutionCandidate:
    return SolutionCandidate(
        repository="OCA/test",
        module=module,
        odoo_version="18.0" if version_status == "exact_match" else "15.0",
        evidence_level="indexed",
        summary=None,
        license=None,
        dependencies=[],
        source_url=None,
        target_odoo_version="18.0",
        version_status=version_status,
        migration_effort=None,
        migration_guidance=[],
        indexing_guidance=[],
        confidence=confidence,
        why_matched=[],
        warnings=[],
        evidence=SourceEvidence(
            indexed_source_files=0,
            indexed_symbols=0,
            indexed_search_documents=0,
            readme_sections=0,
            security_access_rules=0,
        ),
    )
