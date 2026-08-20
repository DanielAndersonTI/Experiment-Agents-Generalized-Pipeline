# Task 006: Build the Mock Results View

## Objective
Create the browser view that renders service, interaction, and best-result data from a defined mock response.

## Files Affected

- `Interface/static/index.html`
- `Interface/static/js/app.js`
- `Interface/static/css/styles.css`

## Deliverables

- Add a Services table with System, Proposal, Precision, Recall, and F1-Score columns.
- Add an Interactions table with the same columns.
- Add a Best Results section grouped by system.
- Render empty states for empty result collections.
- Add navigation between input and results states without requiring a real pipeline.

## Acceptance Criteria

- A representative mock response renders all three result sections correctly.
- Every submitted system can appear in the results view.
- Precision, Recall, and F1-Score values are displayed as returned.
- Low values are rendered as valid results rather than hidden or converted to errors.
- The results view contains English text and remains usable on narrow screens.

## Dependencies

- Depends on Tasks 003 and 005.
- The run response shape from Task 007 must remain compatible with this view.
