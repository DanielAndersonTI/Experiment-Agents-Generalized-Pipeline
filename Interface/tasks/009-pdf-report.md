# Task 009: Generate the Test PDF Report

## Objective
Expose a backend route that generates a simple, formatted PDF report from the latest mocked decomposition.

## Files Affected

- `Interface/server.py`
- `Interface/static/index.html`
- `Interface/static/js/app.js`
- `Interface/tests/test_server.py`
- `Interface/tests/test_contracts.py`

## Deliverables

- Implement `GET /api/report/pdf` for the latest valid run context.
- Generate a valid downloadable `application/pdf` response using the approved local approach.
- Include each system name, requirements, reference services, reference interactions, normalization map, Services table, Interactions table, Best Results table, and date/time footer.
- Add the `Download Full Report (PDF)` browser action.
- Return a structured error when no report context exists.

## Acceptance Criteria

- A successful run enables or supports the PDF download action.
- The route returns a valid PDF content type and download filename.
- The downloaded document contains all required input and mock-result sections.
- Reports with multiple systems include every submitted system.
- No PDF content is sourced from the real pipeline or existing result directories.

## Dependencies

- Depends on Task 007 and Task 006.
