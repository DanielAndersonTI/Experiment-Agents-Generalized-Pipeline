# Feature Specification: VIRTUS Microservice Architecture Generation Interface

**Feature Branch**: `001-virtus-architecture-interface`

**Created**: 2026-08-19

**Status**: Draft

**Input**: User description: "Create a web prototype for generating microservice architectures from textual requirements using a mocked backend and a future-safe integration boundary."

## User Scenarios & Testing

### User Story 1 - Define Systems for Decomposition (Priority: P1)

As an architecture researcher, I want to enter one or more system definitions so that I can prepare architecture decomposition inputs in a single interface.

**Why this priority**: Input collection is the minimum viable workflow and must work independently before execution or reporting can provide value.

**Independent Test**: Open the home page, complete the first system block, add and remove system blocks, and verify that no more than ten systems can be configured.

**Acceptance Scenarios**:

1. **Given** the home page is opened, **When** the page finishes loading, **Then** exactly one empty system block is displayed.
2. **Given** a system block is displayed, **When** the user enters a system name, requirements, reference services, reference interactions, and a normalization map, **Then** the values remain visible and the block is valid.
3. **Given** fewer than ten system blocks exist, **When** the user selects `Add another system`, **Then** a new empty block is added through an AJAX request.
4. **Given** ten system blocks exist, **When** the user selects `Add another system`, **Then** no eleventh block is added and an appropriate limit message is displayed.
5. **Given** more than one system block exists, **When** the user selects `Remove`, **Then** that block is removed through an AJAX request.
6. **Given** exactly one system block exists, **When** the user attempts to remove it, **Then** it remains visible and the interface explains that one block is required.
7. **Given** one or more fields are invalid, **When** the user selects `Run Pipeline`, **Then** the interface displays field-level or block-level validation messages and does not submit the run request.

### User Story 2 - Run a Mocked Decomposition (Priority: P1)

As an architecture researcher, I want to submit valid system definitions and receive simulated decomposition results so that I can test the complete interface without connecting to the real multi-agent pipeline.

**Why this priority**: The prototype must demonstrate the central product workflow while keeping the experimental pipeline isolated and unchanged.

**Independent Test**: Submit valid data for one or more systems, observe the loading state, and verify that the results page contains mocked services, interactions, metrics, and best-result summaries.

**Acceptance Scenarios**:

1. **Given** all required fields are complete, **When** the user selects `Run Pipeline`, **Then** the browser sends the system definitions to the backend using AJAX.
2. **Given** a valid run request, **When** the mock backend completes successfully, **Then** the interface navigates to a results view containing Services, Interactions, and Best Results tables.
3. **Given** a run is in progress, **When** the backend request is pending, **Then** a visible loading state disables duplicate submission and communicates that a simulated run is being performed.
4. **Given** the mock backend is configured for an LLM failure scenario, **When** the user runs the decomposition, **Then** the interface displays an English error message and keeps the submitted input available for correction or retry.
5. **Given** the mock backend is configured for a low-results scenario, **When** the run completes, **Then** the results view displays the returned low precision, recall, and F1 values without treating them as a transport error.
6. **Given** a backend failure response, **When** the browser receives it, **Then** the interface displays an actionable error message and does not show stale results as if they were current.

### User Story 3 - Review and Export Results (Priority: P2)

As an architecture researcher, I want to inspect mock evaluation results and download a full report so that I can review the decomposition outcome and test the reporting workflow.

**Why this priority**: Reporting completes the demonstrable workflow, but it depends on the successful input and run flows.

**Independent Test**: Open a successful mocked results response, verify all three result sections, request the PDF, and confirm that a PDF response is downloaded.

**Acceptance Scenarios**:

1. **Given** a successful run, **When** the results view is displayed, **Then** the Services table shows System, Proposal, Precision, Recall, and F1-Score columns.
2. **Given** a successful run, **When** the results view is displayed, **Then** the Interactions table shows System, Proposal, Precision, Recall, and F1-Score columns.
3. **Given** a successful run, **When** the results view is displayed, **Then** the Best Results section identifies the best service and interaction result for each system.
4. **Given** a successful run, **When** the user selects `Download Full Report (PDF)`, **Then** the browser requests the backend PDF route and downloads a simple test PDF.
5. **Given** a PDF download request, **When** the backend generates the report, **Then** it includes the system name, submitted requirements, reference services, reference interactions, normalization map, mock Services, Interactions, Best Results tables, and a date/time footer.

