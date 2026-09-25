"""Step 4 - Spearman rank correlations.

Computes the Spearman correlation between the token cost and (i) the service F1,
(ii) the interaction F1 and (iii) the YAML validity, both on the pooled corpus
(all models and configurations) and inside each configuration.

Run from this folder:

    python correlation.py
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from scipy import stats  # noqa: E402

from _paths import DATA_CSV, OUTPUT_DIR, ensure_output_dirs  # noqa: E402
from _source_scan import CONFIGS  # noqa: E402

SPEARMAN_CSV = os.path.join(OUTPUT_DIR, "spearman.csv")

PAIRS = [("total_tokens", "f1_serv"), ("total_tokens", "f1_inter"), ("total_tokens", "yaml_valid")]


def spearman(frame: pd.DataFrame, x: str, y: str, scope: str) -> dict:
    """Compute the Spearman correlation for one pair of variables.

    Args:
        frame: Subset of the observations to analyse.
        x: Name of the independent variable column.
        y: Name of the dependent variable column.
        scope: Label describing the subset (e.g. ``"Global"`` or ``"C1"``).

    Returns:
        A dictionary ready to be written as a CSV row.
    """
    clean = frame[[x, y]].dropna()
    rho, p_value = np.nan, np.nan
    # Spearman is undefined when one of the variables has no rank variation.
    if clean.shape[0] > 2 and clean[x].nunique() > 1 and clean[y].nunique() > 1:
        result = stats.spearmanr(clean[x], clean[y])
        rho, p_value = float(result.statistic), float(result.pvalue)
    return {
        "x": x,
        "y": y,
        "scope": scope,
        "n": int(clean.shape[0]),
        "rho": round(rho, 4) if not np.isnan(rho) else np.nan,
        "p_value": round(p_value, 4) if not np.isnan(p_value) else np.nan,
    }


def main() -> None:
    """Compute the correlations and write ``spearman.csv``."""
    ensure_output_dirs()
    frame = pd.read_csv(DATA_CSV)
    records = []

    for x, y in PAIRS:
        records.append(spearman(frame, x, y, "Global"))
        for config in CONFIGS:
            records.append(spearman(frame[frame["config"] == config], x, y, config))

    result = pd.DataFrame(records)
    result.to_csv(SPEARMAN_CSV, index=False, encoding="utf-8")
    print(result.to_string(index=False))
    print("\nwritten: %s" % SPEARMAN_CSV)


if __name__ == "__main__":
    main()
