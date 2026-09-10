"""Step 3 - Paired statistical tests.

For each LLM and each configuration contrast (C0 vs C1, C1 vs C2, C1 vs C3)
this script runs a Wilcoxon signed-rank test and computes Cliff's delta, both
for ``f1_serv`` and ``f1_inter``. The eight systems are used as paired units:
the value of a system in a configuration is the mean over its three executions,
which reduces the stochastic noise of individual runs (n = 8 pairs per test).

Run from the repository root:

    python Experimento_Multiagente/quantitative_analysis/paired_tests.py
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from scipy import stats  # noqa: E402

from _paths import OUTPUT_DIR, ensure_output_dirs  # noqa: E402
from _source_scan import LLMS  # noqa: E402

DATA_CSV = os.path.join(OUTPUT_DIR, "data.csv")
WILCOXON_CSV = os.path.join(OUTPUT_DIR, "wilcoxon.csv")

METRICS = ["f1_serv", "f1_inter"]
COMPARISONS = [("C0", "C1"), ("C1", "C2"), ("C1", "C3")]


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


def main() -> None:
    """Run the paired tests and write ``wilcoxon.csv``."""
    ensure_output_dirs()
    frame = pd.read_csv(DATA_CSV)
    records = []

    for llm in LLMS:
        subset = frame[frame["llm"] == llm]
        for config_a, config_b in COMPARISONS:
            for metric in METRICS:
                pivot = (
                    subset[subset["config"].isin([config_a, config_b])]
                    .groupby(["system", "config"])[metric]
                    .mean()
                    .unstack("config")
                )
                paired = pivot[[config_a, config_b]].dropna()
                values_a = paired[config_a].to_numpy(dtype=float)
                values_b = paired[config_b].to_numpy(dtype=float)
                differences = values_a - values_b
                nonzero = int(np.count_nonzero(differences))

                statistic = np.nan
                p_value = np.nan
                if nonzero > 0:
                    test = stats.wilcoxon(values_a, values_b, zero_method="wilcox")
                    statistic = float(test.statistic)
                    p_value = float(test.pvalue)

                delta = cliffs_delta(values_a, values_b)
                records.append({
                    "metric": metric,
                    "comparison": "%s vs %s" % (config_a, config_b),
                    "llm": llm,
                    "n_pairs": int(paired.shape[0]),
                    "n_nonzero": nonzero,
                    "statistic": round(statistic, 4) if nonzero > 0 else np.nan,
                    "p_value": round(p_value, 4) if nonzero > 0 else np.nan,
                    "cliffs_delta": round(delta, 4),
                    "effect": effect_magnitude(delta),
                })

    result = pd.DataFrame(records)
    result.to_csv(WILCOXON_CSV, index=False, encoding="utf-8")
    print(result.to_string(index=False))
    print("\nwritten: %s" % WILCOXON_CSV)


if __name__ == "__main__":
    main()
