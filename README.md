# DAVINCI Architect

**Multi-Agent Software Architect**

DAVINCI Architect is an AI-based tool for automated software architecture migration. It transforms textual system requirements into a recommended microservices architecture, using a specialized multi-agent pipeline guided by Domain-Driven Design (DDD) and bounded-context principles.

The tool includes a local web interface that allows users to enter system requirements, reference data for evaluation, and normalization maps. It then orchestrates four LLM agents, generates candidate architectures, refines them, and consolidates the best proposal into a final architecture.

---

## Overview

DAVINCI Architect was developed by **Daniel Anderson** in partnership with **Virtus UFCG**. It is designed as a research prototype for generating and evaluating microservice decompositions from natural-language requirements.

The system is implemented in Python and uses Google Gemini as the underlying LLM. The web interface is built with the Python standard library on the backend and HTML, CSS, Bootstrap 5, and vanilla JavaScript on the frontend. It does not require Flask, FastAPI, or other web frameworks.

---

## Pipeline Architecture

The core pipeline is composed of four specialized agents:

1. **Agent 1 — Software Architect (DDD)**
   Generates a conservative architecture from the textual requirements. It identifies business capabilities, groups responsibilities into cohesive services, and proposes justified communications.

2. **Agent 2 — Microservice Communication Specialist**
   Produces an independent architecture with special attention to inter-service interactions. It uses a large library of abstract, domain-independent reasoning patterns to infer only necessary dependencies.

3. **Agent 4 — Domain-Driven Refiner**
   Refines the proposals from Agents 1 and 2. It removes only unsupported communications, without adding or deleting services.

4. **Agent 3 — Architecture Validator**
   Consolidates the refined proposals. It receives the evaluation metrics of both proposals and uses them to choose the best base architecture, combining complementary interactions when supported by the requirements.

All agents use `temperature=0.0`.

---

## Web Interface

The local web interface allows:

* Adding up to **5 systems** per execution.
* Entering:

  * System name
  * Architecture target (currently only `Microservices`)
  * System requirements
  * Reference services
  * Reference interactions
  * Name normalization map
* Adding or removing system blocks dynamically via AJAX.
* Running the real multi-agent pipeline.
* Viewing final results in a responsive layout.
* Downloading a complete PDF report containing:

  * Inputs provided
  * Agent proposals
  * Final recommended architecture
  * Evaluation metrics
  * Best results per system

---

## Repository Structure

```text
Experimento_Multiagente/
│
├── agentes/
│   ├── agent1_architect_a_fs.py
│   ├── agent2_architect_b_fs.py
│   ├── agent3_validator_fs.py
│   └── agent4_refiner_fs.py
│
├── main_fewshot.py
├── requirements.txt
├── requirements-fixed.txt
├── .env.example
│
└── result/
    └── <system>/
        └── result_generalized_fewshot/
            └── run_<timestamp>/
```

```text
Interface/
├── server.py
├── templates/
│   ├── index.html
│   └── resultados.html
├── static/
│   ├── css/
│   │   └── styles.css
│   └── js/
│       └── app.js
├── utils/
│   ├── parsers.py
│   ├── pipeline_runner.py
│   └── pdf_generator.py
├── tests/
│   ├── test_server.py
│   └── test_contracts.py
└── README.md
```

The files inside `agentes/` are used by `main_fewshot.py`. The `Interface/` directory contains the web application and connects to the pipeline through `utils/pipeline_runner.py`.

---

## Inputs

For each system, the interface requires:

### System Requirements

The textual requirements describe the system capabilities. They are the only input used during architecture generation. The quality of the requirements directly influences the quality of the generated architecture.

### Reference Services

The list of expected microservices. This is used only for evaluation, not for generation. It allows the computation of Precision, Recall, and F1-score for the service identification task.

### Reference Interactions

The expected communication pairs between services. Like reference services, this is used only for evaluation. Each interaction is an unordered pair, such as:

```text
order-service <-> payment-service
```

### Name Normalization Map

Maps alternative service names to canonical names used in the reference data. This prevents valid services or interactions from being penalized because of naming differences.

Example:

```text
apigateway -> api-gateway
gateway -> api-gateway
```

These three evaluation-oriented inputs are optional if the user only wants an architecture recommendation without metrics.

---

## Outputs

For each execution, the pipeline saves the following inside:

```text
result/<system>/result_generalized_fewshot/run_<timestamp>/
```

* `proposta_a.csv`
* `proposta_b.csv`
* `consolidada.csv`
* `metricas_servicos.csv`
* `metricas_interacoes.csv`
* `sumario.json`
* `report.md`

The web interface also displays the final summary and allows downloading a PDF report.

---

## Environment

DAVINCI Architect depends on:

* Python 3.12+
* CrewAI
* python-dotenv
* reportlab (optional, for PDF generation)
* Google Gemini API access

The model is configured via the `.env` file:

```env
GOOGLE_API_KEY=...
GOOGLE_MODEL=gemini/gemini-flash-latest
```

The `.env` file must be located in the `Experimento_Multiagente/` directory.

---

## Installation

From the repository root:

```powershell
pip install -r Experimento_Multiagente\requirements-fixed.txt
```

If PDF generation requires additional dependencies, install them manually:

```powershell
pip install reportlab
```

---

## Running the Web Interface

Start the local server:

```powershell
python Interface/server.py
```

Open:

```text
http://127.0.0.1:8000/
```

Fill in the required fields and click **Run Pipeline**. The execution may take a few minutes because it performs multiple LLM calls.

---

## Running Tests

The automated tests use mocked runners and do not consume Gemini API credits.

```powershell
python -m unittest discover -s Interface/tests -p "test_*.py"
node --check Interface/static/js/app.js
python -m py_compile Interface/server.py
```

---

## Current Status

DAVINCI Architect is an ongoing research prototype. It has achieved high service-identification performance on reference systems such as Bookstore and PetClinic, with interaction results varying across runs. The consolidation layer now selects the best proposal based on F1 metrics, improving final consistency.

The tool is intended to generalize to new systems. It does not contain hardcoded domain-specific rules, and the same agent definitions can be reused for different sets of requirements and reference data.

---

## Credits

**Developed by Daniel Anderson**

In partnership with **Virtus UFCG**

Contact: `daniel.silva@virtus-cc.ufcg.edu.br`

© 2026 DAVINCI Architect. All rights reserved.

---

## License

This project is part of ongoing academic research. Non-commercial use is permitted. For other uses, please contact the authors.
