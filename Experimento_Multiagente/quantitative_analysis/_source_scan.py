"""
Source scanning utilities.

This module centralizes the low-level discovery of the experimental artifacts
produced by the DAVINCI Architect pipeline. It is shared by the inspection
script (Step 0) and the extraction script (Step 1).

Directory layout (per configuration and LLM):

    <base>/<LLM>/<Cx>/Test-<n>/
        *-Metrics.(pdf|txt)     -> Sections with services / interactions F1
        *-YALM.(pdf|txt)        -> YAML architectural specification
        execution metadata .json -> per-system execution tracer (tokens, time)

The functions below are intentionally defensive: the artifacts were generated
over several months and the naming conventions are not perfectly consistent.
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

LLMS = ["Gemini", "DeepSeek"]
CONFIGS = ["C0", "C1", "C2", "C3"]

# Canonical system identifiers used across the analysis. The raw artifacts use
# slightly different spellings (e.g. "acmeair" vs "AcmeAir", "Pet-Clinic" vs
# "PetClinic"), so every raw value is normalized through this table.
CANONICAL_SYSTEMS = [
    "7ep",
    "AcmeAir",
    "Cargo-Tracker",
    "DayTrader7",
    "Jokul",
    "JPetStore",
    "PetClinic",
    "TNTConcept",
]

_SYSTEM_ALIASES = {
    "7ep": "7ep",
    # The DeepSeek/C1 artifacts label this system "7ed" (typo in the generator).
    "7ed": "7ep",
    "acmeair": "AcmeAir",
    "cargo-tracker": "Cargo-Tracker",
    "cargo tracker": "Cargo-Tracker",
    "daytrader7": "DayTrader7",
    "jokul": "Jokul",
    "jpetstore": "JPetStore",
    "petclinic": "PetClinic",
    "pet-clinic": "PetClinic",
    "pet clinic": "PetClinic",
    "tntconcept": "TNTConcept",
}


def normalize_system(name: str) -> Optional[str]:
    """Return the canonical system name for a raw identifier.

    Args:
        name: Raw system identifier found in an artifact.

    Returns:
        The canonical name, or ``None`` when the identifier is unknown.
    """
    if name is None:
        return None
    key = name.strip().strip('"').strip().lower()
    return _SYSTEM_ALIASES.get(key)


@dataclass
class SourceBundle:
    """Paths describing the artifacts of a single (LLM, config, test) run."""

    llm: str
    config: str
    test: str  # "1", "2" or "3"
    test_dir: str
    metrics_file: Optional[str] = None
    yalm_file: Optional[str] = None
    metadata_file: Optional[str] = None
    extra: List[str] = field(default_factory=list)


def discover_bundles(base_dir: str) -> List[SourceBundle]:
    """Walk the artifact tree and group files per (LLM, config, test).

    Args:
        base_dir: Root of the experimental results tree.

    Returns:
        A list of :class:`SourceBundle`, sorted by LLM, config and test.
    """
    bundles: List[SourceBundle] = []
    for llm in LLMS:
        for config in CONFIGS:
            for test in ("1", "2", "3"):
                test_dir = os.path.join(base_dir, llm, config, "Test-%s" % test)
                bundle = SourceBundle(llm=llm, config=config, test=test, test_dir=test_dir)
                if not os.path.isdir(test_dir):
                    bundle.extra.append("MISSING_DIR")
                    bundles.append(bundle)
                    continue
                for fname in sorted(os.listdir(test_dir)):
                    path = os.path.join(test_dir, fname)
                    if not os.path.isfile(path):
                        continue
                    low = fname.lower()
                    if "metrics" in low:
                        bundle.metrics_file = path
                    elif "yalm" in low:
                        bundle.yalm_file = path
                    elif low.endswith(".json"):
                        bundle.metadata_file = path
                    else:
                        bundle.extra.append(fname)
                bundles.append(bundle)
    return bundles


def load_json_metadata(path: str) -> List[dict]:
    """Load a per-system execution tracer JSON file.

    Args:
        path: Path to the JSON metadata file.

    Returns:
        A list of per-system dictionaries (empty when the file is unreadable).
    """
    if not path or not os.path.isfile(path):
        return []
    with open(path, encoding="utf-8") as handle:
        data = json.load(handle)
    if isinstance(data, dict):  # Defensive: tolerate a wrapped structure.
        return list(data.values())
    return data


_CACHE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_text_cache.json")
_CACHE: Optional[Dict[str, str]] = None


def _load_cache() -> Dict[str, str]:
    """Load (once) the JSON text cache produced by ``cache_texts.py``."""
    global _CACHE
    if _CACHE is None:
        if os.path.isfile(_CACHE_PATH):
            with open(_CACHE_PATH, encoding="utf-8") as handle:
                _CACHE = json.load(handle)
        else:
            _CACHE = {}
    return _CACHE


def read_text(path: str, use_cache: bool = True) -> str:
    """Read the full plain-text content of a PDF or TXT artifact.

    Args:
        path: Path to a ``.pdf`` or ``.txt`` file.
        use_cache: When ``True`` the JSON text cache is consulted first, which
            avoids the cost of re-parsing PDFs with pdfplumber.

    Returns:
        The concatenated text of every page (PDF) or the raw file (TXT).
    """
    if not path or not os.path.isfile(path):
        return ""
    if use_cache:
        cached = _load_cache().get(path)
        if cached is not None:
            return cached
    if path.lower().endswith(".pdf"):
        import pdfplumber

        with pdfplumber.open(path) as doc:
            return "\n".join((page.extract_text() or "") for page in doc.pages)
    with open(path, encoding="utf-8", errors="replace") as handle:
        return handle.read()


# A metric row looks like: "<system> | Proposal A | 0.9091 | 1.0000 | 0.9524"
# The DeepSeek/C3/Test-1 TXT variant uses tabs and no proposal column:
# "<system>\t1.0000\t1.0000\t1.0000".
_ROW_PIPE = re.compile(
    r"^(?P<system>[^|]+?)\s*\|\s*(?P<proposal>Proposal\s+[A-Z]|Consolidated)\s*\|"
    r"\s*(?P<precision>[0-9.]+)\s*\|\s*(?P<recall>[0-9.]+)\s*\|\s*(?P<f1>[0-9.]+)\s*$",
    re.IGNORECASE,
)
_ROW_TAB = re.compile(
    r"^(?P<system>[^\t]+?)\t(?P<precision>[0-9.]+)\t(?P<recall>[0-9.]+)\t(?P<f1>[0-9.]+)\s*$"
)


def parse_metrics(path: str) -> Dict[str, Dict[str, float]]:
    """Extract the F1 scores per system and per proposal from a metrics file.

    The parser supports the two formats found in the artifacts:

    * Multi-agent PDF reports with the sections
      ``Services Metrics: ...`` and ``Interactions Metrics: ...`` and rows
      keyed by ``Proposal A/B/...`` or ``Consolidated``.
    * The legacy TXT report (DeepSeek/C3/Test-1) that only exposes the
      services / interactions tables with an implicit ``Proposal A``.

    Args:
        path: Path to the metrics PDF or TXT file.

    Returns:
        Mapping ``system -> {proposal -> f1}`` including the ``Consolidated``
        key when available (falling back to ``Proposal A`` otherwise).
    """
    text = read_text(path)
    result: Dict[str, Dict[str, float]] = {}
    section = None  # "services" or "interactions"

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        low = line.lower()
        if low.startswith("services metrics") or low.startswith("servi"):
            # Covers "Services Metrics:" (PDF) and "Serviços" (legacy TXT).
            section = "services"
            continue
        if low.startswith("interactions metrics") or low.startswith("intera"):
            # Covers "Interactions Metrics:" (PDF) and "Interações" (legacy TXT).
            section = "interactions"
            continue
        if low.startswith("section 4") or low.startswith("best results"):
            # Any other section terminates the metric tables.
            section = None
            continue
        if section is None or ("|" not in line and "\t" not in line):
            continue

        match = _ROW_PIPE.match(line)
        if match:
            system = normalize_system(match.group("system"))
            if system is None:
                continue
            proposal = match.group("proposal")
            proposal = "Consolidated" if proposal.lower().startswith("consolidated") else proposal
            result.setdefault(system, {})["%s::%s" % (section, proposal)] = float(match.group("f1"))
            continue

        match = _ROW_TAB.match(line)
        if match:
            system = normalize_system(match.group("system"))
            if system is None:
                continue
            result.setdefault(system, {})["%s::Proposal A" % section] = float(match.group("f1"))
    return result


def split_yaml_systems(path: str) -> Dict[str, str]:
    """Split an architectural specification file into one YAML block per system.

    Every ``SYSTEM: <name>`` marker delimits a new system; the YAML body starts
    at the following ``system:`` key and runs until the next marker.

    Args:
        path: Path to the YALM PDF or TXT file.

    Returns:
        Mapping ``canonical system name -> YAML text``.
    """
    text = read_text(path)
    if not text:
        return {}

    # The DeepSeek/C3/Test-1 variant is already a single YAML document that
    # wraps every system under a top-level ``systems:`` list.
    if re.search(r"^\s*systems:\s*$", text, re.MULTILINE) and "SYSTEM:" not in text:
        return {"__document__": text}

    markers = list(re.finditer(r"^SYSTEM:\s*(?P<name>.+?)\s*$", text, re.MULTILINE))
    blocks: Dict[str, str] = {}
    for index, marker in enumerate(markers):
        raw_name = marker.group("name")
        system = normalize_system(raw_name)
        if system is None:
            continue
        start = marker.end()
        end = markers[index + 1].start() if index + 1 < len(markers) else len(text)
        body = text[start:end]
        body = body.split("Developed by Daniel Anderson")[0]
        blocks[system] = body.strip("\n")
    return blocks


# ---------------------------------------------------------------------------
# YAML normalization and validation
# ---------------------------------------------------------------------------

# The PDF renderer flattens the 2-space indentation of the "to:" lines that
# belong to the preceding "- from:" mapping entry, e.g. it emits
#
#     interactions:
#     - from: "A"
#     to: "B"
#
# instead of the intended
#
#     interactions:
#     - from: "A"
#       to: "B"
#
# ``normalize_pdf_yaml`` repairs exactly this artifact so that the YAML syntax
# can be evaluated (see the report's methodology section).
_TO_LINE = re.compile(r"^to:", re.MULTILINE)


def normalize_pdf_yaml(text: str) -> str:
    """Repair the indentation artifact introduced by the PDF renderer.

    Args:
        text: Raw YAML text extracted from a PDF.

    Returns:
        The text with ``to:`` lines re-indented under their ``- from:`` entry.
    """
    return _TO_LINE.sub("  to:", text)


def yaml_validity(path: str) -> Dict[str, int]:
    """Evaluate the syntactic validity of the generated YAML per system.

    Args:
        path: Path to a YALM PDF or TXT file.

    Returns:
        Mapping ``canonical system name -> 1|0``, where ``1`` means that the
        normalized YAML loads with ``yaml.safe_load``.
    """
    import yaml

    blocks = split_yaml_systems(path)
    result: Dict[str, int] = {}
    if "__document__" in blocks:
        # Legacy TXT: a single YAML document with a top-level ``systems`` list.
        try:
            data = yaml.safe_load(blocks["__document__"])
            listed = data.get("systems", []) if isinstance(data, dict) else []
        except Exception:
            listed = []
        names = [normalize_system(str(item.get("system"))) for item in listed] or CANONICAL_SYSTEMS
        for system in names:
            if system:
                result[system] = 1 if listed else 0
        return result

    for system, block in blocks.items():
        try:
            yaml.safe_load(normalize_pdf_yaml(block))
            result[system] = 1
        except Exception:
            result[system] = 0
    return result


def load_metadata_mapped(path: str) -> Dict[str, dict]:
    """Load the execution tracer metadata keyed by canonical system name.

    Some DeepSeek files omit the ``system`` field; in that case the entries are
    assigned following :data:`CANONICAL_SYSTEMS` order. That positional
    assumption was validated against the per-system token tables of the
    synthesized reports (they match exactly).

    Args:
        path: Path to the JSON metadata file.

    Returns:
        Mapping ``canonical system name -> {"total_tokens", "duration_ms"}``.
    """
    rows = load_json_metadata(path)
    mapped: Dict[str, dict] = {}
    for index, row in enumerate(rows):
        system = normalize_system(str(row.get("system", "")))
        if system is None and index < len(CANONICAL_SYSTEMS):
            system = CANONICAL_SYSTEMS[index]
        if system is None:
            continue
        usage = row.get("llm_usage", {}) or {}
        execution = row.get("execution", {}) or {}
        mapped[system] = {
            "total_tokens": usage.get("total_tokens"),
            "duration_ms": execution.get("duration_ms"),
        }
    return mapped
