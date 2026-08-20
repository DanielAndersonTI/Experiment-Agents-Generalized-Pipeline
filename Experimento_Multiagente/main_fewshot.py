"""
Script Principal de Orquestração Multiagente – FEW-SHOT (Generalizado)

Este módulo expõe a função `executar_pipeline` que executa o pipeline
multiagente completo para um único sistema.

Os dados específicos de cada sistema (requisitos, serviços de referência,
interações de referência e mapa de normalização) são fornecidos como
argumentos da função, permitindo integração com a interface web.
"""

import os
import re
import sys
import csv
import json
import contextlib
import io
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

from crewai import LLM, Crew

sys.path.insert(0, str(Path(__file__).resolve().parent))

from agentes.agent1_architect_a_fs import criar_agente1, criar_task_arquitetura
from agentes.agent2_architect_b_fs import criar_agente2, criar_task_arquitetura_alternativa
from agentes.agent3_validator_fs import criar_agente3, criar_task_consolidacao
from agentes.agent4_refiner_fs import criar_agente4, criar_task_refinamento


RESULTS_ROOT = Path("result")


def criar_llm() -> LLM:
    """Cria o modelo LLM usando Google Gemini."""

    env_path = Path(__file__).parent / ".env"

    if env_path.exists():
        load_dotenv(env_path)
    else:
        load_dotenv()

    api_key = os.getenv("GOOGLE_API_KEY")
    model_name = os.getenv(
        "GOOGLE_MODEL",
        "gemini/gemini-flash-latest"
    )

    if not api_key:
        raise RuntimeError("GOOGLE_API_KEY not configured. Please define it in the .env file.")

    print(f"\n🔧 Inicializando modelo Gemini: {model_name}")

    llm = LLM(
        model=model_name,
        api_key=api_key,
        temperature=0.0,
        max_tokens=4096,
    )

    print(f"✓ Modelo {model_name} inicializado com sucesso")

    return llm


# ============================================
# Exemplo Few-Shot Genérico
# ============================================

EXAMPLE_GENERIC = """Catalog Service,Manage catalog entries;Update catalog item details;List available items,Order Service;Inventory Service
Order Service,Create orders from catalog items;View order history;Track order status,Catalog Service;Payment Service;Customer Service
Payment Service,Process order payments;Update payment status,Order Service
Customer Service,Register customer profiles;Update customer profiles;Retrieve customer profiles,Order Service;Auth Service
Auth Service,Authenticate user credentials;Issue access tokens,Customer Service"""


# ============================================
# Funções de Salvamento
# ============================================

def criar_diretorio_run(system_name: str, timestamp: str) -> Path:
    """Cria o diretório de saída generalizado para o sistema."""
    run_dir = RESULTS_ROOT / system_name.lower() / "result_generalized_fewshot" / f"run_{timestamp}"
    run_dir.mkdir(parents=True, exist_ok=True)
    return run_dir


def salvar_csv(filepath: Path, cabecalho: list, linhas: list):
    """Salva dados em formato CSV no caminho especificado."""
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(cabecalho)
        writer.writerows(linhas)


def salvar_proposta(run_dir: Path, sufixo: str, csv_texto: str):
    """Extrai as linhas do CSV gerado pelo agente e salva em arquivo."""
    linhas = []
    cabecalho = ["Microservice", "Responsibilities", "Communicates With"]
    for line in csv_texto.strip().split("\n"):
        line = line.strip()
        if not line or line.startswith("Microservice"):
            continue
        partes = [p.strip() for p in line.split(",")]
        if len(partes) >= 3:
            linhas.append(partes[:3])
    filepath = run_dir / f"{sufixo}.csv"
    salvar_csv(filepath, cabecalho, linhas)


def salvar_metricas(run_dir: Path, metricas: dict):
    """Salva métricas de serviços e interações em CSVs separados."""
    cab_serv = ["Proposta", "Precision", "Recall", "F1", "Match", "Gerados", "FP", "FN"]
    linhas_serv = []
    for key in ["proposta_a", "proposta_b", "consolidada"]:
        m = metricas.get(key)
        if m and "match_count" in m:
            linhas_serv.append([key, m["precision"], m["recall"], m["f1_score"],
                                m["match_count"], m["generated_count"],
                                ";".join(m["false_positives"]), ";".join(m["false_negatives"])])
    if linhas_serv:
        salvar_csv(run_dir / "metricas_servicos.csv", cab_serv, linhas_serv)

    cab_inter = ["Proposta", "Precision", "Recall", "F1", "TP", "Total_Gerado", "FP", "FN"]
    linhas_inter = []
    for key in ["proposta_a_inter", "proposta_b_inter", "consolidada_inter"]:
        m = metricas.get(key)
        if m:
            total_gerado = m["tp_count"] + m["fp_count"]
            linhas_inter.append([key.replace("_inter", ""), m["precision"], m["recall"],
                                 m["f1_score"], m["tp_count"], total_gerado,
                                 ";".join(f"{a}-{b}" for a, b in m["fp"]),
                                 ";".join(f"{a}-{b}" for a, b in m["fn"])])
    if linhas_inter:
        salvar_csv(run_dir / "metricas_interacoes.csv", cab_inter, linhas_inter)


