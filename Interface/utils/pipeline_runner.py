"""Adapter between web input data and the real generalized pipeline."""

from __future__ import annotations

import sys
import traceback
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
EXPERIMENT_DIR = PROJECT_ROOT / "Experimento_Multiagente"
if str(EXPERIMENT_DIR) not in sys.path:
    sys.path.insert(0, str(EXPERIMENT_DIR))


try:
    from main_fewshot import (
        executar_pipeline,
        executar_pipeline_c0,
        executar_pipeline_c2,
        executar_pipeline_c3,
    )
except ModuleNotFoundError:
    executar_pipeline = None
    executar_pipeline_c0 = None
    executar_pipeline_c2 = None
    executar_pipeline_c3 = None

from .parsers import (
    parse_reference_interactions,
    parse_reference_services,
)


def _error_message(error: Exception, agent: str | None = None) -> str:
    message = str(error).lower()
    if "credit" in message or "api" in message or "deepseek_api_key" in message:
        return "LLM request failed. Please check your API credits and try again."
    if agent:
        return f"The pipeline encountered an error while running {agent}."
    return str(error) or "The pipeline could not be completed."


def run_real_pipeline(system_data: dict, tracer_run_id: str | None = None) -> dict:
    """Parse one interface system and execute the real pipeline adapter."""
    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    try:
        system_name = system_data["system_name"].strip()
        requirements = system_data["requirements"].strip()
        reference_services = parse_reference_services(system_data["reference_services"])
        interaction_reference = parse_reference_interactions(system_data["reference_interactions"])

       
        global executar_pipeline, executar_pipeline_c0, executar_pipeline_c2, executar_pipeline_c3

        mode = str(system_data.get("mode", "c0")).lower()

        if mode == "c1":
            
            if executar_pipeline is None:
                from main_fewshot import executar_pipeline as pipeline_entrypoint
                executar_pipeline = pipeline_entrypoint
            pipeline_entrypoint = executar_pipeline

        elif mode == "c2":
            if executar_pipeline_c2 is None:
                from main_fewshot import executar_pipeline_c2 as pipeline_entrypoint
                executar_pipeline_c2 = pipeline_entrypoint
            pipeline_entrypoint = executar_pipeline_c2

        elif mode == "c3":
            if executar_pipeline_c3 is None:
                from main_fewshot import executar_pipeline_c3 as pipeline_entrypoint
                executar_pipeline_c3 = pipeline_entrypoint
            pipeline_entrypoint = executar_pipeline_c3

        else:
           
            if executar_pipeline_c0 is None:
                from main_fewshot import executar_pipeline_c0 as pipeline_entrypoint
                executar_pipeline_c0 = pipeline_entrypoint
            pipeline_entrypoint = executar_pipeline_c0

        results, metrics = pipeline_entrypoint(
            system_name,
            requirements,
            reference_services,
            interaction_reference,
            tracer_run_id=tracer_run_id,
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
        traceback.print_exc()
        agent = getattr(error, "agent", None)
        return {"ok": False, "run_id": run_id, "metrics": {}, "error": _error_message(error, agent)}