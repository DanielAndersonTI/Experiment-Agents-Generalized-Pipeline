"""Model, configuration and label constants of the updated corpus.

The frozen pipeline discovers these lists by walking the artifact tree
(``_source_scan.py`` of ``Experimento_Multiagente/quantitative_analysis``).  The
updated analysis reuses the table extracted from the same tree by
``scan_all.py``, so the lists are declared here explicitly.
"""

from __future__ import annotations

#: Execution order of the five configurations.
CONFIGS = ["C0", "C1", "C2", "C3", "C4"]

#: Every configuration contrast evaluated by the paired tests (10 per model).
COMPARISONS = [
    ("C0", "C1"),
    ("C0", "C2"),
    ("C0", "C3"),
    ("C0", "C4"),
    ("C1", "C2"),
    ("C1", "C3"),
    ("C1", "C4"),
    ("C2", "C3"),
    ("C2", "C4"),
    ("C3", "C4"),
]

#: Language models, in the order used by the tables and figures.  The labels are
#: the ones written by the execution metadata of the artifacts.
LLMS = ["Gemini", "DeepSeek", "Claude"]

#: Long labels for the report tables.
LLM_LABELS = {
    "Gemini": "Gemini (gemini-flash-latest)",
    "DeepSeek": "DeepSeek",
    "Claude": "Claude Sonnet 4.5",
}

#: The eight subject systems, in the canonical order of the experiment.
SYSTEMS = [
    "7ep",
    "AcmeAir",
    "Cargo-Tracker",
    "DayTrader7",
    "Jokul",
    "JPetStore",
    "PetClinic",
    "TNTConcept",
]

#: Agent composition of each configuration (used by the cost/effort tables).
AGENTS = {
    "C0": "1",
    "C1": "1, 2, 3, 4, 5",
    "C2": "1, 2, 3, 5",
    "C3": "1, 4, 5",
    "C4": "1, 2.1, 3, 4, 5",
}

#: One-line purpose of each configuration.
PURPOSE = {
    "C0": "single-agent baseline (Agent 1 alone)",
    "C1": "complete pipeline",
    "C2": "Refiner ablated",
    "C3": "Communication Specialist and Consolidator ablated",
    "C4": "Communication Specialist replaced by a generalist architect",
}

#: Rounds of the design (R1-R3 of every cell).
ROUNDS = [1, 2, 3]
