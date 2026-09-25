"""Step 5 - Cost, validity, precision/recall, C4 proposals and cell ranking.

This module extends the frozen pipeline (which produced descriptive statistics,
paired tests and correlations only) with the analyses the discussion of the
updated corpus needs:

* ``cost.csv``            - token and wall-clock cost of every cell, plus the
                            mean number of LLM calls per execution;
* ``yaml.csv``            - well-formed specifications per cell, in the
                            normalised and in the raw variant, and the metric
                            coverage of the cell;
* ``precision_recall.csv``- mean precision and recall of services and
                            interactions, which separate over-specification from
                            under-specification;
* ``proposals_c4.csv``    - the two proposals of C4 (A = architect, B = second
                            generalist architect) and what the consolidation kept;
* ``per_system.csv``      - per-system means of both metrics, per cell;
* ``ranking.csv``         - the cost-benefit table: combined F1, tokens per
                            execution and F1 points per 1000 tokens;
* ``results.json``        - every number the Markdown report cites, in one file.

Run from this folder:

    python cost_report.py
"""

from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from _paths import DATA_CSV, OUTPUT_DIR, ensure_output_dirs  # noqa: E402
from _source_scan import CONFIGS, LLMS, PURPOSE, SYSTEMS  # noqa: E402
from _source_scan import AGENTS  # noqa: E402
from paired_tests import cliffs_delta, effect_magnitude, paired_values  # noqa: E402

METRICS = ["f1_serv", "f1_inter"]
RESULTS_JSON = os.path.join(OUTPUT_DIR, "results.json")


def cell_key(llm: str, config: str) -> str:
    """Return the canonical key of a (model, configuration) cell."""
    return "%s|%s" % (llm, config)


def rounded(value) -> float:
    """Round a scalar to four decimals, propagating ``NaN``."""
    if value is None:
        return float("nan")
    if isinstance(value, float) and np.isnan(value):
        return float("nan")
    return round(float(value), 4)


def safe_mean(series: pd.Series) -> float:
    """Mean of the non-null values of a series."""
    clean = series.dropna()
    return rounded(clean.mean()) if clean.size else float("nan")


def build_descriptive(frame: pd.DataFrame) -> dict:
    """Return the descriptive statistics of both metrics for every cell."""
    descriptive = {metric: {} for metric in METRICS}
    for config in CONFIGS:
        for llm in LLMS:
            subset = frame[(frame["config"] == config) & (frame["llm"] == llm)]
            for metric in METRICS:
                values = subset[metric].dropna()
                descriptive[metric][cell_key(llm, config)] = {
                    "n": int(values.size),
                    "n_missing": int(subset.shape[0] - values.size),
                    "mean": safe_mean(values),
                    "std": rounded(values.std(ddof=1)) if values.size > 1 else float("nan"),
                    "min": rounded(values.min()) if values.size else float("nan"),
                    "max": rounded(values.max()) if values.size else float("nan"),
                }
    return descriptive


def build_cost(frame: pd.DataFrame) -> dict:
    """Return the cost profile of every cell.

    A few executions recorded no budget: they carry neither metrics nor tokens
    (Claude C4 round 3), while their YAML verdict survived the run.  They are
    counted in the inventory but excluded from the cost averages, so that a cell
    is priced on the executions that actually recorded a consumption.  ``n_zero``
    makes that adjustment explicit.
    """
    cost = {}
    for config in CONFIGS:
        for llm in LLMS:
            subset = frame[(frame["config"] == config) & (frame["llm"] == llm)]
            budget = subset[subset["total_tokens"].fillna(0) > 0]
            tokens = budget["total_tokens"].dropna()
            duration = budget["duration_ms"].dropna()
            calls = budget["total_calls"].dropna()
            cost[cell_key(llm, config)] = {
                "config": config,
                "llm": llm,
                "agents": AGENTS[config],
                "purpose": PURPOSE[config],
                "n_executions": int(subset.shape[0]),
                "n_budget": int(tokens.size),
                "n_zero": int(subset.shape[0] - tokens.size),
                "mean_tokens": safe_mean(tokens),
                "median_tokens": rounded(tokens.median()) if tokens.size else float("nan"),
                "min_tokens": rounded(tokens.min()) if tokens.size else float("nan"),
                "max_tokens": rounded(tokens.max()) if tokens.size else float("nan"),
                "total_tokens": rounded(tokens.sum()) if tokens.size else float("nan"),
                "mean_duration_ms": safe_mean(duration),
                "mean_calls": safe_mean(calls),
            }
    return cost


