"""Adapter between web input data and the real generalized pipeline."""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
EXPERIMENT_DIR = PROJECT_ROOT / "Experimento_Multiagente"
if str(EXPERIMENT_DIR) not in sys.path:
    sys.path.insert(0, str(EXPERIMENT_DIR))

try:
    from main_fewshot import executar_pipeline  # noqa: E402
except ModuleNotFoundError:
    executar_pipeline = None

from .parsers import (
    parse_name_map,
    parse_reference_interactions,
    parse_reference_services,
)


def _error_message(error: Exception, agent: str | None = None) -> str:
    message = str(error).lower()
    if "credit" in message or "api" in message or "google_api_key" in message:
        return "LLM request failed. Please check your API credits and try again."
    if agent:
        return f"The pipeline encountered an error while running {agent}."
    return str(error) or "The pipeline could not be completed."


def run_real_pipeline(system_data: dict) -> dict:
    """Parse one interface system and execute the real pipeline adapter."""
    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    try:
        system_name = system_data["system_name"].strip()
        requirements = system_data["requirements"].strip()
        reference_services = parse_reference_services(system_data["reference_services"])
        interaction_reference = parse_reference_interactions(system_data["reference_interactions"])
        name_map = parse_name_map(system_data["name_normalization_map"])

        global executar_pipeline
        if executar_pipeline is None:
            from main_fewshot import executar_pipeline as pipeline_entrypoint
            executar_pipeline = pipeline_entrypoint

        # TODO: Integrate with pipeline_runner here
        results, metrics = executar_pipeline(
            system_name,
            requirements,
            reference_services,
            interaction_reference,
            name_map,
        )
        f1_values = [
            metric["f1_score"]
            for key, metric in metrics.items()
            if isinstance(metric, dict)
            and (key in {"proposta_a", "proposta_b", "consolidada"} or key.endswith("_inter"))
            and isinstance(metric.get("f1_score"), (int, float))
        ]
        warning = None
        if f1_values and max(f1_values) < 0.40:
            warning = "Low agreement with the reference architecture. This may indicate incomplete or inconsistent requirements."
        return {
            "ok": True,
            "run_id": run_id,
            "metrics": metrics,
            "results": results,
            "warning": warning,
        }
    except KeyError as error:
        return {"ok": False, "run_id": run_id, "metrics": {}, "error": f"Missing required field: {error.args[0]}."}
    except Exception as error:
        agent = getattr(error, "agent", None)
        return {"ok": False, "run_id": run_id, "metrics": {}, "error": _error_message(error, agent)}
