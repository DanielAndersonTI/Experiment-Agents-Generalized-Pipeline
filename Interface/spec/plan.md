# Implementation Plan: VIRTUS Microservice Architecture Generation Interface

**Branch**: `001-virtus-architecture-interface` | **Date**: 2026-08-19 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `Interface/spec/spec.md`

## Summary

Implement a local web prototype for collecting up to five generalized system definitions, running a mocked microservice architecture decomposition, displaying mock metrics, and downloading a simple PDF report. The backend will use only Python's standard-library `http.server`; the frontend will use HTML, CSS, Bootstrap 5, and plain JavaScript with AJAX. No stage in this plan invokes or modifies the existing multi-agent pipeline.

All future real-pipeline integration will remain behind the mock execution boundary and will be marked in the relevant backend code with `# TODO: Integrate with pipeline_runner here` or equivalent. The implementation will remain entirely inside `Interface/`.

## Technical Context

**Language/Version**: Python 3.x; HTML5; CSS3; JavaScript ES6+

**Primary Dependencies**: Python standard library `http.server`, `json`, `datetime`, and PDF-support utilities selected during implementation; Bootstrap 5 for layout and components; no backend framework and no frontend framework

**Storage**: In-memory mock run context for the local server lifetime; no database and no modification of existing experiment result directories

**Testing**: Python standard-library tests or focused HTTP smoke checks, browser-based manual verification, and responsive viewport checks

**Target Platform**: Local Windows development environment with a Python runtime and a modern desktop or mobile browser

**Project Type**: Local web application prototype

**Performance Goals**: Initial page and static assets should load locally without perceptible delay; mock AJAX responses should complete promptly and provide a visible loading state during the request

**Constraints**: Maximum five systems per decomposition; all required fields validated; English-only interface; mock-only execution; no files outside `Interface/` changed; no calls to the real pipeline or LLM

**Scale/Scope**: One local user, up to five systems per run, one active in-memory report context, one input page and one results view

## Constitution Check

**Status: PASS**

- **Interface-first scope**: All implementation files will be created or modified under `Interface/` only.
- **Standard-library backend**: The server will use Python `http.server` and standard-library request, validation, and response handling.
- **Mocked pipeline boundary**: The run route will return deterministic mock data and will not import, execute, or modify `Experimento_Multiagente/`.
- **Future integration markers**: The mock execution boundary will contain `# TODO: Integrate with pipeline_runner here` to identify the later adapter location.
- **Complete prototype workflow**: The plan covers dynamic systems, run, reset, results, error scenarios, and PDF download.
- **VIRTUS identity**: CSS variables and Bootstrap overrides will implement the required navy, white, light-gray, and gold palette with uppercase headings.
- **Generalization**: Mock fixtures and UI structures will use generic system/proposal terminology and will not encode benchmark-specific architecture data.
- **Reproducibility protection**: Existing pipeline files, historical results, and experiment configuration remain untouched.

## Project Structure

### Documentation (this feature)

```text
Interface/spec/
├── spec.md       # Feature specification
└── plan.md       # This implementation plan
```

### Source Code (repository root)

```text
Interface/
├── server.py                 # Local http.server application and API routes
├── static/
│   ├── index.html            # Input page and results view shell
│   ├── css/
│   │   └── styles.css        # VIRTUS theme and responsive overrides
│   └── js/
│       └── app.js            # Form state, AJAX calls, rendering, and reset logic
├── tests/
│   ├── test_server.py        # Backend validation, mock routes, and PDF smoke tests
│   └── test_contracts.py     # Request/response shape checks
├── spec/
│   ├── spec.md              # Approved feature specification
│   └── plan.md              # This plan
└── README.md                 # Local startup and mock scenario instructions
```

**Structure Decision**: Use a single local web application rooted at `Interface/`. `server.py` owns HTTP delivery and mock API behavior. `static/` contains the browser-facing assets. `tests/` contains focused backend and contract checks. The existing `Experimento_Multiagente/` directory is an intentionally protected external dependency and is not part of this implementation structure.

## Implementation Stages

### 1. Establish the Interface Application Skeleton

**Objective**: Create the minimal local project structure and define ownership boundaries before adding behavior.

**Files affected**:

- `Interface/server.py`
- `Interface/static/index.html`
- `Interface/static/css/styles.css`
- `Interface/static/js/app.js`
- `Interface/tests/test_server.py`
- `Interface/tests/test_contracts.py`
- `Interface/README.md`

