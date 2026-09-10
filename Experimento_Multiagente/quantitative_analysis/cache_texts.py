"""Cache extracted text from every PDF/TXT artifact.

Extracting text from ~50 PDFs with pdfplumber is slow (tens of seconds). This
helper performs the extraction once and stores the result as JSON so that the
inspection and extraction scripts run quickly afterwards.

Run from the repository root:

    python Experimento_Multiagente/quantitative_analysis/cache_texts.py
"""

from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from _source_scan import discover_bundles, read_text  # noqa: E402

BASE_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "2027-FSE-Report-and-Dates",
)
CACHE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_text_cache.json")


def main() -> None:
    """Extract and cache the text of every source artifact."""
    cache = {}
    bundles = discover_bundles(BASE_DIR)
    for bundle in bundles:
        for path in (bundle.metrics_file, bundle.yalm_file):
            if path and path not in cache:
                print("extracting: %s" % path, flush=True)
                cache[path] = read_text(path)
    with open(CACHE_PATH, "w", encoding="utf-8") as handle:
        json.dump(cache, handle, ensure_ascii=False)
    print("cached %d files -> %s" % (len(cache), CACHE_PATH), flush=True)


if __name__ == "__main__":
    main()