def salvar_sumario_json(run_dir: Path, metricas: dict):
    """Salva um JSON completo com as métricas."""
    resumo = {
        "metricas": metricas,
        "arquivos": {
            "proposta_a": str(run_dir / "proposta_a.csv"),
            "proposta_b": str(run_dir / "proposta_b.csv"),
            "consolidada": str(run_dir / "consolidada.csv"),
            "metricas": str(run_dir / "metricas.csv"),
        }
    }
    filepath = run_dir / "sumario.json"
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(resumo, f, indent=2, ensure_ascii=False)


def extrair_csv_do_output(texto: str) -> str:
    """Extrai apenas as linhas que fazem parte do CSV da arquitetura."""
    linhas = texto.split('\n')
    csv_linhas = []
    started = False
    for line in linhas:
        stripped = line.strip()
        if not started:
            if stripped.startswith('Microservice,') or stripped.startswith('=== CONSOLIDATED ARCHITECTURE ==='):
                started = True
                if stripped.startswith('Microservice,'):
                    csv_linhas.append(stripped)
                continue
            if stripped.count(',') >= 2 and not any(c in stripped for c in ['└', '┌', '├', '│', '╭', '╰', 'Task', 'Agent:', 'Thought:', 'Begin!']):
                started = True
                csv_linhas.append(stripped)
                continue
            continue

        if (stripped.startswith('===') and 'CONSOLIDATED' in stripped) or \
           stripped.startswith('Note:') or \
           stripped.startswith('Key Observation') or \
           stripped.startswith('**') or \
           stripped.startswith('---'):
            if ',' in stripped:
                csv_linhas.append(stripped)
            continue
        if any(c in stripped for c in ['└', '┌', '├', '│', '╭', '╰', 'Task', 'Agent:', 'Thought:', 'Begin!']):
            continue
        if stripped.startswith('Note:') or stripped.startswith('Key Observation'):
            continue
        if re.match(r'^\d+\.\s', stripped):
            continue
        if ',' in stripped and not stripped.startswith('Thought:'):
            csv_linhas.append(stripped)
    return '\n'.join(csv_linhas)


def salvar_relatorio_md(run_dir: Path, system_name: str, metricas: dict):
    """Gera um relatório Markdown com as métricas e salva no diretório da execução."""
    linhas = [
        f"# Relatório de Execução – {system_name} (Few-Shot Generalizado)",
        "",
        f"**Data/hora:** {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}",
        "",
        "## Métricas de Serviços",
        "",
        "| Proposta | Precision | Recall | F1-Score | Match (TP) | Serviços Gerados |",
        "|----------|-----------|--------|----------|------------|------------------|",
    ]
    for key, label in [("proposta_a", "Proposta A (DDD)"),
                       ("proposta_b", "Proposta B (Alternativa)"),
                       ("consolidada", "Consolidada")]:
        m = metricas.get(key)
        if m and "match_count" in m:
            linhas.append(f"| {label} | {m['precision']:.4f} | {m['recall']:.4f} | {m['f1_score']:.4f} | {m['match_count']} | {m['generated_count']} |")
        else:
            linhas.append(f"| {label} | – | – | – | – | – |")

    linhas += [
        "",
        "## Métricas de Interações",
        "",
        "| Proposta | Precision | Recall | F1-Score | TP | Total Gerado |",
        "|----------|-----------|--------|----------|----|--------------|",
    ]
    for key, label in [("proposta_a_inter", "Proposta A (DDD)"),
                       ("proposta_b_inter", "Proposta B (Alternativa)"),
                       ("consolidada_inter", "Consolidada")]:
        m = metricas.get(key)
        if m:
            total = m["tp_count"] + m["fp_count"]
            linhas.append(f"| {label} | {m['precision']:.4f} | {m['recall']:.4f} | {m['f1_score']:.4f} | {m['tp_count']} | {total} |")
        else:
            linhas.append(f"| {label} | – | – | – | – | – |")

    filepath = run_dir / "report.md"
    with open(filepath, "w", encoding="utf-8") as f:
        f.write("\n".join(linhas))


