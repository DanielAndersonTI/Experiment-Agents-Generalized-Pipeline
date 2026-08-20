# Task 005: Validate Required Fields in the Frontend

## Objective
Prevent invalid decomposition submissions by validating every required system field before the run request is sent.

## Files Affected

- `Interface/static/index.html`
- `Interface/static/js/app.js`
- `Interface/static/css/styles.css`
- `Interface/tests/test_contracts.py`

## Deliverables

- Validate non-empty, non-whitespace values for all required text fields.
- Validate the selected architecture target.
- Display field-level or block-level English validation messages.
- Apply accessible invalid styling and focus behavior.
- Keep the entered values available for correction.

## Acceptance Criteria

- `Run Pipeline` does not send an AJAX run request when any required field is empty.
- Every invalid field has a clear English message.
- Valid values clear or bypass the corresponding validation state.
- Validation works independently for all system blocks up to the five-system limit.
- The frontend validation rules match the backend payload requirements.

## Dependencies

- Depends on Task 004.
