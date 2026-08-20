# Task 008: Add Simulated Error Scenarios

## Objective
Provide explicit mock scenarios for backend failures so the interface can demonstrate error handling without external credentials or services.

## Files Affected

- `Interface/server.py`
- `Interface/static/index.html`
- `Interface/static/js/app.js`
- `Interface/static/css/styles.css`
- `Interface/tests/test_server.py`
- `Interface/tests/test_contracts.py`

## Deliverables

- Add a simulated credits/quota failure scenario with a stable error code and English message.
- Add a simulated agent or LLM failure scenario with a stable error code and English message.
- Add a low-results scenario that returns valid but low metrics.
- Show loading, error, retry, and stale-result protection states in the frontend.
- Prevent duplicate run requests while a request is pending.

## Acceptance Criteria

- Credits/quota failure displays an appropriate user-facing error.
- Agent/LLM failure displays an appropriate user-facing error and no false result tables.
- Low-results mode displays metrics and best-result data without being treated as a transport failure.
- Failed requests preserve input values for retry.
- The frontend handles malformed responses and network failures with an English fallback message.
- Automated or manual checks can trigger every scenario without code changes.

## Dependencies

- Depends on Task 007.
