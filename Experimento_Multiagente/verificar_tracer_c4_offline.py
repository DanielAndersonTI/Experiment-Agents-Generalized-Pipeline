"""Verificação end-to-end do tracer no C4, sem chamadas reais de API.

Roda a configuração C4 completa (Agente 1 -> Agente 4 -> Agente 2.1 -> Agente 4
-> Agente 3 -> YAML determinístico) usando o CrewAI real, o event bus real e o
`execution_tracker` real. A única substituição é o método que fala com a API do
provider (Anthropic/Claude ou OpenAI-compatível/DeepSeek), que passa a devolver
um CSV fixo e a emitir o evento de conclusão com `usage` sintético.

O objetivo é confirmar dois pontos antes de gastar tokens no experimento:
1. o C4 executa de ponta a ponta (5 chamadas, mesma ordem do C1);
2. o `execution_metadata.json` separa corretamente `agent_1`, `agent_2_1`,
   `agent_3` e `agent_4` (o rótulo do Agente 2.1 vence o papel compartilhado
   "Software Architect").

Uso:
    python verificar_tracer_c4_offline.py
"""

import json
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

EXPERIMENT_DIR = Path(__file__).resolve().parent
if str(EXPERIMENT_DIR) not in sys.path:
    sys.path.insert(0, str(EXPERIMENT_DIR))

import main_fewshot as mf  # noqa: E402
from crewai.events.types.llm_events import LLMCallType  # noqa: E402
from crewai.llms.providers.anthropic.completion import AnthropicCompletion  # noqa: E402
from crewai.llms.providers.gemini.completion import GeminiCompletion  # noqa: E402
from crewai.llms.providers.openai.completion import OpenAICompletion  # noqa: E402

FAKE_CSV = (
    "Microservice,Responsibilities,Communicates With\n"
    "Alpha Service,Handle alpha work,Beta Service\n"
    "Beta Service,Handle beta work,Alpha Service"
)

FAKE_USAGE = {"prompt_tokens": 1200, "completion_tokens": 180, "total_tokens": 1380}

REQUIREMENTS = (
    "- The system must allow users to register records.\n"
    "- The system must allow users to consult and update records.\n"
    "- Every record change must be traceable.\n"
)

REFERENCE_SERVICES = ["Alpha Service", "Beta Service"]

EXPECTED_AGENTS = {"agent_1", "agent_2_1", "agent_3", "agent_4"}


def fake_handle_completion(self, *args, **kwargs):
    """Substitui a chamada à API mantendo a emissão de eventos.

    Cada provider chama `_handle_completion` com uma assinatura diferente
    (Anthropic e OpenAI por keyword/posição, Gemini com um parâmetro extra de
    config), então `from_agent` e `from_task` são localizados pelos atributos
    dos próprios objetos, evitando depender da ordem dos argumentos.
    """
    def _localizar(*atributos):
        for valor in list(args) + list(kwargs.values()):
            if valor is not None and all(hasattr(valor, atributo) for atributo in atributos):
                return valor
        return None

    from_agent = _localizar("role", "goal", "backstory")
    from_task = _localizar("description", "expected_output")
    self._emit_call_completed_event(
        response=FAKE_CSV,
        call_type=LLMCallType.LLM_CALL,
        from_task=from_task,
        from_agent=from_agent,
        usage=dict(FAKE_USAGE),
    )
    return FAKE_CSV


def main() -> int:
    # The provider is chosen by DAVINCI_LLM_PROVIDER; this only builds the LLM
    # object (clients are created lazily), so it is safe to run without network.
    print("Provider ativo:", mf.criar_llm().model)

    with tempfile.TemporaryDirectory() as temporary_dir:
        with patch.object(mf, "RESULTS_ROOT", Path(temporary_dir)), \
             patch.object(mf, "DEBUG_RAW_OUTPUT", False), \
             patch.object(AnthropicCompletion, "_handle_completion", fake_handle_completion), \
             patch.object(OpenAICompletion, "_handle_completion", fake_handle_completion), \
             patch.object(GeminiCompletion, "_handle_completion", fake_handle_completion):
            resultados, metricas = mf.executar_pipeline_c4(
                "smoke-offline",
                REQUIREMENTS,
                REFERENCE_SERVICES,
                set(),
                tracer_run_id="tracer-offline",
            )

        metadata_path = (
            Path(temporary_dir) / "results-tracer-tracer-offline" / "smoke-offline"
            / "execution_metadata.json"
        )
        if not metadata_path.is_file():
            print(f"FALHOU: {metadata_path} não foi criado.")
            return 1
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))

    print("Chamadas de LLM registradas:", metadata["llm_usage"]["total_calls"])
    print("Tokens totais registrados:", metadata["llm_usage"]["total_tokens"])
    print("\nResumo por agente:")
    print(json.dumps(metadata["agents"], indent=2, ensure_ascii=False))

    registrados = set(metadata["agents"])
    faltando = EXPECTED_AGENTS - registrados
    if faltando:
        print(f"\nFALHOU: agentes ausentes no tracer: {sorted(faltando)}")
        print(f"Encontrados: {sorted(registrados)}")
        return 1

    if metadata["llm_usage"]["total_tokens"] != len(metadata["calls"]) * FAKE_USAGE["total_tokens"]:
        print("\nFALHOU: soma de tokens inconsistente com o usage sintético.")
        return 1

    print("\nOK: C4 executou de ponta a ponta e o tracer separou "
          f"{sorted(registrados)}.")
    print("CSV consolidado salvo:", "sim" if resultados.get("consolidada") else "não")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