**Functionality delivered**:

- Directory layout for server, static assets, tests, and documentation.
- Local startup convention for the Python server.
- Explicit separation between browser assets, HTTP handling, mock execution, and tests.
- Documentation stating that the pipeline is not connected in this phase.

**Completion criterion**: The files exist within `Interface/`, the server can be started locally, and the repository remains free of changes outside `Interface/`.

### 2. Implement the Basic HTTP Server and Static Routes

**Objective**: Serve the frontend and establish the standard-library HTTP foundation.

**Files affected**:

- `Interface/server.py`
- `Interface/static/index.html`
- `Interface/tests/test_server.py`

**Functionality delivered**:

- `GET /` serves the input page.
- `GET /static/<asset>` serves HTML, CSS, and JavaScript assets safely from the Interface static directory.
- JSON response helpers, request-body parsing, status handling, and common error formatting.
- Protection against serving paths outside the static directory.
- A local server entry point suitable for manual browser testing.

**Completion criterion**: Opening the local server URL displays the page, static assets load successfully, unsupported paths return a structured HTTP error, and no web framework is required.

### 3. Build the Input Page and Dynamic System Blocks

**Objective**: Implement the initial form and the complete system-definition input model.

**Files affected**:

- `Interface/static/index.html`
- `Interface/static/css/styles.css`
- `Interface/static/js/app.js`

**Functionality delivered**:

- One system block rendered on initial load.
- Fields for system name, architecture target, requirements, reference services, reference interactions, and name normalization map.
- `Microservices` as the only enabled architecture target.
- English labels, placeholders, descriptions, required indicators, and accessible form associations.
- Add and remove controls with a visible count or limit state.
- Client-side state model for up to five systems.

**Completion criterion**: A user can fill one block, see all required fields, add blocks until five, and cannot select an unsupported architecture target.

### 4. Add AJAX System Management and Validation

**Objective**: Connect dynamic block operations and input validation to the local backend contract.

**Files affected**:

- `Interface/server.py`
- `Interface/static/js/app.js`
- `Interface/static/css/styles.css`
- `Interface/tests/test_server.py`
- `Interface/tests/test_contracts.py`

**Functionality delivered**:

- `POST /api/systems` returns an empty system-block model and enforces the five-system limit.
- `DELETE /api/systems/<index>` validates indexes and prevents deletion of the final block.
- Frontend AJAX handlers add and remove blocks without a full page reload.
- Frontend validation for whitespace-only required fields and unsupported targets.
- Backend validation for malformed JSON, zero systems, more than five systems, missing fields, and invalid targets.
- English field-level and request-level error messages.

**Completion criterion**: Add/remove flows work without reload, invalid input prevents pipeline submission, and direct invalid API requests receive stable structured errors.

### 5. Implement the Mock Pipeline Run Boundary

**Objective**: Provide a deterministic simulated execution that exercises the full run workflow without the real pipeline.

**Files affected**:

- `Interface/server.py`
- `Interface/static/js/app.js`
- `Interface/tests/test_server.py`
- `Interface/tests/test_contracts.py`
- `Interface/README.md`

**Functionality delivered**:

- `POST /api/pipeline/run` accepts the defined system payload and an optional mock scenario.
- Deterministic success fixtures containing service metrics, interaction metrics, best results, run identifier, and report availability.
- Simulated `llm_error` response with a stable error code and no result tables.
- Simulated `low_results` response containing valid low metric values.
- In-memory storage of the most recent valid run context for report generation.
- Explicit future integration boundary comment:

```python
# TODO: Integrate with pipeline_runner here
```

- No import or invocation of `main_fewshot.py` or any agent module.

**Completion criterion**: Valid requests return the documented mock response, all three scenarios can be selected for testing, and inspection confirms that the real multi-agent pipeline is never called.

### 6. Build the Results View and Loading/Error States

**Objective**: Render mock execution output in a clear, responsive results workflow.

**Files affected**:

- `Interface/static/index.html`
- `Interface/static/js/app.js`
- `Interface/static/css/styles.css`

**Functionality delivered**:

- Results view or results section with Services, Interactions, and Best Results tables.
- Required columns: System, Proposal, Precision, Recall, and F1-Score.
- Per-system best proposal summaries for services and interactions.
- Empty-state handling for missing result arrays.
- Loading indicator during run requests.
- Duplicate-submit prevention while a request is pending.
- Recovery actions or navigation back to input after errors.
- Correct display of low metric results as valid output rather than a transport failure.

