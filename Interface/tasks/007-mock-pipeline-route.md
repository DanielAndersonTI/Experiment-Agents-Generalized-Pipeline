# Task 007: Implement the Mock Pipeline Route

## Objective
Implement the AJAX execution route that validates input and returns deterministic simulated decomposition results without calling the real pipeline.

## Files Affected

- `Interface/server.py`
- `Interface/static/js/app.js`
- `Interface/tests/test_server.py`
- `Interface/tests/test_contracts.py`
- `Interface/README.md`

## Deliverables

- Implement `POST /api/pipeline/run`.
- Accept the system definitions and an optional mock scenario.
- Return `run_id`, submitted systems, service metrics, interaction metrics, best results, and report availability for success.
- Store the latest valid report context in memory.
- Add the future integration marker at the mock execution boundary:

```python
# TODO: Integrate with pipeline_runner here
```

- Explicitly avoid importing, executing, or modifying `main_fewshot.py` and the existing agents.

## Acceptance Criteria

- Valid requests return the documented success JSON shape.
- Results are deterministic enough for repeatable browser tests.
- The route never starts an LLM or the real multi-agent pipeline.
- Invalid payloads return structured English errors.
- The latest successful run can be used by the report route.
- The README explains how to exercise the mock scenario selection.

## Dependencies

- Depends on Tasks 002, 005, and 006.