def build_yaml(frame: pd.DataFrame) -> dict:
    """Return the YAML verdicts and the metric coverage of every cell."""
    yaml_summary = {}
    for config in CONFIGS:
        for llm in LLMS:
            subset = frame[(frame["config"] == config) & (frame["llm"] == llm)]
            valid = subset["yaml_valid"].dropna()
            raw = subset["yaml_valid_raw"].dropna()
            yaml_summary[cell_key(llm, config)] = {
                "n_executions": int(subset.shape[0]),
                "n_valid_normalised": int(valid.sum()) if valid.size else 0,
                "n_valid_raw": int(raw.sum()) if raw.size else 0,
                "n_labeled": int(valid.size),
                "n_metrics": int(subset[METRICS].notna().all(axis=1).sum()),
            }
    return yaml_summary


def build_precision(frame: pd.DataFrame) -> dict:
    """Return the mean precision and recall of every cell."""
    precision = {}
    for config in CONFIGS:
        for llm in LLMS:
            subset = frame[(frame["config"] == config) & (frame["llm"] == llm)]
            precision[cell_key(llm, config)] = {
                "serv_precision": safe_mean(subset["serv_precision"]),
                "serv_recall": safe_mean(subset["serv_recall"]),
                "inter_precision": safe_mean(subset["inter_precision"]),
                "inter_recall": safe_mean(subset["inter_recall"]),
            }
    return precision


def build_proposals(frame: pd.DataFrame) -> dict:
    """Return the C4 proposal comparison for each model."""
    proposals = {}
    subset = frame[frame["config"] == "C4"]
    for llm in LLMS:
        block = subset[subset["llm"] == llm]
        entry = {}
        for stem in ["serv", "inter"]:
            first = safe_mean(block["%s_a" % stem])
            second = safe_mean(block["%s_b" % stem])
            final = safe_mean(block["%s_cons" % stem])
            entry[stem] = {
                "n_a": int(block["%s_a" % stem].notna().sum()),
                "n_b": int(block["%s_b" % stem].notna().sum()),
                "a": first,
                "b": second,
                "final": final,
                "gap_a_b": rounded(first - second),
                "final_minus_a": rounded(final - first),
                "final_minus_b": rounded(final - second),
            }
        proposals[llm] = entry
    return proposals


def build_per_system(frame: pd.DataFrame) -> dict:
    """Return the per-system means of both metrics, per cell."""
    per_system = {}
    for llm in LLMS:
        per_system[llm] = {}
        block = frame[frame["llm"] == llm]
        for metric in METRICS:
            means = (
                block.groupby(["system", "config"])[metric]
                .mean()
                .unstack("config")
                .reindex(SYSTEMS)
            )
            per_system[llm][metric] = {
                system: {
                    config: (rounded(means.loc[system, config])
                             if config in means.columns and pd.notna(means.loc[system, config])
                             else float("nan"))
                    for config in CONFIGS
                }
                for system in SYSTEMS
            }
    return per_system


