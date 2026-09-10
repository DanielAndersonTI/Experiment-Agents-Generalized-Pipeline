"""Shared path configuration for the quantitative analysis scripts."""

from __future__ import annotations

import os

# Repository root: .../Experiment-Agents-Generalized-Pipeline-FSE-2026
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(os.path.dirname(_SCRIPT_DIR))

#: Directory holding the experimental artifacts (source data).
SOURCE_DIR = os.path.join(REPO_ROOT, "2027-FSE-Report-and-Dates")

#: Directory where the CSV files, figures and report are written.
OUTPUT_DIR = os.path.join(SOURCE_DIR, "Quantitative-Analysis")

#: Sub-directory for the generated figures.
FIGURES_DIR = os.path.join(OUTPUT_DIR, "figures")


def ensure_output_dirs() -> None:
    """Create the output directory tree when it does not exist yet."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(FIGURES_DIR, exist_ok=True)
