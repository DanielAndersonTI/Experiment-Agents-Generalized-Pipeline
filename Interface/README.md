# DAVINCI Architect

This local prototype collects generalized system requirements and displays microservice architecture results from the existing pipeline. It uses Python's standard-library HTTP server. The PDF route remains a local report boundary while full persisted-artifact integration is developed.

## Local startup

From the repository root, run:

```powershell
python Interface/server.py
```

Open <http://127.0.0.1:8000/> in a browser. Stop the server with `Ctrl+C`.

## Browser workflow

1. Complete the required fields in the first system block.
2. Use `ADD ANOTHER SYSTEM` to add up to five systems.
3. Choose `RUN PIPELINE` to run the real pipeline for each submitted system.
4. Review Services, Interactions, and Best Results.
5. Select `DOWNLOAD FULL REPORT (PDF)` after a successful run.
6. Select `NEW DECOMPOSITION` to reset the form.

Real LLM and agent errors are returned as structured results and displayed on the results page, including partial results when available. The PDF route is marked with `# TODO: Integrate full PDF later`.

## API routes

- `GET /` serves the interface.
- `GET /static/<asset>` serves frontend assets.
- `POST /api/systems` creates an empty system-block model.
- `DELETE /api/systems/<index>` validates removal of a system block.
- `POST /api/pipeline/run` executes the real pipeline for each submitted system.
- `GET /api/report/pdf` downloads the latest successful architecture report.

## Testing

From the repository root, run:

```powershell
python -m unittest discover -s Interface/tests -p "test_*.py"
```

No external model credentials or pipeline dependencies are required.
