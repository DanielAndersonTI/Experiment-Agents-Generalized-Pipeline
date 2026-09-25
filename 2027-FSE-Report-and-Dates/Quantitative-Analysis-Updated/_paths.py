"""Shared path configuration for the updated quantitative analysis scripts.

This folder is a parallel pipeline of ``Experimento_Multiagente/quantitative_analysis``.
It reuses the same statistical procedures (bootstrap with a fixed seed, Wilcoxon
signed-rank test with Cliff's delta, Spearman rank correlation) but works on the
whole 2027-FSE corpus - three models and five configurations - which is why the
scripts live next to their own ``data.csv`` instead of re-scanning the PDFs.
"""

from __future__ import annotations

import os

# Repository root: .../DAVINCI
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(os.path.dirname(_SCRIPT_DIR))

#: Directory holding the experimental artifacts of the FSE 2027 submission.
SOURCE_DIR = os.path.join(REPO_ROOT, "2027-FSE-Report-and-Dates")

#: Directory where the CSV files, figures and report are written.
OUTPUT_DIR = os.path.join(SOURCE_DIR, "Quantitative-Analysis-Updated")

#: Sub-directory for the generated figures.
FIGURES_DIR = os.path.join(OUTPUT_DIR, "figures")

#: Observation table extracted from the artifacts by ``scan_all.py``.
SOURCE_CSV = os.path.join(OUTPUT_DIR, "source_all_data.csv")

#: Observation table in the column layout of the frozen analysis.
DATA_CSV = os.path.join(OUTPUT_DIR, "data.csv")


def ensure_output_dirs() -> None:
    """Create the output directory tree when it does not exist yet."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(FIGURES_DIR, exist_ok=True)