def build_ranking(descriptive: dict, cost: dict, yaml_summary: dict) -> list:
    """Return the cost-benefit table: quality, cost and quality per 1000 tokens."""
    cheapest = min(entry["mean_tokens"] for entry in cost.values())
    combined_quality = {}
    for key in cost:
        combined_quality[key] = (
            descriptive["f1_serv"][key]["mean"] + descriptive["f1_inter"][key]["mean"]
        ) / 2.0
    best_combined = max(combined_quality.values())

    rows = []
    for key, entry in cost.items():
        rows.append({
            "cell": key,
            "config": entry["config"],
            "llm": entry["llm"],
            "agents": entry["agents"],
            "mean_serv": descriptive["f1_serv"][key]["mean"],
            "mean_inter": descriptive["f1_inter"][key]["mean"],
            "combined": rounded(combined_quality[key]),
            "mean_tokens": entry["mean_tokens"],
            "mean_duration_ms": entry["mean_duration_ms"],
            "mean_calls": entry["mean_calls"],
            "yaml_ok": yaml_summary[key]["n_valid_normalised"],
            "n_metrics": yaml_summary[key]["n_metrics"],
            "cost_index": rounded(entry["mean_tokens"] / cheapest),
            "quality_per_ktoken": rounded(combined_quality[key] / (entry["mean_tokens"] / 1000.0)),
            "quality_index": rounded(combined_quality[key] / best_combined),
        })
    rows.sort(key=lambda row: row["quality_per_ktoken"], reverse=True)
    return rows


def pareto_front(rows: list) -> list:
    """Return the cells that no other cell dominates in (quality, cost)."""
    front = []
    for row in rows:
        dominated = any(
            other is not row
            and other["combined"] >= row["combined"]
            and other["mean_tokens"] <= row["mean_tokens"]
            and (other["combined"] > row["combined"] or other["mean_tokens"] < row["mean_tokens"])
            for other in rows
        )
        row["pareto"] = not dominated
        if not dominated:
            front.append(row["cell"])
    return front


def system_vector(frame: pd.DataFrame, key: str, metric: str) -> pd.Series:
    """Return the per-system mean of a metric for one cell.

    Args:
        frame: Full observation table.
        key: Cell key in the ``model|config`` form.
        metric: Metric column to average.

    Returns:
        Series indexed by system.
    """
    llm, config = key.split("|")
    return (
        frame[(frame["llm"] == llm) & (frame["config"] == config)]
        .groupby("system")[metric]
        .mean()
    )


def build_election(frame: pd.DataFrame, rows: list) -> dict:
    """Elect the best cost-benefit cell of the corpus.

    The criterion is explicit and reproducible: the quality reference is the cell
    with the highest mean F1 of interactions; a cell is *equivalent* to the
    reference when Cliff's delta between the two per-system vectors is negligible
    (|delta| < 0.147, the threshold of the frozen analysis); among the equivalent
    cells the election falls on the cheapest one in tokens.
    """
    ordered = sorted(rows, key=lambda row: row["mean_inter"], reverse=True)
    reference = ordered[0]
    reference_vector = system_vector(frame, reference["cell"], "f1_inter")

    candidates = []
    for row in ordered:
        vector = system_vector(frame, row["cell"], "f1_inter")
        joined = pd.concat(
            [vector, reference_vector], axis=1, keys=["cell", "ref"]
        ).dropna()
        delta = cliffs_delta(
            joined["cell"].to_numpy(dtype=float), joined["ref"].to_numpy(dtype=float)
        )
        candidates.append({
            "cell": row["cell"],
            "mean_inter": row["mean_inter"],
            "mean_serv": row["mean_serv"],
            "combined": row["combined"],
            "mean_tokens": row["mean_tokens"],
            "delta_vs_reference": rounded(delta),
            "effect_vs_reference": effect_magnitude(delta),
            "equivalent": abs(delta) < 0.147,
            "n_pairs": int(joined.shape[0]),
        })

    equivalent = [candidate for candidate in candidates if candidate["equivalent"]]
    elected = min(equivalent, key=lambda candidate: candidate["mean_tokens"]) if equivalent else {
        "cell": reference["cell"],
        "mean_serv": reference["mean_serv"],
        "mean_inter": reference["mean_inter"],
        "mean_tokens": reference["mean_tokens"],
        "combined": reference["combined"],
        "delta_vs_reference": 0.0,
        "effect_vs_reference": "negligible",
    }

    per_model_multiagent = {}
    for llm in LLMS:
        multiagent = [row for row in rows if row["llm"] == llm and row["config"] != "C0"]
        best = max(multiagent, key=lambda row: row["mean_inter"])
        single = next(row for row in rows if row["llm"] == llm and row["config"] == "C0")
        values_a, values_b = paired_values(
            frame, llm, single["config"], best["config"], "f1_inter"
        )
        delta = cliffs_delta(values_a, values_b)
        delta_serv = cliffs_delta(*paired_values(
            frame, llm, single["config"], best["config"], "f1_serv"
        ))
        per_model_multiagent[llm] = {
            "single_cell": single["cell"],
            "single_inter": single["mean_inter"],
            "single_serv": single["mean_serv"],
            "single_tokens": single["mean_tokens"],
            "best_multiagent_cell": best["cell"],
            "best_multiagent_config": best["config"],
            "best_multiagent_inter": best["mean_inter"],
            "best_multiagent_serv": best["mean_serv"],
            "best_multiagent_tokens": best["mean_tokens"],
            "delta_inter_single_minus_best": rounded(delta),
            "effect_inter": effect_magnitude(delta),
            "delta_serv_single_minus_best": rounded(delta_serv),
            "effect_serv": effect_magnitude(delta_serv),
            "token_ratio": rounded(best["mean_tokens"] / single["mean_tokens"]),
            "inter_gain": rounded(best["mean_inter"] - single["mean_inter"]),
            "serv_gain": rounded(best["mean_serv"] - single["mean_serv"]),
        }

    return {
        "reference_cell": reference["cell"],
        "reference_inter": reference["mean_inter"],
        "reference_serv": reference["mean_serv"],
        "reference_tokens": reference["mean_tokens"],
        "elected_cell": elected["cell"],
        "elected_combined": elected["combined"],
        "elected_serv": elected["mean_serv"],
        "elected_inter": elected["mean_inter"],
        "elected_tokens": elected["mean_tokens"],
        "elected_delta_vs_reference": elected["delta_vs_reference"],
        "elected_effect_vs_reference": elected["effect_vs_reference"],
        "elected_token_saving_pct": rounded(
            100.0 * (1.0 - elected["mean_tokens"] / reference["mean_tokens"])
        ),
        "elected_inter_saving_pct": rounded(
            100.0 * (1.0 - elected["mean_inter"] / reference["mean_inter"])
        ),
        "n_equivalent": len(equivalent),
        "candidates": candidates,
        "per_model_multiagent": per_model_multiagent,
    }


