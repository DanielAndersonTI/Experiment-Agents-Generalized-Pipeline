"""Step 3 - Paired statistical tests over every configuration contrast.

For each of the three models and each of the ten configuration contrasts
(C0..C4 pairwise) this script runs a Wilcoxon signed-rank test and computes
Cliff's delta, both for ``f1_serv`` and ``f1_inter``.

The pairing unit is the **system**: the value of a system in a configuration is
the mean over the rounds of that system, which keeps the pairing valid and avoids
pseudo-replication (n = 8 pairs per test).  Zero-different pairs are discarded
from the statistic (``zero_method="wilcox"``), which is the convention of the
frozen analysis, and the test is two-sided.

Run from this folder:

    python paired_tests.py
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from scipy import stats  # noqa: E402

from _paths import DATA_CSV, OUTPUT_DIR, ensure_output_dirs  # noqa: E402
from _source_scan import COMPARISONS, LLMS  # noqa: E402

WILCOXON_CSV = os.path.join(OUTPUT_DIR, "wilcoxon.csv")

METRICS = ["f1_serv", "f1_inter"]


def cliffs_delta(group_a: np.ndarray, group_b: np.ndarray) -> float:
    """Compute Cliff's delta effect size between two paired samples.

    Args:
        group_a: Values of the first configuration (per system).
        group_b: Values of the second configuration (per system).

    Returns:
        Cliff's delta in ``[-1, 1]``. Positive values mean that ``group_a``
        tends to be larger than ``group_b``.
    """
    differences = group_a[:, None] - group_b[None, :]
    return float((np.sign(differences)).sum() / differences.size)


def effect_magnitude(delta: float) -> str:
    """Classify a Cliff's delta value using the usual thresholds.

    Args:
        delta: Cliff's delta value.

    Returns:
        One of ``"negligible"``, ``"small"``, ``"medium"`` or ``"large"``.
    """
    magnitude = abs(delta)
    if magnitude < 0.147:
        return "negligible"
    if magnitude < 0.330:
        return "small"
    if magnitude < 0.474:
        return "medium"
    return "large"


def paired_values(frame: pd.DataFrame, llm: str, config_a: str, config_b: str, metric: str):
    """Return the per-system paired vectors of two configurations of one model.

    Args:
        frame: Full observation table.
        llm: Model to filter.
        config_a: First configuration.
        config_b: Second configuration.
        metric: Metric column to use.

    Returns:
        Tuple ``(values_a, values_b)`` with one entry per subject system.
    """
    subset = frame[(frame["llm"] == llm) & (frame["config"].isin([config_a, config_b]))]
    pivot = subset.groupby(["system", "config"])[metric].mean().unstack("config")
    paired = pivot[[config_a, config_b]].dropna()
    return paired[config_a].to_numpy(dtype=float), paired[config_b].to_numpy(dtype=float)


def main() -> None:
    """Run the paired tests and write ``wilcoxon.csv``."""
    ensure_output_dirs()
    frame = pd.read_csv(DATA_CSV)
    records = []

    for llm in LLMS:
        for config_a, config_b in COMPARISONS:
            for metric in METRICS:
                values_a, values_b = paired_values(frame, llm, config_a, config_b, metric)
                differences = values_a - values_b
                nonzero = int(np.count_nonzero(differences))

                statistic = np.nan
                p_value = np.nan
                if nonzero > 0:
                    test = stats.wilcoxon(values_a, values_b, zero_method="wilcox")
                    statistic = float(test.statistic)
                    p_value = float(test.pvalue)

                delta = cliffs_delta(values_a, values_b) if values_a.size else np.nan
                records.append({
                    "metric": metric,
                    "comparison": "%s vs %s" % (config_a, config_b),
                    "config_a": config_a,
                    "config_b": config_b,
                    "llm": llm,
                    "n_pairs": int(values_a.size),
                    "n_nonzero": nonzero,
                    "statistic": round(statistic, 4) if nonzero > 0 else np.nan,
                    "p_value": round(p_value, 4) if nonzero > 0 else np.nan,
                    "cliffs_delta": round(delta, 4) if not np.isnan(delta) else np.nan,
                    "effect": effect_magnitude(delta) if not np.isnan(delta) else "n/a",
                })

    result = pd.DataFrame(records)
    result.to_csv(WILCOXON_CSV, index=False, encoding="utf-8")
    significant = result[(result["p_value"] < 0.05)]
    print(result.to_string(index=False))
    print("\ncontrasts: %d | p < 0.05: %d" % (result.shape[0], significant.shape[0]))
    print("\nwritten: %s" % WILCOXON_CSV)


if __name__ == "__main__":
    main()
