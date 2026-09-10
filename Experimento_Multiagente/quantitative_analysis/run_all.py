"""Orchestrator for the whole quantitative analysis pipeline.

Runs, in order: text caching, data extraction, descriptive statistics, paired
tests, Spearman correlations, figure generation, Markdown report generation and
the standalone HTML preview.

Run from the repository root:

    python Experimento_Multiagente/quantitative_analysis/run_all.py
    python Experimento_Multiagente/quantitative_analysis/run_all.py --refresh-cache

The ``--refresh-cache`` flag forces the re-extraction of the text from every
PDF, which is only needed when the source artifacts change.
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import cache_texts  # noqa: E402
import correlation  # noqa: E402
import descriptive_stats  # noqa: E402
import extract_data  # noqa: E402
import generate_report  # noqa: E402
import paired_tests  # noqa: E402
import plots  # noqa: E402
import render_report_html  # noqa: E402


def main() -> None:
    """Execute every analysis step in the required order."""
    refresh = "--refresh-cache" in sys.argv
    if refresh or not os.path.isfile(cache_texts.CACHE_PATH):
        print("=== [0/6] Caching source texts ===")
        cache_texts.main()

    steps = [
        ("1/7", "Extracting data", extract_data.main),
        ("2/7", "Descriptive statistics", descriptive_stats.main),
        ("3/7", "Paired tests", paired_tests.main),
        ("4/7", "Spearman correlations", correlation.main),
        ("5/7", "Figures", plots.main),
        ("6/7", "Report (Markdown)", generate_report.main),
        ("7/7", "Report (HTML preview)", render_report_html.main),
    ]
    for number, label, function in steps:
        print("\n=== [%s] %s ===" % (number, label))
        function()


if __name__ == "__main__":
    main()