### User Story 4 - Start a New Decomposition (Priority: P2)

As an architecture researcher, I want to start a new decomposition so that I can clear the current session without manually removing each field and block.

**Why this priority**: Resetting the workflow prevents stale input from contaminating later prototype demonstrations.

**Independent Test**: Populate multiple blocks, select `New Decomposition`, and verify that one empty block remains.

**Acceptance Scenarios**:

1. **Given** multiple populated system blocks exist, **When** the user selects `New Decomposition`, **Then** all values are cleared and extra blocks are removed.
2. **Given** the results view is displayed, **When** the user selects `New Decomposition`, **Then** the interface returns to the input view with one empty system block.

### Edge Cases

- A request containing zero systems MUST be rejected by the backend with a structured validation error.
- A request containing more than ten systems MUST be rejected by the backend with a structured validation error.
- A system with a missing or whitespace-only required field MUST be rejected before mock execution.
- The `Architecture target` control MUST display `Microservices` as the only enabled option; unsupported targets remain unavailable.
- Empty mock arrays MUST render a meaningful empty state rather than broken tables.
- A repeated `Run Pipeline` click while a request is pending MUST not create duplicate runs.
- A network timeout or malformed JSON response MUST produce a user-visible English error.
- PDF generation with multiple systems MUST include each submitted system and its corresponding mock results.

## Requirements

### Functional Requirements

- **FR-001**: The system MUST render an initial decomposition page containing exactly one system block.
- **FR-002**: Each system block MUST contain required fields for system name, system requirements, reference services, and reference interactions.
- **FR-003**: Each system block MUST contain an `Architecture target` dropdown with only `Microservices` enabled in this phase.
- **FR-004**: The system MUST provide placeholders and short descriptions for all input fields.
- **FR-005**: The system MUST add system blocks dynamically through an AJAX request, up to a maximum of ten blocks.
- **FR-006**: The system MUST allow a block to be removed through AJAX when more than one block exists.
- **FR-007**: The system MUST prevent removal of the final remaining system block.
- **FR-008**: The system MUST validate all required fields in the frontend before submitting a run.
- **FR-009**: The backend MUST validate the submitted JSON payload, including system count, required strings, and supported architecture target.
- **FR-010**: The `Run Pipeline` action MUST submit valid system definitions to the backend through AJAX.
- **FR-011**: The backend MUST return deterministic mock results and MUST NOT execute `main_fewshot.py`, any existing agent module, or the real multi-agent pipeline.
- **FR-012**: The implementation MUST support mock scenarios for successful results, simulated LLM failure, and low metric results.
- **FR-013**: The frontend MUST show a loading state while a run request is pending and MUST prevent duplicate submissions.
- **FR-014**: The backend MUST return structured JSON success and error responses suitable for frontend rendering.
- **FR-015**: The results view MUST render Services, Interactions, and Best Results sections for every submitted system.
- **FR-016**: The Services and Interactions tables MUST contain System, Proposal, Precision, Recall, and F1-Score columns.
- **FR-017**: The Best Results section MUST identify the best service and interaction result by system using the returned mock metrics.
- **FR-018**: The `New Decomposition` action MUST clear all fields, discard extra blocks, and return to one empty system block.
- **FR-019**: The backend MUST expose a PDF report route that returns a simple test PDF for the current submitted decomposition.
- **FR-020**: The PDF report MUST include submitted inputs, mock result tables, and a date/time footer.
- **FR-021**: All visible interface text and user-facing error messages MUST be in English.
- **FR-022**: The interface MUST use Bootstrap 5, responsive layout rules, plain JavaScript, and AJAX without a frontend framework.
- **FR-023**: The backend MUST use Python's standard-library `http.server` without a web framework.
- **FR-024**: The interface MUST use the VIRTUS colors `#0A1E5C`, `#FFFFFF`, `#F2F2F2`, and `#E9C46A`, with sans-serif typography and uppercase headings.
- **FR-025**: Every future real-pipeline integration location MUST contain an explicit TODO comment, such as `# TODO: Integrate with pipeline_runner here`.
- **FR-026**: No implementation in this phase MAY modify files outside `Interface/`, including `Experimento_Multiagente/main_fewshot.py` and the existing agent modules.
- **FR-027**: Reusable UI and mock contracts MUST remain system-agnostic and MUST NOT embed benchmark-specific services, interactions, or normalization maps.

### Routes and Interface Contracts