def build_extremes(rows: list) -> dict:
    """Return the best, worst, cheapest and most expensive cells of the corpus."""
    best_serv = max(rows, key=lambda row: row["mean_serv"])
    worst_serv = min(rows, key=lambda row: row["mean_serv"])
    best_inter = max(rows, key=lambda row: row["mean_inter"])
    worst_inter = min(rows, key=lambda row: row["mean_inter"])
    cheapest = min(rows, key=lambda row: row["mean_tokens"])
    priciest = max(rows, key=lambda row: row["mean_tokens"])
    return {
        "best_serv": best_serv["cell"], "best_serv_value": best_serv["mean_serv"],
        "worst_serv": worst_serv["cell"], "worst_serv_value": worst_serv["mean_serv"],
        "best_inter": best_inter["cell"], "best_inter_value": best_inter["mean_inter"],
        "worst_inter": worst_inter["cell"], "worst_inter_value": worst_inter["mean_inter"],
        "cheapest": cheapest["cell"], "cheapest_tokens": cheapest["mean_tokens"],
        "most_expensive": priciest["cell"], "most_expensive_tokens": priciest["mean_tokens"],
        "spread_tokens": rounded(priciest["mean_tokens"] / cheapest["mean_tokens"]),
    }


def build_corpus(frame: pd.DataFrame) -> dict:
    """Return the corpus-level inventory numbers.

    The token and duration figures rest on the executions that recorded a budget
    (see :func:`build_cost`); the count of executions without budget is reported
    separately.
    """
    complete = frame[METRICS].notna().all(axis=1)
    budget = frame[frame["total_tokens"].fillna(0) > 0]
    return {
        "n_observations": int(frame.shape[0]),
        "n_metrics": int(complete.sum()),
        "n_yaml": int(frame["yaml_valid"].notna().sum()),
        "n_metric_observations": int(frame["f1_serv"].notna().sum()),
        "n_cells": int(frame.groupby(["llm", "config"]).ngroups),
        "n_rounds": int(frame["execution"].max()),
        "n_systems": int(frame["system"].nunique()),
        "n_models": int(frame["llm"].nunique()),
        "n_configs": int(frame["config"].nunique()),
        "metrics_missing": int(frame.shape[0] - complete.sum()),
        "n_no_budget": int(frame.shape[0] - budget.shape[0]),
        "n_budget": int(budget.shape[0]),
        "tokens_min": rounded(budget["total_tokens"].min()),
        "tokens_max": rounded(budget["total_tokens"].max()),
        "tokens_mean": safe_mean(budget["total_tokens"]),
        "tokens_median": rounded(budget["total_tokens"].median()),
        "tokens_total": rounded(budget["total_tokens"].sum()),
        "duration_mean_ms": safe_mean(budget["duration_ms"]),
        "duration_total_ms": rounded(budget["duration_ms"].sum()),
        "calls_mean": safe_mean(budget["total_calls"]),
        "calls_total": rounded(budget["total_calls"].sum()),
        "first_run": str(frame["execution_id"].min())[:8],
        "last_run": str(frame["execution_id"].max())[:8],
        "yaml_raw_valid": int(frame["yaml_valid_raw"].fillna(0).sum()),
        "yaml_normalised_valid": int(frame["yaml_valid"].fillna(0).sum()),
        "cells_with_missing_metrics": sorted({
            cell_key(row.llm, row.config) for row in frame[~complete].itertuples()
        }),
        "missing_metric_systems": sorted(frame.loc[~complete, "system"].unique().tolist()),
        "missing_metric_rounds": sorted(frame.loc[~complete, "execution"].unique().tolist()),
    }


