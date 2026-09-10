"""Step 1 - Data extraction.

Builds ``data.csv`` with one row per (system, config, llm, execution):

    system, config, llm, execution,
    f1_serv, f1_inter, yaml_valid, total_tokens, duration_ms

* ``f1_serv`` / ``f1_inter`` come from the "Consolidated" row of the metrics
  report (falling back to "Proposal A" for the single-proposal configurations
  C0 and C3).
* ``yaml_valid`` is 1 when the normalized YAML specification loads with
  ``yaml.safe_load`` (see ``_source_scan.normalize_pdf_yaml``).
* ``total_tokens`` and ``duration_ms`` come from the execution tracer JSON.

Run from the repository root:

    python Experimento_Multiagente/quantitative_analysis/extract_data.py
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pandas as pd  # noqa: E402

from _paths import SOURCE_DIR, OUTPUT_DIR, ensure_output_dirs  # noqa: E402
from _source_scan import (  # noqa: E402
    CANONICAL_SYSTEMS,
    CONFIGS,
    LLMS,
    discover_bundles,
    load_metadata_mapped,
    parse_metrics,
    yaml_validity,
)

DATA_CSV = os.path.join(OUTPUT_DIR, "data.csv")


def consolidated_value(metrics: dict, system: str, section: str):
    """Return the consolidated F1 for a system, with a Proposal A fallback.

    Args:
        metrics: Mapping ``system -> {section::proposal -> f1}``.
        system: Canonical system name.
        section: Either ``"services"`` or ``"interactions"``.

    Returns:
        The F1 score as ``float`` or ``None`` when it could not be parsed.
    """
    values = metrics.get(system, {})
    for proposal in ("Consolidated", "Proposal A"):
        key = "%s::%s" % (section, proposal)
        if key in values:
            return values[key]
    return None


def build_rows() -> list:
    """Parse every artifact bundle and return the flattened observation rows."""
    rows = []
    for bundle in discover_bundles(SOURCE_DIR):
        metrics = parse_metrics(bundle.metrics_file)
        validity = yaml_validity(bundle.yalm_file)
        metadata = load_metadata_mapped(bundle.metadata_file)
        for system in CANONICAL_SYSTEMS:
            meta = metadata.get(system, {})
            rows.append({
                "system": system,
                "config": bundle.config,
                "llm": bundle.llm,
                "execution": int(bundle.test),
                "f1_serv": consolidated_value(metrics, system, "services"),
                "f1_inter": consolidated_value(metrics, system, "interactions"),
                "yaml_valid": validity.get(system, 0),
                "total_tokens": meta.get("total_tokens"),
                "duration_ms": meta.get("duration_ms"),
            })
    return rows


def main() -> None:
    """Extract the observations and write ``data.csv``."""
    ensure_output_dirs()
    rows = build_rows()
    frame = pd.DataFrame(rows)
    frame = frame.sort_values(["llm", "config", "execution", "system"]).reset_index(drop=True)
    frame.to_csv(DATA_CSV, index=False, encoding="utf-8")

    expected = len(LLMS) * len(CONFIGS) * 3 * len(CANONICAL_SYSTEMS)
    print("rows written : %d (expected %d)" % (len(frame), expected))
    print("missing F1   : %d" % int(frame["f1_serv"].isna().sum() + frame["f1_inter"].isna().sum()))
    print("missing meta : %d" % int(frame["total_tokens"].isna().sum() + frame["duration_ms"].isna().sum()))
    print("yaml valid   : %d/%d" % (int(frame["yaml_valid"].sum()), len(frame)))
    print("written      : %s" % DATA_CSV)


if __name__ == "__main__":
    main()