# ============================================
# Funções de Avaliação
# ============================================

def parse_csv_architecture(csv_text: str):
    """Extrai nomes de serviços do CSV (não normaliza)."""
    services = []
    try:
        lines = str(csv_text).strip().split('\n')
        for line in lines:
            line = line.strip()
            if (not line or
                line.lower().startswith('microservice') or
                line.startswith('===') or
                line.startswith('- ') or
                line.startswith('#') or
                line.startswith('--') or
                line.startswith('**') or
                line.lower().startswith('thought:')):
                continue
            parts = [p.strip() for p in line.split(',')]
            if len(parts) >= 3:
                service_name = parts[0].lower().replace(' ', '-')
                if service_name:
                    services.append(service_name)
    except Exception as e:
        print(f"  ⚠ Erro ao parsear CSV: {e}")
    return services


def parse_csv_interactions(csv_text: str, name_map: dict) -> set:
    """Extrai pares de interações normalizados."""
    interactions = set()
    for line in csv_text.strip().split('\n'):
        line = line.strip()
        if not line or line.startswith('Microservice') or line.startswith('===') or line.startswith('-'):
            continue
        parts = [p.strip() for p in line.split(',')]
        if len(parts) >= 3:
            origem = normalize_service_name(parts[0], name_map)
            destinos_str = parts[2] if len(parts) == 3 else parts[2]
            destinos = [normalize_service_name(d.strip(), name_map) for d in destinos_str.split(';') if d.strip()]
            for destino in destinos:
                par = tuple(sorted([origem, destino]))
                interactions.add(par)
    return interactions


def evaluate_interactions(generated_set: set, reference_set: set):
    """Calcula métricas de interações (Precision, Recall, F1)."""
    tp = generated_set & reference_set
    fp = generated_set - reference_set
    fn = reference_set - generated_set

    precision = len(tp) / len(generated_set) if generated_set else 0.0
    recall = len(tp) / len(reference_set) if reference_set else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0

    return {
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1_score": round(f1, 4),
        "tp_count": len(tp),
        "fp_count": len(fp),
        "fn_count": len(fn),
        "tp": sorted(tp),
        "fp": sorted(fp),
        "fn": sorted(fn),
    }


def normalize_service_name(name: str, name_map: dict) -> str:
    """Normaliza um nome de serviço usando o mapa do sistema."""
    name = name.lower().strip()
    name = name.replace(' ', '-').replace('_', '-')
    name = name.removesuffix('-service')
    name = name.removesuffix('-microservice')
    name = name.removesuffix('-ms')
    name = name_map.get(name, name)
    return name


def calculate_metrics(generated_services, reference_services, name_map: dict):
    """Calcula Precision, Recall e F1-Score para serviços."""
    gen_normalized = set(normalize_service_name(s, name_map) for s in generated_services)
    ref_normalized = set(normalize_service_name(s, name_map) for s in reference_services)

    true_positives = gen_normalized & ref_normalized
    false_positives = gen_normalized - ref_normalized
    false_negatives = ref_normalized - gen_normalized

    precision = len(true_positives) / len(gen_normalized) if gen_normalized else 0.0
    recall = len(true_positives) / len(ref_normalized) if ref_normalized else 0.0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0

    return {
        "true_positives": sorted(true_positives),
        "false_positives": sorted(false_positives),
        "false_negatives": sorted(false_negatives),
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1_score": round(f1, 4),
        "generated_count": len(gen_normalized),
        "reference_count": len(ref_normalized),
        "match_count": len(true_positives),
    }


def print_evaluation_report(metrics, title: str = "Evaluation Report"):
    """Imprime relatório formatado de avaliação (mantido para uso futuro)."""
    print(f"\n{'='*60}")
    print(f"{title}")
    print(f"{'='*60}")
    print(f"\n📊 Métricas:")
    print(f"  Precision: {metrics['precision']:.4f} ({metrics['precision']*100:.2f}%)")
    print(f"  Recall:    {metrics['recall']:.4f} ({metrics['recall']*100:.2f}%)")
    print(f"  F1-Score:  {metrics['f1_score']:.4f} ({metrics['f1_score']*100:.2f}%)")
    print(f"\n📋 Detalhes:")
    print(f"  Serviços Gerados:  {metrics['generated_count']}")
    print(f"  Serviços Referência: {metrics['reference_count']}")
    print(f"  Match (TP): {metrics['match_count']}")
    print(f"  False Positives: {len(metrics['false_positives'])}")
    print(f"  False Negatives: {len(metrics['false_negatives'])}")

    if metrics['false_positives']:
        print(f"\n  ❌ False Positives (gerados mas não na referência):")
        for s in metrics['false_positives']:
            print(f"     - {s}")

    if metrics['false_negatives']:
        print(f"\n  ⚠ False Negatives (na referência mas não gerados):")
        for s in metrics['false_negatives']:
            print(f"     - {s}")

    if metrics['true_positives']:
        print(f"\n  ✅ True Positives (match):")
        for s in metrics['true_positives']:
            print(f"     - {s}")


