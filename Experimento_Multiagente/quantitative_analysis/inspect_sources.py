"""Step 0 - Source verification.

Scans the experimental artifact tree and reports, for every (LLM, config, test)
bundle, which artifacts are present, how many systems were parsed from the
metrics table, whether a "Consolidated" row exists and whether the YAML
specification is syntactically valid.

Run from the repository root:

    python Experimento_Multiagente/quantitative_analysis/inspect_sources.py
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import yaml  # noqa: E402

from _source_scan import (  # noqa: E402
    CANONICAL_SYSTEMS,
    discover_bundles,
    load_json_metadata,
    normalize_system,
    parse_metrics,
    split_yaml_systems,
)

BASE_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "2027-FSE-Report-and-Dates",
)


def yaml_is_valid(text: str) -> bool:
    """Return ``True`` when ``text`` loads with ``yaml.safe_load``."""
    if not text.strip():
        return False
    try:
        yaml.safe_load(text)
        return True
    except Exception:
        return False


def main() -> None:
    """Print a verification report for every artifact bundle."""
    print("Base directory: %s" % BASE_DIR)
    print("=" * 100)
    bundles = discover_bundles(BASE_DIR)
    problems = []

    for bundle in bundles:
        label = "%s/%s/Test-%s" % (bundle.llm, bundle.config, bundle.test)
        metrics = parse_metrics(bundle.metrics_file)
        metadata = load_json_metadata(bundle.metadata_file)
        yaml_blocks = split_yaml_systems(bundle.yalm_file)

        serv_systems = {s for s, v in metrics.items() if any(k.startswith("services::") for k in v)}
        inter_systems = {s for s, v in metrics.items() if any(k.startswith("interactions::") for k in v)}
        consolidated = {
            s
            for s, v in metrics.items()
            if "services::Consolidated" in v and "interactions::Consolidated" in v
        }
        # The legacy TXT variant has no explicit "Consolidated" row.
        consolidated_fallback = {
            s
            for s, v in metrics.items()
            if "services::Proposal A" in v and "interactions::Proposal A" in v
        }
        meta_systems = {normalize_system(str(row.get("system", ""))) for row in metadata}
        yaml_valid = sum(1 for block in yaml_blocks.values() for _ in [block] if yaml_is_valid(block))

        print("\n%s" % label)
        print("  files      : metrics=%s | yalm=%s | metadata=%s | extra=%s" % (
            os.path.basename(bundle.metrics_file) if bundle.metrics_file else "MISSING",
            os.path.basename(bundle.yalm_file) if bundle.yalm_file else "MISSING",
            os.path.basename(bundle.metadata_file) if bundle.metadata_file else "MISSING",
            bundle.extra or "-",
        ))
        print("  metrics    : services=%d interactions=%d consolidated=%d fallbackA=%d" % (
            len(serv_systems), len(inter_systems), len(consolidated), len(consolidated_fallback),
        ))
        print("  metadata   : %d system rows" % len(metadata))
        print("  yalm       : %d system blocks, %d valid (doc-level=%s)" % (
            len(yaml_blocks), yaml_valid, "__document__" in yaml_blocks,
        ))

        if bundle.metrics_file is None:
            problems.append("%s: metrics file missing" % label)
        if bundle.yalm_file is None:
            problems.append("%s: YALM file missing" % label)
        if bundle.metadata_file is None:
            problems.append("%s: metadata file missing" % label)
        if serv_systems != set(CANONICAL_SYSTEMS):
            problems.append("%s: services systems mismatch -> %s" % (label, sorted(serv_systems)))
        if inter_systems != set(CANONICAL_SYSTEMS):
            problems.append("%s: interactions systems mismatch -> %s" % (label, sorted(inter_systems)))
        if not consolidated and not consolidated_fallback:
            problems.append("%s: no consolidated row and no Proposal A fallback" % label)
        if len(metadata) != len(CANONICAL_SYSTEMS):
            problems.append("%s: metadata has %d rows" % (label, len(metadata)))
        if yaml_blocks and yaml_valid == 0 and "__document__" not in yaml_blocks:
            problems.append("%s: no valid YAML block" % label)

    print("\n" + "=" * 100)
    print("PROBLEMS (%d)" % len(problems))
    for item in problems:
        print("  - %s" % item)


if __name__ == "__main__":
    main()
