"""Step 2 - Descriptive statistics.

For every (config x llm) group and for both metrics (``f1_serv`` and
``f1_inter``) this script reports the mean, median, standard deviation and a
95% confidence interval obtained with a non-parametric bootstrap (1000
resamples), following the protocol defined in the analysis plan.

Run from the repository root:

    python Experimento_Multiagente/quantitative_analysis/descriptive_stats.py
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from _paths import OUTPUT_DIR, ensure_output_dirs  # noqa: E402
from _source_scan import CONFIGS, LLMS  # noqa: E402

DATA_CSV = os.path.join(OUTPUT_DIR, "data.csv")
DESCRIPTIVE_CSV = os.path.join(OUTPUT_DIR, "descriptive.csv")

METRICS = ["f1_serv", "f1_inter"]
BOOTSTRAP_ROUNDS = 1000
RANDOM_SEED = 42


def bootstrap_ci(values: np.ndarray, rounds: int = BOOTSTRAP_ROUNDS, seed: int = RANDOM_SEED):
    """Compute a percentile bootstrap 95% confidence interval for the mean.

    Args:
        values: One-dimensional array of observations.
        rounds: Number of bootstrap resamples.
        seed: Seed for reproducibility.

    Returns:
        Tuple ``(low, high)`` with the 2.5th and 97.5th percentiles.
    """
    if values.size == 0:
        return (np.nan, np.nan)
    rng = np.random.default_rng(seed)
    samples = rng.choice(values, size=(rounds, values.size), replace=True)
    means = samples.mean(axis=1)
    return float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5))


def main() -> None:
    """Compute the descriptive table and write ``descriptive.csv``."""
    ensure_output_dirs()
    frame = pd.read_csv(DATA_CSV)
    records = []

    for config in CONFIGS:
        for llm in LLMS:
            subset = frame[(frame["config"] == config) & (frame["llm"] == llm)]
            for metric in METRICS:
                values = subset[metric].dropna().to_numpy(dtype=float)
                low, high = bootstrap_ci(values)
                records.append({
                    "metric": metric,
                    "config": config,
                    "llm": llm,
                    "n": int(values.size),
                    "mean": round(float(values.mean()), 4) if values.size else np.nan,
                    "median": round(float(np.median(values)), 4) if values.size else np.nan,
                    "std": round(float(values.std(ddof=1)), 4) if values.size > 1 else np.nan,
                    "ci95_low": round(low, 4),
                    "ci95_high": round(high, 4),
                })

    result = pd.DataFrame(records)
    result.to_csv(DESCRIPTIVE_CSV, index=False, encoding="utf-8")
    print(result.to_string(index=False))
    print("\nwritten: %s" % DESCRIPTIVE_CSV)


if __name__ == "__main__":
    main()