# ============================================
# Função auxiliar para silenciar o CrewAI
# ============================================

def silent_kickoff(crew: Crew, inputs: dict):
    """Executa crew.kickoff silenciando stdout/stderr do CrewAI."""
    buf_out = io.StringIO()
    buf_err = io.StringIO()
    with contextlib.redirect_stdout(buf_out), contextlib.redirect_stderr(buf_err):
        return crew.kickoff(inputs=inputs)


def _format_metrics_for_prompt(service_metrics, interaction_metrics):
    """Formata métricas de serviços e interações para exibição no prompt do Agente 3."""
    if not service_metrics or not interaction_metrics:
        return "Metrics unavailable."

    return (
        "Services: "
        f"Precision={service_metrics['precision']:.4f}, "
        f"Recall={service_metrics['recall']:.4f}, "
        f"F1={service_metrics['f1_score']:.4f}\n"
        "Interactions: "
        f"Precision={interaction_metrics['precision']:.4f}, "
        f"Recall={interaction_metrics['recall']:.4f}, "
        f"F1={interaction_metrics['f1_score']:.4f}"
    )


# ============================================
# Execução do Pipeline
# ============================================

def _executar_experimento(llm, system_name: str, config: dict, timestamp: str, example: str):
    """
    Executa o experimento completo para um sistema.
    Retorna (resultados, metricas) com o terminal silencioso.
    """

    system_name = config["name"]
    requirements = config["requirements"]
    reference_services = config["reference_services"]
    interaction_reference = config["interaction_reference"]
    name_map = config["name_map"]

    run_dir = criar_diretorio_run(system_name, timestamp)

    agente1 = criar_agente1(llm)
    agente2 = criar_agente2(llm)
    agente3 = criar_agente3(llm)
    agente4 = criar_agente4(llm)

    task1 = criar_task_arquitetura(agente1)
    task2 = criar_task_arquitetura_alternativa(agente2)
    task3 = criar_task_consolidacao(agente3)
    task4 = criar_task_refinamento(agente4)

    resultados = {}

    # --- Executar Agente 1 ---
    try:
        crew1 = Crew(agents=[agente1], tasks=[task1], verbose=True)
        output_a = silent_kickoff(crew1, {"example": example, "requirements": requirements})
        output_a_limpo = extrair_csv_do_output(str(output_a))
        original_a = output_a_limpo

        try:
            crew4a = Crew(agents=[agente4], tasks=[task4], verbose=False)
            refined_a = silent_kickoff(crew4a, {
                "original_architecture": output_a_limpo,
                "requirements": requirements
            })
            output_a_limpo = extrair_csv_do_output(str(refined_a))

            refined_services = set(parse_csv_architecture(output_a_limpo))
            original_services = set(parse_csv_architecture(original_a))
            if original_services - refined_services:
                output_a_limpo = original_a
        except Exception:
            output_a_limpo = original_a

        resultados["proposta_a"] = output_a_limpo
        salvar_proposta(run_dir, "proposta_a", output_a_limpo)
    except Exception as e:
        print(f"✗ Erro no Agente 1: {str(e)}")
        resultados["proposta_a"] = None

    # --- Executar Agente 2 ---
    try:
        crew2 = Crew(agents=[agente2], tasks=[task2], verbose=False)
        output_b = silent_kickoff(crew2, {"example": example, "requirements": requirements})
        output_b_limpo = extrair_csv_do_output(str(output_b))
        original_b = output_b_limpo

        try:
            crew4b = Crew(agents=[agente4], tasks=[task4], verbose=False)
            refined_b = silent_kickoff(crew4b, {
                "original_architecture": output_b_limpo,
                "requirements": requirements
            })
            output_b_limpo = extrair_csv_do_output(str(refined_b))

            refined_services = set(parse_csv_architecture(output_b_limpo))
            original_services = set(parse_csv_architecture(original_b))
            if original_services - refined_services:
                output_b_limpo = original_b
        except Exception:
            output_b_limpo = original_b

        resultados["proposta_b"] = output_b_limpo
        salvar_proposta(run_dir, "proposta_b", output_b_limpo)
    except Exception as e:
        print(f"✗ Erro no Agente 2: {str(e)}")
        resultados["proposta_b"] = None

    # --- Calcular métricas preliminares de A e B para o Agente 3 ---
    metricas_pre = {}
    for key in ["proposta_a", "proposta_b"]:
        if resultados.get(key):
            try:
                services = parse_csv_architecture(resultados[key])
                metricas_pre[key] = calculate_metrics(services, reference_services, name_map)
            except Exception:
                metricas_pre[key] = None
        else:
            metricas_pre[key] = None

    for key in ["proposta_a", "proposta_b"]:
        if resultados.get(key):
            try:
                gen_inter = parse_csv_interactions(resultados[key], name_map)
                metricas_pre[f"{key}_inter"] = evaluate_interactions(gen_inter, interaction_reference)
            except Exception:
                metricas_pre[f"{key}_inter"] = None
        else:
            metricas_pre[f"{key}_inter"] = None

    # --- Executar Agente 3 (Validador) ---
    if resultados["proposta_a"] and resultados["proposta_b"]:
        try:
            metrics_a_text = _format_metrics_for_prompt(
                metricas_pre.get("proposta_a"),
                metricas_pre.get("proposta_a_inter"),
            )
            metrics_b_text = _format_metrics_for_prompt(
                metricas_pre.get("proposta_b"),
                metricas_pre.get("proposta_b_inter"),
            )

            crew3 = Crew(agents=[agente3], tasks=[task3], verbose=False)
            output_c = silent_kickoff(crew3, {
                "architecture_a": resultados["proposta_a"],
                "architecture_b": resultados["proposta_b"],
                "metrics_a": metrics_a_text,
                "metrics_b": metrics_b_text,
                "requirements": requirements,
            })
            output_c_limpo = extrair_csv_do_output(str(output_c))

            linhas = [l for l in output_c_limpo.split('\n') if l.strip() and not l.startswith('===')]
            if len(linhas) < 2:
                output_c_limpo = resultados["proposta_a"]

            resultados["consolidada"] = output_c_limpo
            salvar_proposta(run_dir, "consolidada", output_c_limpo)
        except Exception:
            resultados["consolidada"] = resultados["proposta_a"]
            salvar_proposta(run_dir, "consolidada", resultados["proposta_a"])
    else:
        resultados["consolidada"] = None

    # --- Avaliação final ---
    metricas = {}
    for key in ["proposta_a", "proposta_b", "consolidada"]:
        if resultados.get(key):
            services = parse_csv_architecture(resultados[key])
            metricas[key] = calculate_metrics(services, reference_services, name_map)
        else:
            metricas[key] = None

    for key in ["proposta_a", "proposta_b", "consolidada"]:
        if resultados.get(key):
            gen_inter = parse_csv_interactions(resultados[key], name_map)
            metricas[f"{key}_inter"] = evaluate_interactions(gen_inter, interaction_reference)
        else:
            metricas[f"{key}_inter"] = None

    salvar_metricas(run_dir, metricas)
    salvar_sumario_json(run_dir, metricas)
    salvar_relatorio_md(run_dir, system_name, metricas)

    return resultados, metricas


def executar_pipeline(system_name: str,
                      requirements: str,
                      reference_services: list,
                      interaction_reference: set,
                      name_map: dict,
                      example: str = EXAMPLE_GENERIC) -> tuple:
    """
    Função pública que executa o pipeline multiagente para um sistema.

    Args:
        system_name (str): Nome do sistema.
        requirements (str): Texto dos requisitos do sistema.
        reference_services (list): Lista de serviços de referência (ground truth).
        interaction_reference (set): Conjunto de pares de interações de referência.
        name_map (dict): Mapa de normalização de nomes.
        example (str): Exemplo Few-Shot genérico. Default: EXAMPLE_GENERIC.

    Returns:
        tuple: (resultados, metricas)
            - resultados: dict com 'proposta_a', 'proposta_b', 'consolidada'
            - metricas: dict com métricas de serviços e interações
    """
    llm = criar_llm()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    config = {
        "name": system_name,
        "requirements": requirements,
        "reference_services": reference_services,
        "interaction_reference": interaction_reference,
        "name_map": name_map,
    }
    resultados, metricas = _executar_experimento(llm, system_name, config, timestamp, example)
    return resultados, metricas