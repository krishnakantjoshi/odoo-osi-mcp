import unittest

from odoo_osi.search.coverage import (
    _coverage_status,
    _external_catalog_benchmark,
    _github_discovery_benchmark,
    _percent,
)


class CoverageReportTests(unittest.TestCase):
    def test_percent_handles_zero_total(self) -> None:
        self.assertIsNone(_percent(1, 0))

    def test_percent_rounds_to_two_decimals(self) -> None:
        self.assertEqual(_percent(1, 3), 33.33)

    def test_coverage_status_reports_partial_source_index(self) -> None:
        self.assertEqual(_coverage_status(10, 4), "partial_source_index")

    def test_external_catalog_benchmark_reports_gap(self) -> None:
        benchmark = _external_catalog_benchmark(indexed_modules=125, catalog_module_estimate=20000)

        self.assertEqual(benchmark["estimated_total_modules"], 20000)
        self.assertEqual(benchmark["remaining_modules"], 19875)
        self.assertEqual(benchmark["coverage_percent"], 0.62)

    def test_github_discovery_benchmark_uses_latest_full_discovery_counter(self) -> None:
        benchmark = _github_discovery_benchmark(
            indexed_repositories=8,
            latest_full_discovery={"counters": {"repositories_seen": 100}},
        )

        self.assertEqual(benchmark["estimated_total_repositories"], 100)
        self.assertEqual(benchmark["remaining_repositories"], 92)
        self.assertEqual(benchmark["coverage_percent"], 8.0)

