# VIRTUS Microservice Architecture Interface Constitution

## Core Principles

### I. Interface-First Scope
This project is currently a web interface prototype for generating and reviewing microservice architecture decompositions. The active scope is limited to the frontend experience and the local server structure in `Interface/`. Integration with the existing multi-agent pipeline is explicitly deferred.

### II. Standard-Library Backend
The backend MUST use Python's standard-library `http.server`. It MUST expose the local HTTP endpoints required by the interface without introducing a web framework. Frontend requests MUST use plain JavaScript AJAX and communicate through explicit JSON contracts.

### III. Mocked Pipeline Boundary
Until the real integration is approved, backend pipeline responses MUST be simulated with mock data. Mock behavior MUST preserve the expected shape of systems, requirements, services, interactions, metrics, best results, and report responses so the interface can be tested independently. Future integration points MUST be marked with clear TODO comments, including comments such as `# TODO: Integrate with pipeline_runner here`.

### IV. Complete Prototype Workflow
The interface MUST support adding up to five systems dynamically through AJAX. Each system MUST provide fields for system name, requirements, reference services, reference interactions, and a name normalization map. The workflow MUST provide `Run Pipeline`, `New Decomposition`, a results page with Services, Interactions, and Best Results tables, and `Download Full Report (PDF)`. The report download may remain a simulated or simple test PDF response during this phase.

### V. VIRTUS Visual Identity
The interface MUST use the VIRTUS visual language: navy primary `#0A1E5C`, white background `#FFFFFF`, light-gray fields `#F2F2F2`, and gold accent `#E9C46A`. Typography MUST be sans-serif, headings MUST use uppercase text, and body copy MUST remain legible. All visible interface text MUST be in English.

### VI. Generalized, System-Agnostic Design
The interface and its mock data MUST use generalized structures and terminology. No system-specific services, interactions, normalization rules, or architecture assumptions may be hard-coded into reusable UI or server logic. System-specific values may appear only as user-provided input or isolated mock fixtures used to demonstrate the contract.

### VII. Experimental Pipeline Protection
The existing pipeline is an external protected dependency in this phase. Files under `Experimento_Multiagente/`, including `main_fewshot.py` and all existing agent modules, MUST remain unchanged. Existing result artifacts and reproducibility-related files MUST not be modified. Any future pipeline integration MUST be additive and isolated behind an explicit adapter or runner boundary.

## Technical Constraints

The implementation MUST use HTML, CSS, Bootstrap 5, and plain JavaScript for the frontend. It MUST use AJAX for dynamic system management and pipeline submission. The local server MUST run with Python's standard library only. The interface MUST remain usable without a live LLM, external pipeline process, or production database.

The server MUST validate the maximum of five systems and return structured errors for invalid requests. Mock responses MUST be deterministic enough for repeatable UI testing. File paths and integration details for the existing pipeline MUST not be inferred from browser input.

## Development Workflow

Changes MUST remain within `Interface/` during this phase. Each feature MUST be testable through the local server without the real multi-agent pipeline. Before real integration is introduced, the request and response schemas, output persistence behavior, error handling, and reproducibility requirements MUST be reviewed and approved. Any integration implementation MUST preserve the existing CLI experiment as a separately reproducible path.

## Governance

This constitution governs all implementation work in `Interface/` and supersedes conflicting local conventions for this prototype. Amendments MUST document the changed scope, affected contracts, and impact on the protected experimental pipeline. Reviews MUST verify that no files outside `Interface/` were changed, that mock behavior remains available, and that future integration locations are explicitly marked with TODO comments.

**Version**: 1.0.0 | **Ratified**: 2026-08-19 | **Last Amended**: 2026-08-19