**Completion criterion**: A success response produces readable tables for every submitted system; LLM errors and network failures produce English error states; loading and retry behavior are visible and coherent.

### 7. Implement Reset and PDF Test Reporting

**Objective**: Complete the repeatable prototype workflow with reset and report export.

**Files affected**:

- `Interface/server.py`
- `Interface/static/index.html`
- `Interface/static/js/app.js`
- `Interface/static/css/styles.css`
- `Interface/tests/test_server.py`
- `Interface/tests/test_contracts.py`

**Functionality delivered**:

- `New Decomposition` clears all values and returns to exactly one empty system block without a full reload.
- `GET /api/report/pdf` generates a valid downloadable test PDF from the latest run context.
- PDF includes system names, submitted requirements, reference services, reference interactions, normalization maps, mock Services/Interactions/Best Results tables, and a date/time footer.
- Appropriate response headers identify the document as `application/pdf` and provide a download filename.
- Missing report context returns a structured error instead of an empty or stale document.

**Completion criterion**: Reset works from both input and results states, and the PDF opens as a test report containing all required sections for one or multiple systems.

### 8. Apply VIRTUS Styling and Responsive Behavior

**Objective**: Make the complete workflow visually consistent and usable on desktop and mobile screens.

**Files affected**:

- `Interface/static/index.html`
- `Interface/static/css/styles.css`
- `Interface/static/js/app.js`

**Functionality delivered**:

- CSS variables for navy `#0A1E5C`, white `#FFFFFF`, light gray `#F2F2F2`, and gold `#E9C46A`.
- Bootstrap 5 grid, form, button, alert, table, and responsive utilities.
- Sans-serif typography and uppercase headings.
- Responsive system blocks, action controls, tables, alerts, and loading state.
- Visual distinction between primary actions, destructive removal, validation errors, and successful results.
- English-only visible text and accessible focus/label states.

**Completion criterion**: The main input and results workflows remain usable at desktop and mobile viewport widths, and the interface visibly follows the VIRTUS palette and typography rules.

### 9. Run End-to-End Prototype Validation and Document Operation

**Objective**: Verify every acceptance flow and record how the mock prototype is run.

**Files affected**:

- `Interface/tests/test_server.py`
- `Interface/tests/test_contracts.py`
- `Interface/README.md`

**Functionality delivered**:

- Backend tests for static routes, add/remove limits, validation, success, LLM error, low results, and PDF responses.
- Contract tests for success and error JSON shapes.
- Manual browser checklist for initial form, five-system boundary, reset, loading, results tables, and PDF download.
- Desktop and mobile responsive checks.
- Verification that no real pipeline import, process, or file modification occurs.
- Startup instructions and mock scenario instructions in the README.

**Completion criterion**: All spec acceptance scenarios pass through automated or documented manual checks, the three mock scenarios are demonstrable without credentials, and a final scope check confirms that only `Interface/` changed.

## Future Integration Boundary

Real integration is explicitly out of scope for this plan. The later implementation MUST replace or extend only the mock execution boundary in `Interface/server.py` with an adapter that translates the web request into the existing pipeline's approved callable contract. The integration location MUST retain a clear marker such as:

```python
# TODO: Integrate with pipeline_runner here
```

The future adapter MUST NOT require changes to the existing agent modules and MUST preserve the existing CLI experiment as a separately reproducible execution path. No task in this plan may import or execute `Experimento_Multiagente/main_fewshot.py`.

## Dependencies and Ordering

1. Stage 1 establishes the project skeleton.
2. Stage 2 must precede browser workflow work because it provides the server and static delivery.
3. Stage 3 may begin after the static shell exists, but the complete dynamic form depends on Stage 4 contracts.
4. Stage 4 must precede the run flow because it defines shared validation and AJAX conventions.
5. Stage 5 must precede Stage 6 because the results view consumes the mock response schema.
6. Stage 7 depends on the stored mock run context from Stage 5.
7. Stage 8 can proceed alongside Stages 6 and 7 after the initial HTML structure exists, but final responsive validation waits for all views.
8. Stage 9 is the final validation gate after all implementation stages.

## Complexity Tracking

No constitution violations are planned. The separate backend, static asset, and test files are the minimum structure needed to keep HTTP handling, browser behavior, mock contracts, and validation independently testable while preserving the protected experimental pipeline.