The local server MUST provide the following routes. Exact URL prefixes may be selected during planning, but the behavior and payload shape MUST remain equivalent.

- **GET `/`**: Serves the input page.
- **GET `/static/<asset>`**: Serves frontend assets such as CSS and JavaScript.
- **POST `/api/systems`**: Returns a new empty system-block model for dynamic insertion. The request MAY include the current block count; the backend MUST reject a count that would exceed five.
- **DELETE `/api/systems/<index>`**: Confirms removal of a system block when at least one other block remains.
- **POST `/api/pipeline/run`**: Accepts a JSON object containing `systems` and an optional mock scenario. Returns either a success object with `run_id`, normalized input echo, `service_metrics`, `interaction_metrics`, `best_results`, and report metadata, or a structured error object.
- **GET `/api/report/pdf`**: Generates the test PDF for the most recent valid decomposition or a request-selected run context. The route MUST return `application/pdf` and a downloadable filename.

A system input object MUST contain:

```json
{
  "system_name": "string",
  "architecture_target": "Microservices",
  "requirements": "string",
  "reference_services": "string",
  "reference_interactions": "string"
}
```

A successful mock run response MUST contain, at minimum:

```json
{
  "ok": true,
  "run_id": "string",
  "systems": [],
  "service_metrics": [],
  "interaction_metrics": [],
  "best_results": [],
  "report_available": true
}
```

An error response MUST contain `ok: false`, a stable error `code`, an English `message`, and optional field or system details.

### Key Entities

- **SystemDefinition**: A user-provided decomposition target containing the system name, architecture target, textual requirements, reference services, reference interactions, and normalization map.
- **MockRun**: A deterministic simulated execution containing a run identifier, submitted system definitions, selected mock scenario, mock metrics, best-result summaries, and report availability.
- **ServiceMetric**: A result row identified by system and proposal with precision, recall, and F1-Score values.
- **InteractionMetric**: A result row identified by system and proposal with precision, recall, and F1-Score values.
- **BestResult**: A summary identifying the highest-scoring proposal for services and interactions for one system.
- **ReportContext**: The input and result data used to render the downloadable test PDF.

### Mock Scenarios

The backend MUST provide a testable way to select or trigger these scenarios without connecting to the real pipeline:

- **Success**: Returns complete, representative mock metrics and best-result rows.
- **LLM error**: Returns an internal simulated model failure with a stable error code and no result tables.
- **Low results**: Returns valid but low precision, recall, and F1-Score values so the UI can demonstrate poor outcomes as data rather than an exception.

The mock implementation MUST contain a clear future integration marker, for example:

```python
# TODO: Integrate with pipeline_runner here
```

## Success Criteria

### Measurable Outcomes

- **SC-001**: A first-time user can load the input page and see one valid system block without manual setup.
- **SC-002**: The interface accepts and renders up to ten system blocks, and never renders an eleventh block after a rejected add request.
- **SC-003**: A valid mocked run displays Services, Interactions, and Best Results data within one completed AJAX response, without invoking the real pipeline.
- **SC-004**: Every required empty field is identified in the frontend before a run request is sent, and the backend rejects the same invalid payload if submitted directly.
- **SC-005**: The success, LLM error, and low-results mock scenarios can each be demonstrated through the interface without code changes or external model credentials.
- **SC-006**: A successful report request returns a downloadable `application/pdf` response containing all required input and result sections plus a date/time footer.
- **SC-007**: The primary input and results workflows remain usable at desktop and mobile viewport widths using responsive Bootstrap layout behavior.
- **SC-008**: The reset action returns any populated session to exactly one empty system block without a full page reload.
- **SC-009**: No implementation change for this prototype modifies files outside `Interface/` or invokes the existing experimental pipeline.

## Assumptions

- The prototype is run locally and does not require authentication, multi-user persistence, or a production database.
- Bootstrap 5 may be loaded from a stable local asset or an explicitly documented CDN dependency during implementation.
- Mock run state may be held in memory for the lifetime of the local server; durable experiment storage is out of scope.
- The backend may generate a minimal valid PDF directly with the standard library or use a simple test-PDF strategy, provided the downloaded document contains the required sections.
- Reference services, reference interactions, and the normalization map are entered as text in this phase; parsing and evaluation semantics are represented by mock contracts rather than the real pipeline.
- Real pipeline integration will be designed later behind a separate adapter and will preserve the existing CLI experiment as a reproducible path.
- The current phase does not require production-grade security, deployment, observability, or concurrency guarantees.