def build_model_summary(frame: pd.DataFrame) -> dict:
    """Return the pooled behaviour of each model over the five configurations."""
    summary = {}
    for llm in LLMS:
        block = frame[frame["llm"] == llm]
        budget = block[block["total_tokens"].fillna(0) > 0]
        serv = block["f1_serv"].dropna()
        inter = block["f1_inter"].dropna()
        valid = block["yaml_valid"].dropna()
        best_inter = max(
            (key for key in [cell_key(llm, config) for config in CONFIGS]),
            key=lambda key: cell_mean(frame, key, "f1_inter"),
        )
        best_serv = max(
            (key for key in [cell_key(llm, config) for config in CONFIGS]),
            key=lambda key: cell_mean(frame, key, "f1_serv"),
        )
        summary[llm] = {
            "n_obs": int(block.shape[0]),
            "n_metrics": int(block[METRICS].notna().all(axis=1).sum()),
            "mean_serv": safe_mean(serv),
            "mean_inter": safe_mean(inter),
            "std_inter": rounded(inter.std(ddof=1)) if inter.size > 1 else float("nan"),
            "min_inter": rounded(inter.min()) if inter.size else float("nan"),
            "max_inter": rounded(inter.max()) if inter.size else float("nan"),
            "mean_tokens": safe_mean(budget["total_tokens"]),
            "median_tokens": rounded(budget["total_tokens"].median()),
            "mean_duration_ms": safe_mean(budget["duration_ms"]),
            "mean_calls": safe_mean(budget["total_calls"]),
            "yaml_valid_rate": rounded(valid.mean()) if valid.size else float("nan"),
            "yaml_raw_rate": safe_mean(block["yaml_valid_raw"]),
            "best_inter_cell": best_inter,
            "best_inter_value": cell_mean(frame, best_inter, "f1_inter"),
            "best_serv_cell": best_serv,
            "best_serv_value": cell_mean(frame, best_serv, "f1_serv"),
        }
    return summary


def cell_mean(frame: pd.DataFrame, key: str, metric: str) -> float:
    """Mean of a metric inside one cell."""
    llm, config = key.split("|")
    block = frame[(frame["llm"] == llm) & (frame["config"] == config)]
    return safe_mean(block[metric])


