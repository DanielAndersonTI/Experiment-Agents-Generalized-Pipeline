# Task 001: Create the Interface Project Skeleton

## Objective
Create the initial directory and file structure for the VIRTUS web prototype without touching any file outside `Interface/`.

## Files Affected

- `Interface/server.py`
- `Interface/static/index.html`
- `Interface/static/css/styles.css`
- `Interface/static/js/app.js`
- `Interface/tests/test_server.py`
- `Interface/tests/test_contracts.py`
- `Interface/README.md`

## Deliverables

- Create the server, static asset, test, and documentation locations defined in `spec/plan.md`.
- Document local startup expectations and the mock-only scope.
- Keep the future pipeline adapter boundary isolated to the Interface backend.

## Acceptance Criteria

- All listed paths exist under `Interface/`.
- The structure contains no dependency on `Experimento_Multiagente/`.
- The README states that the real pipeline is not connected in this phase.
- No file outside `Interface/` is created or modified.

## Dependencies

- None. This is the first implementation task.
