# Task 004: Add AJAX System Management

## Objective
Implement dynamic addition and removal of system blocks through AJAX with a strict maximum of ten systems.

## Files Affected

- `Interface/server.py`
- `Interface/static/js/app.js`
- `Interface/static/css/styles.css`
- `Interface/tests/test_server.py`
- `Interface/tests/test_contracts.py`

## Deliverables

- Complete `POST /api/systems` with current-count and maximum-count validation.
- Add `DELETE /api/systems/<index>` with index validation.
- Add `Add another system` and `Remove` browser actions.
- Keep one block when removal would leave zero systems.
- Update visible system count and limit feedback without a full page reload.

## Acceptance Criteria

- A new block is added through an AJAX request when fewer than ten exist.
- An eleventh block is rejected with an English limit message.
- A non-final block can be removed through AJAX.
- The only remaining block cannot be removed.
- Invalid indexes and invalid counts receive structured backend errors.
- System values already entered in other blocks remain intact after add/remove operations.

## Dependencies

- Depends on Tasks 002 and 003.