def build_knee(rows: list) -> dict:
    """Return the knee of the Pareto frontier in normalised (cost, quality) space.

    The knee is the frontier cell that lies farthest from the chord joining the
    cheapest and the best cell of the frontier, which is the usual reading of the
    "best compromise" of a cost-benefit curve.
    """
    front = [row for row in rows if row.get("pareto")]
    if len(front) < 3:
        return {"knee": None, "front": [row["cell"] for row in front]}
    cheapest = min(front, key=lambda row: row["mean_tokens"])
    best = max(front, key=lambda row: row["combined"])
    cost_span = best["mean_tokens"] - cheapest["mean_tokens"]
    quality_span = best["combined"] - cheapest["combined"]
    distances = []
    for row in front:
        cost_norm = (row["mean_tokens"] - cheapest["mean_tokens"]) / cost_span
        quality_norm = (row["combined"] - cheapest["combined"]) / quality_span
        # Distance to the chord quality = cost (both normalised to [0, 1]).
        distances.append((abs(quality_norm - cost_norm) / (2 ** 0.5), row))
    distances.sort(key=lambda item: item[0], reverse=True)
    knee = distances[0][1]
    return {
        "knee": knee["cell"],
        "knee_distance": rounded(distances[0][0]),
        "knee_combined": knee["combined"],
        "knee_tokens": knee["mean_tokens"],
        "front": sorted(row["cell"] for row in front),
    }


def build_alternatives(rows: list, yaml_summary: dict) -> list:
    """Return the election that each quality floor would produce.

    The floors are expressed on the combined F1 (mean of the two metrics) and are
    always combined with a hard requirement of at least 90% of well-formed
    specifications, which any automated downstream use of the architecture needs.
    """
    alternatives = []
    for floor in [0.95, 0.92, 0.90, 0.85, None]:
        eligible = [
            row for row in rows
            if (floor is None or row["combined"] >= floor)
            and yaml_summary[row["cell"]]["n_valid_normalised"]
            >= 0.9 * yaml_summary[row["cell"]]["n_labeled"]
        ]
        if not eligible:
            continue
        winner = min(eligible, key=lambda row: row["mean_tokens"])
        alternatives.append({
            "floor": floor,
            "n_eligible": len(eligible),
            "cell": winner["cell"],
            "combined": winner["combined"],
            "mean_serv": winner["mean_serv"],
            "mean_inter": winner["mean_inter"],
            "mean_tokens": winner["mean_tokens"],
            "quality_index": winner["quality_index"],
            "cost_index": winner["cost_index"],
            "quality_per_ktoken": winner["quality_per_ktoken"],
            "yaml_ok": yaml_summary[winner["cell"]]["n_valid_normalised"],
        })
    return alternatives


def build_interaction_alternatives(rows: list, yaml_summary: dict) -> list:
    """Return the election that each interaction-F1 floor would produce.

    Services saturate (they are invariant across configurations), so the axis that
    discriminates the architectures is the F1 of interactions.  The floors below
    are therefore expressed on that metric, always combined with the 90%
    well-formed specification requirement.
    """
    alternatives = []
    for floor in [0.92, 0.90, 0.87, 0.85, 0.80, None]:
        eligible = [
            row for row in rows
            if (floor is None or row["mean_inter"] >= floor)
            and yaml_summary[row["cell"]]["n_valid_normalised"]
            >= 0.9 * yaml_summary[row["cell"]]["n_labeled"]
        ]
        if not eligible:
            continue
        winner = min(eligible, key=lambda row: row["mean_tokens"])
        alternatives.append({
            "floor": floor,
            "n_eligible": len(eligible),
            "cell": winner["cell"],
            "mean_inter": winner["mean_inter"],
            "mean_serv": winner["mean_serv"],
            "mean_tokens": winner["mean_tokens"],
            "cost_index": winner["cost_index"],
            "quality_index": winner["quality_index"],
            "yaml_ok": yaml_summary[winner["cell"]]["n_valid_normalised"],
        })
    return alternatives


