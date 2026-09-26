# DAVINCI Architect

**Multi-Agent Software Architect — LLM-driven microservice decomposition**

DAVINCI Architect is an AI-based tool for automated software architecture migration. It transforms textual system requirements into a recommended microservices architecture, using a specialized multi-agent pipeline guided by Domain-Driven Design (DDD) and bounded-context principles.

The tool ships with a local web interface where requirements and reference data are entered, and it is also the artifact under study in the current research cycle: an ablation of five agent configurations executed by three LLMs over eight open-source subject systems (see [Experiment (FSE 2027)](#experiment-fse-2027)).

---

## Contents

* [Overview](#overview)
* [Repository at a Glance](#repository-at-a-glance)
* [Pipeline Architecture](#pipeline-architecture)
* [Web Interface](#web-interface)
* [Inputs](#inputs)
* [Outputs](#outputs)
* [Experiment (FSE 2027)](#experiment-fse-2027)
* [Environment](#environment)
* [Installation](#installation)
* [Running the Web Interface](#running-the-web-interface)
* [Reproducing the Analyses](#reproducing-the-analyses)
* [Running Tests](#running-tests)
* [Current Status](#current-status)
* [Notes and Known Inconsistencies](#notes-and-known-inconsistencies)
* [Citation](#citation)
* [Credits](#credits)
* [License](#license)

---

## Overview

DAVINCI Architect was developed by **Daniel Anderson** in partnership with **Virtus UFCG**. It is designed as a research prototype for generating and evaluating microservice decompositions from natural-language requirements.

The pipeline is implemented in Python on top of **CrewAI** and is model-agnostic: the LLM provider is selected through the `DAVINCI_LLM_PROVIDER` environment variable, with **Anthropic (Claude) as the default**, and `deepseek` and `gemini` as supported alternatives. The web interface is built with the Python standard library on the backend and HTML, CSS, Bootstrap 5, and vanilla JavaScript on the frontend. It does not require Flask, FastAPI, or other web frameworks.

---

## Repository at a Glance

```text
DAVINCI/
├── Interface/                    # local web interface (backend + UI + tests)
├── Experimento_Multiagente/      # multi-agent pipeline and the experiment inputs
├── 2027-FSE-Report-and-Dates/    # frozen artifacts of the FSE 2027 study + analyses + reports
├── result/                       # pipeline outputs (created locally, ignored by Git)
├── execuion-metadados-C1-Gemini-FS1.json   # execution metadata of a reference run
└── LICENSE- Deed - Attribution 4.0 International - Creative Commons.pdf
```

| Path | What it contains |
|---|---|
| `Interface/` | Local HTTP server (`server.py`), user interface (`static/index.html`, `static/css/styles.css`, `static/js/app.js`), pipeline bridge (`utils/pipeline_runner.py`), parsers (`utils/parsers.py`), automated tests (`tests/`) and the interface specification (`spec/`, `tasks/`) |
| `Experimento_Multiagente/` | Pipeline entry point (`main_fewshot.py`), agents (`agentes/`), execution tracing (`execution_tracker.py`), quantitative analysis (`quantitative_analysis/`), subject systems and static analysis (`Dates-FSE-2027/`), benchmark monolithic systems (`monolits/`), research notes (`.md/`, `.txt/`) |
| `2027-FSE-Report-and-Dates/` | Per-(model, configuration, round) artifacts — metrics PDFs, YAML specifications and execution metadata JSONs — plus the prompts used by each agent, the frozen quantitative analysis, the extended re-analysis, the qualitative synthesis and the consolidated report |
| `result/` | Output directory of the pipeline; it is created on demand and ignored by Git (`.gitignore`) |

---

## Pipeline Architecture

The pipeline is composed of five specialized agents (plus a variant of Agent 2). They cooperate in an assemble-and-consolidate strategy: two independent proposals are produced, each of them is refined, and finally they are merged into a single architecture.

| Agent | Role |
|---|---|
| **Agent 1 — Software Architect (DDD)** | Generates a conservative architecture from the textual requirements. It identifies business capabilities, groups responsibilities into cohesive services, and proposes justified communications. |
| **Agent 2 — Microservice Communication Specialist** | Produces an independent architecture with special attention to inter-service interactions. It uses a large library of abstract, domain-independent reasoning patterns to infer only necessary dependencies. |
| **Agent 2.1 — Generalized Architect (C4)** | Drop-in replacement for Agent 2 in configuration C4: the same prompt as Agent 1, differentiated only by a distinct few-shot example, so that the second proposal comes from a generalist instead of a specialist. |
| **Agent 4 — Domain-Driven Refiner** | Refines the proposals from Agents 1 and 2. It removes only unsupported communications, without adding or deleting services. |
| **Agent 3 — Architecture Validator / Consolidator** | Consolidates the refined proposals. It receives the evaluation metrics of both proposals and uses them to choose the best base architecture, combining complementary interactions when supported by the requirements. |
| **Agent 5 — Architectural Spec Exporter** | Serialises the final architecture into `especificacao_arquitetural.yaml`, the machine-readable specification consumed by the interface and by the analysis scripts. |

All agents use `temperature=0.0`. Every agent has a few-shot variant (`agentes/agent*_fs.py`, the ones used by the experiments) and the three original roles also exist in a zero-shot variant under `agentes/zero-shot-agents/`.

### Configurations (ablations)

Five configurations are selectable programmatically; the web interface runs **C4**.

| Configuration | Agents | Purpose |
|---|---|---|
| **C0** | Agent 1 | A single proposal: no second proposal, no refinement, no consolidation and no dedicated YAML export stage. |
| **C1** | Agents 1, 2, 4, 3, 5 | The complete pipeline. |
| **C2** | Agents 1, 2, 3, 5 | Same as C1 without Agent 4, which isolates the contribution of the refinement stage. |
| **C3** | Agents 1, 4, 5 | Agent 2 and Agent 3 are removed together: a single proposal is refined and exported, evaluating the joint absence of the Communication Specialist and of consolidation. |
| **C4** | Agents 1, 2.1, 4, 3, 5 | Agent 2 is replaced by Agent 2.1, isolating the effect of replacing a specialized agent with a generalist one. |

The entry points are `executar_pipeline_c0()` … `executar_pipeline_c4()` in `Experimento_Multiagente/main_fewshot.py`. The web interface and the experiment runs call them with the inputs of each system.

---

## Web Interface

The local web interface allows:

* Adding up to **10 systems** per execution.
* Entering, for each system:

  * System name
  * Architecture target (currently only `Microservices`)
  * System requirements
  * Reference services
  * Reference interactions
* Adding or removing system blocks dynamically via AJAX.
* Running the real multi-agent pipeline (configuration C4).
* Viewing the final results in a responsive layout.
* Downloading two PDF reports:

  * the **architecture report** — inputs provided, agent proposals, final recommended architecture and evaluation metrics;
  * the **architectural specification** — the contents of `especificacao_arquitetural.yaml`.

---

## Inputs

Each system block receives three kinds of input.

### System Requirements

The natural-language description of the software system to be decomposed. This is the only input the agents use to reason; it is the textual source of the bounded contexts, services and interactions.

### Reference Services

The expected list of microservices for that system, written one per line. This is used **only for evaluation, not for generation**. It allows the computation of Precision, Recall, and F1-score for the service identification task.

```text
order-service
payment-service
inventory-service
```

### Reference Interactions

The expected communication pairs between services. Like reference services, this is used only for evaluation. Each interaction is an unordered pair, such as:

```text
order-service <-> payment-service
```

These evaluation-oriented inputs are optional if the user only wants an architecture recommendation without metrics.

---

## Outputs

For each execution, the pipeline saves the following inside:

```text
result/<system>/result_generalized_fewshot/run_<timestamp>/
```

| File | Content |
|---|---|
| `proposta_a.csv` | Architecture proposed by Agent 1 |
| `proposta_b.csv` | Architecture proposed by Agent 2 (or Agent 2.1 in C4) |
| `consolidada.csv` | Final architecture after refinement and consolidation |
| `metricas_servicos.csv` | Precision, Recall and F1 of the proposed services |
| `metricas_interacoes.csv` | Precision, Recall and F1 of the proposed interactions |
| `sumario.json` | Machine-readable summary of the run |
| `report.md` | Human-readable report of the run |
| `especificacao_arquitetural.yaml` | Architectural specification exported by Agent 5 |
| `execution_metadata.json` | Per-agent tracers: model, tokens, wall-clock time and status |
| `fewshot_c4.json` | Record of the few-shot examples used (C4 only) |

The `result/` directory is generated locally and is not versioned. The web interface displays the final summary and builds the two PDF reports on demand from these artifacts.

---

## Experiment (FSE 2027)

The pipeline is evaluated as an ablation with the following design:

| Factor | Values |
|---|---|
| LLMs | Gemini (`gemini-flash-latest`), DeepSeek (`deepseek-chat`), Claude (`claude-sonnet-4-5`) |
| Configurations | C0, C1, C2, C3, C4 |
| Rounds | 3 executions per (LLM, configuration) cell |
| Subject systems | 8 open-source applications: `7ep`, `AcmeAir`, `Cargo-Tracker`, `DayTrader7`, `Jokul`, `JPetStore`, `PetClinic`, `TNTConcept` |
| Corpus | 45 round artifacts, 15 (LLM, configuration) cells, 360 observations |

**Metrics.** F1 of services, F1 of interactions, YAML validity (raw and normalised verdicts) and cost (total tokens and wall-clock duration taken from the execution metadata). Each metric is aggregated per system before the statistical tests, so a system contributes a single value per configuration — which keeps the pairing valid and avoids pseudo-replication.

### Where the artifacts live

```text
2027-FSE-Report-and-Dates/
├── Gemini/  DeepSeek/  Claude/          # <Model>/<C0..C4>/Test-1..3 + TXT synthesised per cell
├── Prompts-used-in-the-agents/          # Agent-1, Agent-2, Agent-2_1, Agent-3, Agent-4, Agent-5
├── Requirements/Requirements-used-as-input/   # the 8 systems: requirements, reference services, reference interactions
├── Quantitative-Analysis/               # frozen analysis (Gemini + DeepSeek, C0-C3)
├── Quantitative-Analysis-Updated/       # re-analysis of the extended corpus (3 LLMs x C0-C4)
├── Qualitative-Analysis/                # qualitative evaluation protocol
└── DAVINCI-FSE2027-Consolidated-Report.md
```

Every round leaves three artifacts inside the model tree: a metrics report (PDF), a YAML specification and an execution metadata JSON. The subject systems themselves (source code used for the static analysis) and the input bundles consumed by the pipeline are under `Experimento_Multiagente/Dates-FSE-2027/`:

```text
Experimento_Multiagente/Dates-FSE-2027/
├── systems/                  # source code of the 8 subject systems (monolithic versions)
├── static analysis/          # SootUp-based static analysis of those systems
├── static-analysis-systems/  # consolidated static-analysis outputs used as pipeline input
├── ground true/              # reference microservice architectures (CSV) used for evaluation
└── davinci_inputs/           # per-system bundle: requirements, reference_services, reference_interactions
```

### Analyses and reports

| Artifact | Content |
|---|---|
| `Quantitative-Analysis/` | Frozen analysis of the two-model, four-configuration corpus (Gemini + DeepSeek, C0-C3): descriptive statistics, Wilcoxon paired tests, Spearman correlations, figures and `report.md` |
| `Quantitative-Analysis-Updated/` | Extended corpus (three LLMs x C0-C4): cost, per-system behaviour, precision/recall, ranking, C4 proposals, YAML validity, `report.md`, `report.html` and `verify_report.py` for integrity checks |
| `Qualitative-Analysis/` | Protocol used for the qualitative evaluation of the generated architectures |
| `DAVINCI-FSE2027-Consolidated-Report.md` | Single-document consolidation of the whole tree: artifact inventory, run calendar, re-analysis of the extended corpus, the fifteen qualitative syntheses and the integrated conclusions |

---

## Environment

DAVINCI Architect depends on:

* Python 3.12+
* CrewAI
* python-dotenv
* reportlab (PDF generation in the web interface)
* API access to the LLM provider actually used

The provider and the model are configured in the `.env` file placed in the `Experimento_Multiagente/` directory:

```env
# Provider: anthropic (default) | deepseek | gemini
DAVINCI_LLM_PROVIDER=anthropic

# Anthropic / Claude
ANTHROPIC_API_KEY=...
CLAUDE_MODEL=claude-sonnet-4-5-20250929
CLAUDE_MAX_TOKENS=4096

# DeepSeek
DEEPSEEK_API_KEY=...
DEEPSEEK_MODEL=deepseek-chat
DEEPSEEK_MAX_TOKENS=4096

# Google Gemini
GOOGLE_API_KEY=...
GOOGLE_MODEL=gemini-flash-latest
GOOGLE_MAX_TOKENS=4096
```

Only the credentials of the provider in use are required, and `.env` is ignored by Git. `Experimento_Multiagente/.env.example` is kept for reference, but it predates the multi-provider support (it lists OpenRouter variables) — use the block above as the authoritative list.

---

## Installation

From the repository root, in a Python 3.12+ virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r Experimento_Multiagente\requirements.txt
pip install reportlab

# SDK of the provider(s) you actually use (LiteLLM needs them at call time)
pip install anthropic        # Anthropic / Claude (default provider)
pip install openai           # DeepSeek (OpenAI-compatible API)
pip install google-genai     # Google Gemini (google-generativeai on older LiteLLM)
```

`Experimento_Multiagente\requirements.txt` is the pinned environment of the experiments; the provider SDKs and `reportlab` are installed separately, as above. `Experimento_Multiagente\requirements-fixed.txt` is a legacy relaxed list kept for reference only — do not install both. The analysis scripts need a few extra packages:

```powershell
pip install pandas numpy scipy matplotlib pyyaml pdfplumber
```

---

## Running the Web Interface

Start the local server from the repository root:

```powershell
python Interface/server.py
```

Open:

```text
http://127.0.0.1:8000/
```

Fill in the required fields and click **Run Pipeline**. The execution may take a few minutes because it performs several LLM calls (configuration C4 runs five agents). Runs are written to `result/<system>/result_generalized_fewshot/run_<timestamp>/`, and the two PDF reports are built on demand by the server when requested from the results page.

---

## Reproducing the Analyses

```powershell
# frozen analysis (Gemini + DeepSeek, C0-C3) -> CSVs, figures, report.md
python Experimento_Multiagente\quantitative_analysis\run_all.py

# extended re-analysis (three LLMs x C0-C4) -> CSVs, figures, report.md/html
cd 2027-FSE-Report-and-Dates\Quantitative-Analysis-Updated
python run_all.py
python verify_report.py
cd ..\..
```

Use `--refresh-cache` with `quantitative_analysis\run_all.py` to force the re-extraction of the text from every PDF, which is only needed when the source artifacts change.

The consolidated report (`DAVINCI-FSE2027-Consolidated-Report.md`) is generated by the scratch scripts documented in its Appendix A. It reads the experiment tree as read-only input: the PDFs, YAML specifications, metadata JSONs, TXT syntheses and the whole `Quantitative-Analysis/` directory are never modified.

---

## Running Tests

The automated tests use mocked runners and do not consume LLM credits. From the repository root:

```powershell
# interface: unit tests with a real local server and a mocked pipeline (~45 s)
python -m unittest discover -s Interface/tests -p "test_*.py"

# static checks of the interface entry points
node --check Interface/static/js/app.js
python -m py_compile Interface/server.py

# pipeline: C4 wiring (independent proposals, few-shot provenance, agent labels)
# and execution tracker; fully offline
python -m unittest Experimento_Multiagente.test_c4_example_b Experimento_Multiagente.test_execution_tracker
```

The remaining scripts under `Experimento_Multiagente/` (`testar_agente1.py`, `teste_agente.py`, `teste_pipeline.py`, `testar_deepseek_sem_api.py`, `verificar_diversidade_c4.py`, `verificar_tracer_c4_offline.py`, `diagnosticar_openrouter.py`) are exploratory utilities kept for provenance; some of them are meant to be executed directly and may call a provider.

---

## Current Status

DAVINCI Architect is an ongoing research prototype. The current cycle (FSE 2027) evaluates it as an ablation over eight open-source systems, three LLMs and five configurations, with three rounds per cell. The artifacts are frozen in `2027-FSE-Report-and-Dates/` and consolidated in `DAVINCI-FSE2027-Consolidated-Report.md`: the complete pipeline and its variants reach high service-identification F1 on the subject systems, the individual contributions of the refinement stage (Agent 4) and of the second independent proposal (Agent 2) are measurable but configuration-dependent, and YAML validity depends on the model as much as on the pipeline.

The tool is intended to generalize to new systems. It does not contain hardcoded domain-specific rules, and the same agent definitions can be reused for different sets of requirements and reference data. In the experiments the few-shot examples are deliberately taken from systems outside the corpus, so that no example leaks information about the subject systems.

---

## Notes and Known Inconsistencies

* `Experimento_Multiagente/.env.example` still lists the legacy OpenRouter variables; the [Environment](#environment) section is the authoritative list of supported providers.
* `Experimento_Multiagente/requirements-fixed.txt` is a legacy relaxed dependency list; use `requirements.txt`.
* `Experimento_Multiagente/main.py`, `experimento_completo.py` and the `*.py` diagnostic scripts (`diagnosticar_openrouter.py`, `testar_*.py`, `teste_*.py`, `verificar_*.py`) are earlier iterations and exploratory utilities kept for provenance; the current entry point is `main_fewshot.py`.
* The PDFs generated by the interface are named `virtus-architecture-report.pdf` and `virtus-architectural-specification.pdf` — a legacy of the previous name of the tool.
* `Experimento_Multiagente/h origin mainclear` is a stray file created by a malformed shell command; no script reads it.
* The artifacts of the previous study were removed from this repository (commit `5d35770`, "Remove Reproduction_Artifacts (not used in the final article)"); the corpus of the current paper is the one in `2027-FSE-Report-and-Dates/`.
* `result/` and the virtual environments are not versioned: runs and environments are local artifacts.

---

## Citation

The results collected in this repository are part of a study currently under review. The full citation entry (authors, title, venue and DOI) will be added here once the paper is published. Until then, please refer to the consolidated report:

> *DAVINCI Architect — Consolidated Experimental Report (FSE 2027)*, `2027-FSE-Report-and-Dates/DAVINCI-FSE2027-Consolidated-Report.md`.

---

## Credits

**Developed by Daniel Anderson**

In partnership with **Virtus UFCG**

Contact: `daniel.silva@virtus-cc.ufcg.edu.br`

© 2026 DAVINCI Architect. All rights reserved.

---

## License

This project is part of ongoing academic research. Non-commercial use is permitted. For other uses, please contact the authors.

Third-party material redistributed in this repository keeps its original licensing: the two publications stored as `LICENSE- Deed - Attribution 4.0 International - Creative Commons.pdf` (root and `Experimento_Multiagente/`) are licensed under **CC BY 4.0**, and the source code of the subject systems under `Experimento_Multiagente/Dates-FSE-2027/systems/` keeps the license of each upstream project (see the `LICENSE` file of each system).
