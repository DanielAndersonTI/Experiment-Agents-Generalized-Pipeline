"""Step 1 - Build the observation table of the updated corpus.

The table ``source_all_data.csv`` was extracted from the artifacts of the
``2027-FSE-Report-and-Dates`` tree by ``scan_all.py`` (frozen PDF/TXT parsers of
``Experimento_Multiagente/quantitative_analysis``).  This script only renames the
columns to the layout used by the frozen analysis, so that the remaining scripts
of this folder mirror the frozen pipeline line by line:

    serv_final -> f1_serv      (consolidated proposal, or Proposal A when there
                                is a single proposal)
    inter_final -> f1_inter    (same convention)
    test -> execution          (round 1, 2 or 3 of the cell)

Every other column of the extraction is preserved, including the intermediate
proposals (``serv_a``, ``serv_b``, ``serv_cons``) and the raw YAML verdict.

Run from this folder:

    python prepare_data.py
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pandas as pd  # noqa: E402

from _paths import DATA_CSV, SOURCE_CSV, ensure_output_dirs  # noqa: E402

RENAME = {
    "serv_final": "f1_serv",
    "inter_final": "f1_inter",
    "test": "execution",
}

COLUMNS = [
    "llm",
    "config",
    "execution",
    "system",
    "f1_serv",
    "f1_inter",
    "serv_a",
    "serv_b",
    "serv_cons",
    "inter_a",
    "inter_b",
    "inter_cons",
    "serv_precision",
    "serv_recall",
    "inter_precision",
    "inter_recall",
    "yaml_valid",
    "yaml_valid_raw",
    "total_tokens",
    "duration_ms",
    "total_calls",
    "prompt_tokens",
    "completion_tokens",
    "execution_id",
]


def main() -> None:
    """Write ``data.csv`` in the column layout of the frozen analysis."""
    ensure_output_dirs()
    frame = pd.read_csv(SOURCE_CSV).rename(columns=RENAME)
    frame["config"] = frame["config"].astype(str)
    frame["llm"] = frame["llm"].astype(str)
    frame["execution"] = frame["execution"].astype(int)
    frame = frame[[column for column in COLUMNS if column in frame.columns]]

    frame.to_csv(DATA_CSV, index=False, encoding="utf-8")

    metrics = int(frame[["f1_serv", "f1_inter"]].notna().all(axis=1).sum())
    yaml_known = int(frame["yaml_valid"].notna().sum())
    print("observations: %d" % frame.shape[0])
    print("observations with both F1 metrics: %d" % metrics)
    print("observations with a YAML verdict: %d" % yaml_known)
    print("cells: %d" % frame.groupby(["llm", "config"]).ngroups)
    print("\nwritten: %s" % DATA_CSV)


if __name__ == "__main__":
    main()