def write_tables(payload: dict) -> None:
    """Write the auxiliary CSV files of the analysis."""
    pd.DataFrame(payload["ranking"]).to_csv(
        os.path.join(OUTPUT_DIR, "ranking.csv"), index=False, encoding="utf-8"
    )
    pd.DataFrame([
        {"cell": key, **value} for key, value in payload["cost"].items()
    ]).to_csv(os.path.join(OUTPUT_DIR, "cost.csv"), index=False, encoding="utf-8")
    pd.DataFrame([
        {"cell": key, **value} for key, value in payload["yaml"].items()
    ]).to_csv(os.path.join(OUTPUT_DIR, "yaml.csv"), index=False, encoding="utf-8")
    pd.DataFrame([
        {"cell": key, **value} for key, value in payload["precision"].items()
    ]).to_csv(os.path.join(OUTPUT_DIR, "precision_recall.csv"), index=False, encoding="utf-8")

    proposal_rows = []
    for llm, entry in payload["proposals"].items():
        for stem in ["serv", "inter"]:
            proposal_rows.append({"llm": llm, "metric": stem, **entry[stem]})
    pd.DataFrame(proposal_rows).to_csv(
        os.path.join(OUTPUT_DIR, "proposals_c4.csv"), index=False, encoding="utf-8"
    )

    system_rows = []
    for llm in LLMS:
        for system in SYSTEMS:
            for config in CONFIGS:
                system_rows.append({
                    "llm": llm,
                    "system": system,
                    "config": config,
                    "f1_serv": payload["per_system"][llm]["f1_serv"][system][config],
                    "f1_inter": payload["per_system"][llm]["f1_inter"][system][config],
                })
    pd.DataFrame(system_rows).to_csv(
        os.path.join(OUTPUT_DIR, "per_system.csv"), index=False, encoding="utf-8"
    )


def main() -> None:
    """Write every derived table and the consolidated ``results.json``."""
    ensure_output_dirs()
    frame = pd.read_csv(DATA_CSV)

    descriptive = build_descriptive(frame)
    cost = build_cost(frame)
    yaml_summary = build_yaml(frame)
    rows = build_ranking(descriptive, cost, yaml_summary)
    front = pareto_front(rows)

    wilcoxon = pd.read_csv(os.path.join(OUTPUT_DIR, "wilcoxon.csv"))
    spearman = pd.read_csv(os.path.join(OUTPUT_DIR, "spearman.csv"))
    significant = wilcoxon[wilcoxon["p_value"] < 0.05]

    payload = {
        "corpus": build_corpus(frame),
        "descriptive": descriptive,
        "cost": cost,
        "yaml": yaml_summary,
        "precision": build_precision(frame),
        "proposals": build_proposals(frame),
        "per_system": build_per_system(frame),
        "models": build_model_summary(frame),
        "ranking": rows,
        "pareto_front": front,
        "knee": build_knee(rows),
        "alternatives": build_alternatives(rows, yaml_summary),
        "alternatives_interactions": build_interaction_alternatives(rows, yaml_summary),
        "election": build_election(frame, rows),
        "extremes": build_extremes(rows),
        "wilcoxon": wilcoxon.to_dict(orient="records"),
        "spearman": spearman.to_dict(orient="records"),
        "significance": {
            "n_contrasts": int(wilcoxon.shape[0]),
            "n_significant": int(significant.shape[0]),
            "contrasts": significant.to_dict(orient="records"),
        },
    }

    with open(RESULTS_JSON, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=1, ensure_ascii=False)
    write_tables(payload)

    election = payload["election"]
    print("reference cell : %s (inter %s)" % (
        election["reference_cell"], election["reference_inter"]))
    print("elected cell   : %s (serv %s | inter %s | %s tokens)" % (
        election["elected_cell"], election["elected_serv"],
        election["elected_inter"], election["elected_tokens"]))
    print("equivalent     : %s" % ", ".join(
        candidate["cell"] for candidate in election["candidates"] if candidate["equivalent"]))
    print("pareto front   : %s" % ", ".join(payload["pareto_front"]))
    print("knee           : %s (distance %s)" % (
        payload["knee"]["knee"], payload["knee"]["knee_distance"]))
    print("significant    : %d of %d contrasts" % (
        payload["significance"]["n_significant"], payload["significance"]["n_contrasts"]))
    print("\nwritten: %s" % RESULTS_JSON)


if __name__ == "__main__":
    main()
