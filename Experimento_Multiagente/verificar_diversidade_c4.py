"""Verificação de diversidade do C4 (Proposta A vs Proposta B).

Executa apenas as duas etapas de proposta independente da configuração C4
(Agente 1 e Agente 2.1) com o LLM real, sem refinamento nem consolidação, para
checar se o Few-Shot distinto do Agente 2.1 produz realmente uma segunda
arquitetura diferente da Proposta A. Custa duas chamadas por sistema, em vez das
cinco chamadas do pipeline completo (útil como smoke test antes da rodada
completa do C4).

Uso:
    python verificar_diversidade_c4.py                       # sistema padrão: 7ep
    python verificar_diversidade_c4.py acmeair
    python verificar_diversidade_c4.py 7ep --espelhar-exemplo

`--espelhar-exemplo` reproduz o comportamento anterior ao ajuste, em que o
Agente 2.1 recebia o mesmo Few-Shot do Agente 1 (EXAMPLE_GENERIC), e serve para
demonstrar que as duas propostas tendem a coincidir nesse cenário.
"""

import argparse
import sys
from pathlib import Path

EXPERIMENT_DIR = Path(__file__).resolve().parent
if str(EXPERIMENT_DIR) not in sys.path:
    sys.path.insert(0, str(EXPERIMENT_DIR))

from crewai import Crew  # noqa: E402

import main_fewshot as mf  # noqa: E402
from agentes.agent1_architect_a_fs import criar_agente1, criar_task_arquitetura  # noqa: E402
from agentes.agent2_1architect_b_fs import (  # noqa: E402
    criar_agente2_1,
    criar_task_arquitetura as criar_task_arquitetura_2_1,
)

INPUTS_DIR = EXPERIMENT_DIR / "Dates-FSE-2026" / "davinci_inputs"


def carregar_sistema(nome: str):
    """Lê os requisitos e os serviços de referência de um sistema do benchmark."""
    base = INPUTS_DIR / nome
    if not base.is_dir():
        disponiveis = sorted(path.name for path in INPUTS_DIR.iterdir() if path.is_dir())
        raise SystemExit(f"Sistema '{nome}' não encontrado. Disponíveis: {', '.join(disponiveis)}")

    requirements = (base / "requirements.txt").read_text(encoding="utf-8").strip()
    reference_services = [
        line.strip()
        for line in (base / "reference_services.txt").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    return requirements, reference_services


def gerar_proposta(llm, requirements: str, example: str, criar_agente, criar_task) -> str:
    """Roda uma única crew de proposta (sem refino) e devolve o CSV puro."""
    agente = criar_agente(llm)
    task = criar_task(agente)
    crew = Crew(agents=[agente], tasks=[task], verbose=False)
    saida = mf.silent_kickoff(crew, {"example": example, "requirements": requirements})
    return mf.extrair_csv_do_output(mf.normalizar_output_llm(str(saida)))


def nomes_normalizados(csv_texto: str) -> list:
    return [mf.normalize_service_name(nome) for nome in mf.parse_csv_architecture(csv_texto)]


def jaccard(conjunto_a: set, conjunto_b: set) -> float:
    uniao = conjunto_a | conjunto_b
    return len(conjunto_a & conjunto_b) / len(uniao) if uniao else 0.0


def main() -> int:
    parser = argparse.ArgumentParser(description="Compara a Proposta A (Agente 1) e a Proposta B (Agente 2.1) do C4.")
    parser.add_argument("sistema", nargs="?", default="7ep", help="sistema do benchmark (padrão: 7ep)")
    parser.add_argument(
        "--espelhar-exemplo",
        action="store_true",
        help="usa o mesmo Few-Shot do Agente 1 na Proposta B (comportamento anterior ao ajuste)",
    )
    args = parser.parse_args()

    requirements, reference_services = carregar_sistema(args.sistema)
    exemplo_a = mf.EXAMPLE_GENERIC
    exemplo_b = mf.EXAMPLE_GENERIC if args.espelhar_exemplo else mf.EXAMPLE_ARCHITECT_B

    print(f"Sistema: {args.sistema}")
    print(f"Few-shot A (Agente 1): {len(exemplo_a)} chars")
    print(f"Few-shot B (Agente 2.1): {len(exemplo_b)} chars"
          f" ({'EXAMPLE_GENERIC (espelhado)' if args.espelhar_exemplo else 'EXAMPLE_ARCHITECT_B'})")

    llm = mf.criar_llm()
    proposta_a = gerar_proposta(llm, requirements, exemplo_a, criar_agente1, criar_task_arquitetura)
    proposta_b = gerar_proposta(
        llm, requirements, exemplo_b, criar_agente2_1, criar_task_arquitetura_2_1
    )

    servicos_a = nomes_normalizados(proposta_a)
    servicos_b = nomes_normalizados(proposta_b)
    metricas_a = mf.calculate_metrics(servicos_a, reference_services)
    metricas_b = mf.calculate_metrics(servicos_b, reference_services)

    print("\n=== Proposta A (Agente 1) ===")
    print(proposta_a)
    print("\n=== Proposta B (Agente 2.1) ===")
    print(proposta_b)

    print("\n=== Comparação ===")
    print(f"Serviços A: {servicos_a}")
    print(f"Serviços B: {servicos_b}")
    print(f"Jaccard(A, B): {jaccard(set(servicos_a), set(servicos_b)):.2f}")
    print(f"CSV idêntico: {'sim' if proposta_a.strip() == proposta_b.strip() else 'não'}")
    print(f"F1 de A vs referência: {metricas_a['f1_score']:.4f}")
    print(f"F1 de B vs referência: {metricas_b['f1_score']:.4f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
