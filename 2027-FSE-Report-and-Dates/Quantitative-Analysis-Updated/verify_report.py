"""Verification of the report and of the analysis outputs.

Checks that the Markdown report and the standalone HTML are complete and
self-consistent: every figure referenced by the report exists on disk, every
figure is embedded in the HTML, no placeholder or ``nan`` survived, and the
derived tables carry the expected number of records.

Run from this folder:

    python verify_report.py
"""

from __future__ import annotations

import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from _paths import FIGURES_DIR, OUTPUT_DIR  # noqa: E402

REPORT_MD = os.path.join(OUTPUT_DIR, "report.md")
REPORT_HTML = os.path.join(OUTPUT_DIR, "report.html")
RESULTS_JSON = os.path.join(OUTPUT_DIR, "results.json")

LINK = re.compile(r"!\[[^\]]*\]\(([^)]+)\)")
FORBIDDEN = ["nan", "None", "TODO", "%s", "%d", "%%"]
TABLES = [
    ("descriptive.csv", 30),
    ("wilcoxon.csv", 60),
    ("spearman.csv", 18),
    ("ranking.csv", 15),
    ("cost.csv", 15),
    ("yaml.csv", 15),
    ("precision_recall.csv", 15),
    ("per_system.csv", 120),
    ("proposals_c4.csv", 6),
]


def main() -> None:
    """Run every verification and exit with a non-zero code on failure."""
    failures = []

    with open(REPORT_MD, encoding="utf-8") as handle:
        markdown = handle.read()
    with open(REPORT_HTML, encoding="utf-8") as handle:
        html = handle.read()

    links = LINK.findall(markdown)
    for link in links:
        path = os.path.join(OUTPUT_DIR, link.replace("/", os.sep))
        if not os.path.isfile(path):
            failures.append("missing figure: %s" % link)
    print("figures referenced by report.md : %d" % len(links))
    print("figures present in figures/    : %d" % len(os.listdir(FIGURES_DIR)))
    if len(links) != len(os.listdir(FIGURES_DIR)):
        failures.append("the report does not reference every figure")

    embedded = html.count("data:image/png;base64,")
    print("figures embedded in report.html: %d" % embedded)
    if embedded != len(links):
        failures.append("not every figure is embedded in the HTML")
    if 'src="figures/' in html:
        failures.append("the HTML still points to a relative figure path")

    for token in FORBIDDEN:
        if token in markdown:
            failures.append("forbidden token in report.md: %r" % token)

    with open(RESULTS_JSON, encoding="utf-8") as handle:
        payload = json.load(handle)
    expected_cells = payload["corpus"]["n_cells"]
    if len(payload["ranking"]) != expected_cells:
        failures.append("ranking.csv does not cover every cell")
    if len(payload["wilcoxon"]) != 60:
        failures.append("wilcoxon.csv does not hold 60 contrasts")
    election = payload["election"]
    print("elected cell                   : %s" % election["elected_cell"])
    print("equivalent cells               : %d" % election["n_equivalent"])

    for name, rows in TABLES:
        path = os.path.join(OUTPUT_DIR, name)
        if not os.path.isfile(path):
            failures.append("missing table: %s" % name)
            continue
        with open(path, encoding="utf-8") as handle:
            count = len([line for line in handle.read().splitlines() if line.strip()]) - 1
        status = "ok" if count == rows else "expected %d" % rows
        print("%-22s rows: %3d  %s" % (name, count, status))
        if count != rows:
            failures.append("%s has %d rows, expected %d" % (name, count, rows))

    print("\nreport.md   : %d lines, %.1f KB" % (
        markdown.count("\n"), os.path.getsize(REPORT_MD) / 1024.0))
    print("report.html : %.1f KB" % (os.path.getsize(REPORT_HTML) / 1024.0))

    if failures:
        print("\nFAILED:")
        for failure in failures:
            print(" - %s" % failure)
        sys.exit(1)
    print("\nall checks passed")


if __name__ == "__main__":
    main()
