"""Orchestrator for the updated quantitative analysis pipeline.

Runs, in order: preparation of the observation table, descriptive statistics,
paired tests, Spearman correlations, the cost/validity/ranking analysis, the
figures, the Markdown report and the standalone HTML preview.

Run from this folder:

    python run_all.py
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import correlation  # noqa: E402
import cost_report  # noqa: E402
import descriptive_stats  # noqa: E402
import generate_report  # noqa: E402
import paired_tests  # noqa: E402
import plots  # noqa: E402
import prepare_data  # noqa: E402
import render_report_html  # noqa: E402


def main() -> None:
    """Execute every step of the analysis in the required order."""
    steps = [
        ("1/8", "Observation table", prepare_data.main),
        ("2/8", "Descriptive statistics", descriptive_stats.main),
        ("3/8", "Paired tests", paired_tests.main),
        ("4/8", "Spearman correlations", correlation.main),
        ("5/8", "Cost, validity, ranking and election", cost_report.main),
        ("6/8", "Figures", plots.main),
        ("7/8", "Report (Markdown)", generate_report.main),
        ("8/8", "Report (HTML preview)", render_report_html.main),
    ]
    for number, label, function in steps:
        print("\n=== [%s] %s ===" % (number, label))
        function()


if __name__ == "__main__":
    main()
