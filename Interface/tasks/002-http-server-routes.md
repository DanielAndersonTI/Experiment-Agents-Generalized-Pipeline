# Task 002: Implement the Basic HTTP Server and Routes

## Objective
Implement the local Python standard-library HTTP server and the initial GET/POST route foundation.

## Files Affected

- `Interface/server.py`
- `Interface/static/index.html`
- `Interface/tests/test_server.py`

## Deliverables

- Serve `GET /` with the initial HTML page.
- Serve static assets under `GET /static/<asset>`.
- Add JSON request parsing and structured JSON response helpers.
- Add the initial `POST /api/systems` route for requesting an empty system-block model.
- Add safe handling for unsupported paths and malformed request bodies.

## Acceptance Criteria

- The local server starts with Python's `http.server` and no web framework.
- `GET /` returns the input page with a successful response.
- Static CSS and JavaScript assets load through the server.
- `POST /api/systems` returns a valid empty block response.
- Invalid routes and malformed JSON return structured errors.
- The server does not import or execute the real pipeline.

## Dependencies

- Depends on Task 001.
