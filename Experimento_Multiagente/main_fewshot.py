"""
Script Principal de Orquestração Multiagente – FEW-SHOT (Generalizado)

Este módulo expõe a função `executar_pipeline` que executa o pipeline
multiagente completo para um único sistema.

Os dados específicos de cada sistema (requisitos, serviços de referência e
interações de referência) são fornecidos como argumentos da função.
O mapa de normalização foi substituído por uma avaliação semântica
automática aplicada somente no cálculo das métricas.
"""

import os
import re
import sys
import csv
import json
import hashlib
import traceback
import contextlib
import io
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Windows terminals, redirected streams and the web interface may expose a
# non-UTF-8 stdout (e.g. cp1252). The informational prints below use symbols
# such as the wrench and the check mark, and an unencodable character would
# raise UnicodeEncodeError and abort the whole run. Force an UTF-8 stream with
# replacement as a fallback so the pipeline never fails while logging.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        try:
            _stream.reconfigure(errors="replace")
        except Exception:
            pass

from crewai import LLM, Crew

sys.path.insert(0, str(Path(__file__).resolve().parent))

from agentes.agent1_architect_a_fs import criar_agente1, criar_task_arquitetura
from agentes.agent2_architect_b_fs import criar_agente2, criar_task_arquitetura_alternativa
from agentes.agent3_validator_fs import criar_agente3, criar_task_consolidacao
from agentes.agent4_refiner_fs import criar_agente4, criar_task_refinamento
from agentes.agent5_architectural_spec_fs import gerar_especificacao_yaml
from execution_tracker import track_execution

# Optional: agent-level labels (added for the C4 configuration). Kept in a
# try/except so the pipeline keeps working with an older tracking module.
try:
    from execution_tracker import reset_agent_label, set_agent_label
except Exception:  # pragma: no cover
    reset_agent_label = None
    set_agent_label = None


# ---------------------------------------------------------------------------
# Agente 2.1 (configuração C4)
# ---------------------------------------------------------------------------
# Segunda proposta independente, usada apenas pela configuração C4. O import
# segue o mesmo padrão dos outros agentes; o try/except garante que um problema
# nesse arquivo não derrube C0, C1, C2 e C3.
try:
    from agentes.agent2_1architect_b_fs import (
        criar_agente2_1,
        criar_task_arquitetura as criar_task_arquitetura_2_1,
    )
except Exception as _erro_agente2_1:  # pragma: no cover
    print(f"⚠ Agente 2.1 indisponível: {type(_erro_agente2_1).__name__}: {_erro_agente2_1}")
    criar_agente2_1 = None
    criar_task_arquitetura_2_1 = None


RESULTS_ROOT = Path("result")

SYNONYM_MAP = {
    "auth": "authentication",
    "authentication": "authentication",
    "login": "authentication",
    "account": "account",
    "customer": "customer",
    "client": "customer",
    "user": "user",
    "catalog": "catalog",
    "product": "catalog",
    "book": "catalog",
    "inventory": "inventory",
    "stock": "inventory",
    "cart": "cart",
    "shopping": "cart",
    "order": "order",
    "purchase": "order",
    "payment": "payment",
    "billing": "payment",
    "delivery": "delivery",
    "shipping": "delivery",
    "logistics": "delivery",
    "media": "media",
    "video": "media",
    "movie": "media",
    "film": "media",
    "reader": "reader",
    "borrower": "reader",
    "loan": "loan",
    "lending": "loan",
    "math": "utility",
    "demo": "utility",
    "environment": "environment",
    "administration": "administration",
    "admin": "administration",
    "management": "management",
    "cargo": "cargo",
    "route": "route",
    "tracking": "tracking",
    "event": "event",
    "integration": "integration",
    "location": "location",
    "voyage": "voyage",
    "network": "network",
    "investor": "investor",
    "portfolio": "portfolio",
    "trading": "trading",
    "market": "market",
    "simulation": "simulation",
    "planejamento": "planning",
    "rota": "route",
    "rotas": "route",
    "evento": "event",
    "eventos": "event",
    "carga": "cargo",
    "cargas": "cargo",
    "rastreamento": "tracking",
    "acompanhamento": "tracking",
    "integração": "integration",
    "integracao": "integration",
    "localidade": "location",
    "localidades": "location",
    "viagem": "voyage",
    "viagens": "voyage",
    "owner": "owner",
    "animal": "pet",
    "pet": "pet",
    "workforce": "workforce",
    "proposal": "proposal",
    "billing": "billing",
    "commissioning": "commissioning",
    "reporting": "reporting",
    "notification": "notification",
    "storage": "storage",
    "content": "content",
    "identity": "identity",
    "access": "access",
    "reservation": "booking",
    "booking": "booking",
    "administration": "administration",
}

def criar_llm() -> LLM:
    """Create the LLM shared by every agent of every configuration (C0-C4).

    The provider comes from DAVINCI_LLM_PROVIDER in the .env file:

    - "anthropic" (default): Claude, model from CLAUDE_MODEL;
    - "deepseek": DeepSeek, model from DEEPSEEK_MODEL;
    - "gemini": Google Gemini, model from GOOGLE_MODEL.

    Everything else stays identical across providers (temperature 0.0,
    max_tokens, prompts, few-shots and the C0-C4 definitions), so the same
    experiment can be repeated with another model. DeepSeek is
    OpenAI-compatible and CrewAI routes `deepseek/<model>` to its native
    `openai_compatible` provider: base URL https://api.deepseek.com/v1
    (overridable with DEEPSEEK_BASE_URL) and API key from DEEPSEEK_API_KEY.
    """
    env_path = Path(__file__).parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)
    else:
        load_dotenv()

    provider = os.getenv("DAVINCI_LLM_PROVIDER", "anthropic").strip().lower()
    if provider in ("claude", "anthropic"):
        provider = "anthropic"
    elif provider == "google":
        provider = "gemini"
    elif provider not in ("deepseek", "gemini"):
        raise RuntimeError(
            f"DAVINCI_LLM_PROVIDER inválido: '{provider}'. Use 'anthropic', 'deepseek' ou 'gemini'."
        )

    # OpenRouter configuration kept for historical experiments:
    # api_key = os.getenv("OPENROUTER_API_KEY")
    # model_name = os.getenv("OPENROUTER_MODEL", "deepseek/deepseek-chat-v3-0324:free")
    # max_tokens = int(os.getenv("OPENROUTER_MAX_TOKENS", "512"))

    if provider == "gemini":
        api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        model_name = os.getenv("GOOGLE_MODEL", "gemini-flash-latest")
        max_tokens = int(os.getenv("GOOGLE_MAX_TOKENS", "4096"))

        if not api_key:
            raise RuntimeError("GOOGLE_API_KEY not configured. Please define it in the .env file.")

        print(f"\n🔧 Inicializando modelo via Google Gemini: {model_name}")

        llm = LLM(
            model=f"gemini/{model_name}",
            api_key=api_key,
            temperature=0.0,
            max_tokens=max_tokens,
        )

        print(f"✓ Modelo {model_name} inicializado com sucesso via Google Gemini")
        return llm

    if provider == "deepseek":
        api_key = os.getenv("DEEPSEEK_API_KEY")
        model_name = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
        max_tokens = int(os.getenv("DEEPSEEK_MAX_TOKENS", "4096"))

        if not api_key:
            raise RuntimeError("DEEPSEEK_API_KEY not configured. Please define it in the .env file.")

        print(f"\n🔧 Inicializando modelo via DeepSeek: {model_name}")

        llm = LLM(
            model=f"deepseek/{model_name}",
            api_key=api_key,
            temperature=0.0,
            max_tokens=max_tokens,
        )

        print(f"✓ Modelo {model_name} inicializado com sucesso via DeepSeek")
        return llm

    # Anthropic Claude configuration (selected with DAVINCI_LLM_PROVIDER=anthropic):
    api_key = os.getenv("ANTHROPIC_API_KEY")
    model_name = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-5-20250929")
    max_tokens = int(os.getenv("CLAUDE_MAX_TOKENS", "4096"))

    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY not configured. Please define it in the .env file.")

    print(f"\n🔧 Inicializando modelo via Anthropic (Claude): {model_name}")

    llm = LLM(
        model=f"anthropic/{model_name}",
        api_key=api_key,
        temperature=0.0,
        max_tokens=max_tokens,
    )

    print(f"✓ Modelo {model_name} inicializado com sucesso via Anthropic (Claude)")
    return llm


EXAMPLE_GENERIC = """Catalog Service,Manage catalog entries;Update catalog item details;List available items,Order Service;Inventory Service
Order Service,Create orders from catalog items;View order history;Track order status,Catalog Service;Payment Service;Customer Service
Payment Service,Process order payments;Update payment status,Order Service
Customer Service,Register customer profiles;Update customer profiles;Retrieve customer profiles,Order Service;Auth Service
Auth Service,Authenticate user credentials;Issue access tokens,Customer Service"""


# Few-Shot exclusivo da Proposta B do C4 (Agente 2.1).
#
# O Agente 2.1 é um clone do prompt do Agente 1: mesmo papel CrewAI, mesmo
# objetivo, mesmo backstory e temperatura 0.0. Se os dois receberem o
# EXAMPLE_GENERIC, a Proposta B tende a reproduzir a Proposta A e o C4 degenera
# em um C0 com cinco chamadas de LLM por sistema (custo ~5x sem ganho). Este
# exemplo existe para introduzir diversidade entre as duas propostas
# independentes.
#
# Domínio escolhido deliberadamente fora dos oito sistemas avaliados (biblioteca,
# cia aérea, logística de carga, trading, mídia, pet shop, clínica veterinária e
# gestão de serviços) e fora do domínio do EXAMPLE_GENERIC (catálogo/pedido/
# pagamento/cliente/autenticação), de modo que a Proposta B não receba nenhuma
# referência de domínio que a favoreça em qualquer sistema do benchmark.
#
# O prompt das tasks classifica o Few-Shot como referência de formato, não como
# conhecimento de domínio; portanto os serviços abaixo não devem ser copiados
# para a arquitetura analisada.
EXAMPLE_ARCHITECT_B = """Device Registry Service,Register monitored devices;Maintain device metadata;Assign devices to monitored areas,Telemetry Ingestion Service;Firmware Update Service
Telemetry Ingestion Service,Collect sensor measurements;Persist measurement time series;Expose the latest measurement per device,Device Registry Service;Threshold Evaluation Service
Threshold Evaluation Service,Apply measurement thresholds;Raise deviation events,Telemetry Ingestion Service;Alert Notification Service
Alert Notification Service,Deliver deviation alerts;Maintain alert subscriptions,Threshold Evaluation Service;Device Registry Service
Firmware Update Service,Publish firmware versions;Report update results,Device Registry Service;Telemetry Ingestion Service"""


def criar_diretorio_run(system_name: str, timestamp: str) -> Path:
    run_dir = RESULTS_ROOT / system_name.lower() / "result_generalized_fewshot" / f"run_{timestamp}"
    run_dir.mkdir(parents=True, exist_ok=True)
    return run_dir


def salvar_csv(filepath: Path, cabecalho: list, linhas: list):
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(cabecalho)
        writer.writerows(linhas)


def salvar_proposta(run_dir: Path, sufixo: str, csv_texto: str):
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


def normalizar_output_llm(texto: str) -> str:
    """Converte saída em markdown (cercas, negrito, tabelas) para CSV puro."""
    # Remove cercas de código
    texto = re.sub(r"```(?:csv|CSV)?\s*\n?", "", texto)
    texto = texto.replace("```", "")
    # Remove negrito
    texto = texto.replace("**", "")
    # Converte tabelas markdown (| a | b | c |) em CSV
    linhas_saida = []
    for linha in texto.split("\n"):
        if "|" in linha:
            cols = [c.strip() for c in linha.strip().strip("|").split("|")]
            if len(cols) >= 3 and not all(set(c) <= {"-", ":", " "} for c in cols):
                linhas_saida.append(",".join(cols[:3]))
        else:
            linhas_saida.append(linha)
    return "\n".join(linhas_saida)


# Temporary diagnostic switch: prints the raw text returned by the LLM before
# the CSV extraction, so the console shows whether the model answered with
# markdown (fences, bold, tables) or with plain CSV. Set it to False to silence.
DEBUG_RAW_OUTPUT = True


def _debug_raw_output(label: str, texto: str) -> None:
    if not DEBUG_RAW_OUTPUT:
        return
    print(f"=== RAW OUTPUT [{label}] ===")
    print(str(texto)[:2000])
    print(f"=== FIM RAW [{label}] ===")


def extrair_csv_do_output(texto: str) -> str:
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


def normalize_service_name(name: str) -> str:
    name = name.lower().strip()
    name = name.replace(' ', '-').replace('_', '-')
    name = name.removesuffix('-service')
    name = name.removesuffix('-microservice')
    name = name.removesuffix('-ms')
    return name


def parse_csv_architecture(csv_text: str):
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


def _is_valid_architecture_csv(csv_text: str) -> bool:
    """Reject consolidated responses that contain prose or malformed rows."""
    rows = list(csv.reader(str(csv_text).strip().splitlines()))
    if not rows or [column.strip() for column in rows[0][:3]] != [
        "Microservice", "Responsibilities", "Communicates With"
    ]:
        return False
    data_rows = rows[1:]
    return bool(data_rows) and all(
        len(row) == 3 and row[0].strip() and not row[0].lstrip().startswith(("-", "Actually", "Note:"))
        for row in data_rows
    )


def parse_csv_interactions(csv_text: str) -> set:
    interactions = set()
    for line in csv_text.strip().split('\n'):
        line = line.strip()
        if not line or line.startswith('Microservice') or line.startswith('===') or line.startswith('-'):
            continue
        parts = [p.strip() for p in line.split(',')]
        if len(parts) >= 3:
            origem = normalize_service_name(parts[0])
            destinos_str = parts[2] if len(parts) == 3 else parts[2]
            destinos = [normalize_service_name(d.strip()) for d in destinos_str.split(';') if d.strip()]
            for destino in destinos:
                par = tuple(sorted([origem, destino]))
                interactions.add(par)
    return interactions


def tokenize_service_name(name: str) -> set:
    name = normalize_service_name(name)
    tokens = set(re.split(r'[-]', name))
    tokens = {t for t in tokens if t and t not in {"of", "and", "the", "for", "to"}}
    return tokens


def semantic_token_set(name: str) -> set:
    tokens = tokenize_service_name(name)
    return {SYNONYM_MAP.get(t, t) for t in tokens}




def are_services_equivalent(generated_name: str, reference_name: str) -> bool:
    """
    Verifica equivalência semântica justa.

    Considera equivalentes quando:
    - os nomes normalizados são idênticos;
    - ou os tokens principais, após sinônimos, são iguais;
    - ou um nome contém o token principal do outro.

    Não considera equivalentes apenas por interseção mínima.
    """

    gen_norm = normalize_service_name(generated_name)
    ref_norm = normalize_service_name(reference_name)

    if gen_norm == ref_norm:
        return True

    gen_tokens = semantic_token_set(generated_name)
    ref_tokens = semantic_token_set(reference_name)

    if not gen_tokens or not ref_tokens:
        return False

    # Se os conjuntos semânticos são iguais
    if gen_tokens == ref_tokens:
        return True

    # Se um contém todos os tokens principais do outro
    if gen_tokens.issubset(ref_tokens) or ref_tokens.issubset(gen_tokens):
        return True

    # Se compartilham o token principal de domínio
    # Ex.: catalog, media, authentication, cargo, trading
    main_tokens = {
        "authentication", "catalog", "media", "cargo", "trading",
        "portfolio", "account", "customer", "order", "payment",
        "delivery", "inventory", "tracking", "route", "event",
        "integration", "administration", "simulation", "market",
    }

    gen_main = gen_tokens.intersection(main_tokens)
    ref_main = ref_tokens.intersection(main_tokens)

    if gen_main and gen_main == ref_main:
        return True

    return False


def are_interactions_equivalent(pair_a, pair_b) -> bool:
    a1, a2 = pair_a
    b1, b2 = pair_b
    return (
        (are_services_equivalent(a1, b1) and are_services_equivalent(a2, b2)) or
        (are_services_equivalent(a1, b2) and are_services_equivalent(a2, b1))
    )


def evaluate_interactions(generated_set: set, reference_set: set):
    generated_list = list(generated_set)
    reference_list = list(reference_set)

    matched_generated_pairs = []
    matched_reference_pairs = []

    for gen_pair in generated_list:
        for ref_pair in reference_list:
            if ref_pair in matched_reference_pairs:
                continue
            if are_interactions_equivalent(gen_pair, ref_pair):
                matched_generated_pairs.append(gen_pair)
                matched_reference_pairs.append(ref_pair)
                break

    tp = len(matched_generated_pairs)
    fp = len(generated_list) - tp
    fn = len(reference_list) - tp

    precision = tp / len(generated_list) if generated_list else 0.0
    recall = tp / len(reference_list) if reference_list else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0

    return {
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1_score": round(f1, 4),
        "tp_count": tp,
        "fp_count": fp,
        "fn_count": fn,
        "tp": sorted([tuple(sorted(pair)) for pair in matched_generated_pairs]),
        "fp": sorted([tuple(sorted(pair)) for pair in generated_list if pair not in matched_generated_pairs]),
        "fn": sorted([tuple(sorted(pair)) for pair in reference_list if pair not in matched_reference_pairs]),
    }


def calculate_metrics(generated_services, reference_services):
    gen_norm = [normalize_service_name(s) for s in generated_services]
    ref_norm = [normalize_service_name(s) for s in reference_services]

    matched_generated = set()
    matched_reference = set()
    pairs = []

    for i, gen in enumerate(gen_norm):
        for j, ref in enumerate(ref_norm):
            if j in matched_reference:
                continue
            if are_services_equivalent(gen, ref):
                matched_generated.add(i)
                matched_reference.add(j)
                pairs.append((gen, ref))
                break

    tp = len(matched_generated)
    fp = len(gen_norm) - tp
    fn = len(ref_norm) - tp

    precision = tp / len(gen_norm) if gen_norm else 0.0
    recall = tp / len(ref_norm) if ref_norm else 0.0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0

    return {
        "true_positives": sorted(pairs),
        "false_positives": sorted(set(gen_norm) - set(matched_generated)),
        "false_negatives": sorted(set(ref_norm) - set(matched_reference)),
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1_score": round(f1, 4),
        "generated_count": len(gen_norm),
        "reference_count": len(ref_norm),
        "match_count": tp,
    }


def print_evaluation_report(metrics, title: str = "Evaluation Report"):
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

    if metrics['false_positives']:
        print(f"\n  ❌ False Positives (gerados mas não na referência):")
        for s in metrics['false_positives']:
            print(f"     - {s}")

    if metrics['false_negatives']:
        print(f"\n  ⚠ False Negatives (na referência mas não gerados):")
        for s in metrics['false_negatives']:
            print(f"     - {s}")

    if metrics['true_positives']:
        print(f"\n  ✅ True Positives (match semântico):")
        for s in metrics['true_positives']:
            print(f"     - {s}")


def silent_kickoff(crew: Crew, inputs: dict):
    buf_out = io.StringIO()
    buf_err = io.StringIO()
    with contextlib.redirect_stdout(buf_out), contextlib.redirect_stderr(buf_err):
        return crew.kickoff(inputs=inputs)


def _format_metrics_for_prompt(service_metrics, interaction_metrics):
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


@track_execution
def _executar_experimento(llm, system_name: str, config: dict, timestamp: str, example: str):
    system_name = config["name"]
    requirements = config["requirements"]
    reference_services = config["reference_services"]
    interaction_reference = config["interaction_reference"]

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

    # --- Agente 1 + Refinamento ---
    try:
        crew1 = Crew(agents=[agente1], tasks=[task1], verbose=True)
        output_a = silent_kickoff(crew1, {"example": example, "requirements": requirements})
        _debug_raw_output("agent_1/proposta_a", str(output_a))
        output_a_limpo = extrair_csv_do_output(normalizar_output_llm(str(output_a)))
        original_a = output_a_limpo

        try:
            crew4a = Crew(agents=[agente4], tasks=[task4], verbose=False)
            refined_a = silent_kickoff(crew4a, {
                "original_architecture": output_a_limpo,
                "requirements": requirements
            })
            _debug_raw_output("agent_4/refined_a", str(refined_a))
            output_a_limpo = extrair_csv_do_output(normalizar_output_llm(str(refined_a)))

            refined_services = set(parse_csv_architecture(output_a_limpo))
            original_services = set(parse_csv_architecture(original_a))

            if len(refined_services) < len(original_services):
                output_a_limpo = original_a
        except Exception:
            output_a_limpo = original_a

        resultados["proposta_a"] = output_a_limpo
        salvar_proposta(run_dir, "proposta_a", output_a_limpo)
    except Exception as e:
        print(f"✗ Erro no Agente 1: {type(e).__name__}: {e}")
        traceback.print_exc()
        resultados["proposta_a"] = None

    # --- Agente 2 + Refinamento ---
    try:
        crew2 = Crew(agents=[agente2], tasks=[task2], verbose=False)
        output_b = silent_kickoff(crew2, {"example": example, "requirements": requirements})
        _debug_raw_output("agent_2/proposta_b", str(output_b))
        output_b_limpo = extrair_csv_do_output(normalizar_output_llm(str(output_b)))
        original_b = output_b_limpo

        try:
            crew4b = Crew(agents=[agente4], tasks=[task4], verbose=False)
            refined_b = silent_kickoff(crew4b, {
                "original_architecture": output_b_limpo,
                "requirements": requirements
            })
            _debug_raw_output("agent_4/refined_b", str(refined_b))
            output_b_limpo = extrair_csv_do_output(normalizar_output_llm(str(refined_b)))

            refined_services = set(parse_csv_architecture(output_b_limpo))
            original_services = set(parse_csv_architecture(original_b))

            if len(refined_services) < len(original_services):
                output_b_limpo = original_b
        except Exception:
            output_b_limpo = original_b

        resultados["proposta_b"] = output_b_limpo
        salvar_proposta(run_dir, "proposta_b", output_b_limpo)
    except Exception as e:
        print(f"✗ Erro no Agente 2: {type(e).__name__}: {e}")
        traceback.print_exc()
        resultados["proposta_b"] = None

    # --- Métricas preliminares ---
    metricas_pre = {}
    for key in ["proposta_a", "proposta_b"]:
        if resultados.get(key):
            try:
                services = parse_csv_architecture(resultados[key])
                metricas_pre[key] = calculate_metrics(services, reference_services)
            except Exception:
                metricas_pre[key] = None
        else:
            metricas_pre[key] = None

    for key in ["proposta_a", "proposta_b"]:
        if resultados.get(key):
            try:
                gen_inter = parse_csv_interactions(resultados[key])
                metricas_pre[f"{key}_inter"] = evaluate_interactions(gen_inter, interaction_reference)
            except Exception:
                metricas_pre[f"{key}_inter"] = None
        else:
            metricas_pre[f"{key}_inter"] = None

    # --- Agente 3 ---
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
            _debug_raw_output("agent_3/consolidada", str(output_c))
            output_c_limpo = extrair_csv_do_output(normalizar_output_llm(str(output_c)))

            if _is_valid_architecture_csv(output_c_limpo):
                resultados["consolidada"] = output_c_limpo
            else:
                print("⚠️ Consolidação inválida. Usando Proposta A como fallback.")
                resultados["consolidada"] = resultados["proposta_a"]
            salvar_proposta(run_dir, "consolidada", resultados["consolidada"])
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
            metricas[key] = calculate_metrics(services, reference_services)
        else:
            metricas[key] = None

    for key in ["proposta_a", "proposta_b", "consolidada"]:
        if resultados.get(key):
            gen_inter = parse_csv_interactions(resultados[key])
            metricas[f"{key}_inter"] = evaluate_interactions(gen_inter, interaction_reference)
        else:
            metricas[f"{key}_inter"] = None

    especificacao_yaml = gerar_especificacao_yaml(system_name, resultados.get("consolidada", ""))
    (run_dir / "especificacao_arquitetural.yaml").write_text(especificacao_yaml, encoding="utf-8")
    resultados["especificacao_yaml"] = especificacao_yaml

    salvar_metricas(run_dir, metricas)
    salvar_sumario_json(run_dir, metricas)
    salvar_relatorio_md(run_dir, system_name, metricas)

    return resultados, metricas


def _registrar_fewshots_c4(run_dir: Path, example_a: str, example_b: str) -> None:
    """Grava a proveniência dos Few-Shots usados pelas propostas A e B do C4.

    O Agente 2.1 é um clone do prompt do Agente 1, então o único fator de
    diversidade entre as duas propostas independentes é o Few-Shot. Registrar
    tamanho e hash dos dois exemplos permite auditar depois qual material de
    referência gerou cada proposta, sem depender da versão do repositório.

    Best-effort: nunca interrompe a execução do pipeline.
    """
    try:
        registro = {
            "proposta_a_agente": "agent_1",
            "proposta_b_agente": "agent_2_1",
            "proposta_a_fewshot_chars": len(example_a),
            "proposta_b_fewshot_chars": len(example_b),
            "proposta_a_fewshot_sha256": hashlib.sha256(example_a.encode("utf-8")).hexdigest(),
            "proposta_b_fewshot_sha256": hashlib.sha256(example_b.encode("utf-8")).hexdigest(),
            "mesmo_fewshot": example_a.strip() == example_b.strip(),
        }
        (run_dir / "fewshot_c4.json").write_text(
            json.dumps(registro, indent=2, ensure_ascii=False), encoding="utf-8"
        )
    except Exception:
        pass


def kickoff_com_rotulo(crew: Crew, inputs: dict, rotulo: str):
    """Executa uma crew rotulando as chamadas de LLM com o nome do agente.

    O Agente 2.1 compartilha o papel CrewAI "Software Architect" com o Agente 1,
    então o rastreamento não consegue separá-los apenas pelo papel. O rótulo vale
    somente para este kickoff e é removido logo depois; as demais configurações
    continuam usando a atribuição por papel.
    """
    if set_agent_label is None or reset_agent_label is None:
        return silent_kickoff(crew, inputs)
    token = None
    try:
        token = set_agent_label(rotulo)
    except Exception:
        token = None
    try:
        return silent_kickoff(crew, inputs)
    finally:
        if token is not None:
            reset_agent_label(token)


@track_execution
def _executar_experimento_c4(llm, system_name: str, config: dict, timestamp: str, example: str,
                            example_b: str | None = None):
    """C4: C1 com o Agente 2.1 no lugar do Agente 2.

    Todas as etapas da C1 são mantidas. A única diferença é que a segunda
    proposta passa a ser construída pelo Agente 2.1, que desenvolve a sua própria
    arquitetura sem receber a saída do Agente 1.

    Como o Agente 2.1 é um clone do prompt do Agente 1, a diversidade entre as
    duas propostas depende do Few-Shot: a Proposta A usa `example` e a Proposta B
    usa `example_b`. Se `example_b` não for informado, vale o EXAMPLE_ARCHITECT_B
    (exemplo de outro domínio). Para reproduzir o comportamento em que as duas
    propostas recebem o mesmo Few-Shot, passe `example_b=example`.
    """
    if criar_agente2_1 is None or criar_task_arquitetura_2_1 is None:
        raise RuntimeError(
            "Agente 2.1 indisponível: verifique agentes/agent2_1architect_b_fs.py "
            "(funções criar_agente2_1 e criar_task_arquitetura)."
        )

    system_name = config["name"]
    requirements = config["requirements"]
    reference_services = config["reference_services"]
    interaction_reference = config["interaction_reference"]

    run_dir = criar_diretorio_run(system_name, timestamp)

    # Proposta A (Agente 1) e Proposta B (Agente 2.1) são propostas
    # independentes; o Few-Shot de cada uma é registrado no run_dir.
    example_b_efetivo = example_b if example_b else EXAMPLE_ARCHITECT_B
    _registrar_fewshots_c4(run_dir, example, example_b_efetivo)

    agente1 = criar_agente1(llm)
    agente2 = criar_agente2_1(llm)
    agente3 = criar_agente3(llm)
    agente4 = criar_agente4(llm)

    task1 = criar_task_arquitetura(agente1)
    task2 = criar_task_arquitetura_2_1(agente2)
    task3 = criar_task_consolidacao(agente3)
    task4 = criar_task_refinamento(agente4)

    resultados = {}

    # --- Agente 1 + Refinamento ---
    try:
        crew1 = Crew(agents=[agente1], tasks=[task1], verbose=True)
        output_a = silent_kickoff(crew1, {"example": example, "requirements": requirements})
        _debug_raw_output("c4/agent_1/proposta_a", str(output_a))
        output_a_limpo = extrair_csv_do_output(normalizar_output_llm(str(output_a)))
        original_a = output_a_limpo

        try:
            crew4a = Crew(agents=[agente4], tasks=[task4], verbose=False)
            refined_a = silent_kickoff(crew4a, {
                "original_architecture": output_a_limpo,
                "requirements": requirements
            })
            _debug_raw_output("c4/agent_4/refined_a", str(refined_a))
            output_a_limpo = extrair_csv_do_output(normalizar_output_llm(str(refined_a)))

            refined_services = set(parse_csv_architecture(output_a_limpo))
            original_services = set(parse_csv_architecture(original_a))

            if len(refined_services) < len(original_services):
                output_a_limpo = original_a
        except Exception:
            output_a_limpo = original_a

        resultados["proposta_a"] = output_a_limpo
        salvar_proposta(run_dir, "proposta_a", output_a_limpo)
    except Exception as e:
        print(f"✗ Erro no Agente 1: {type(e).__name__}: {e}")
        traceback.print_exc()
        resultados["proposta_a"] = None

    # --- Agente 2.1 + Refinamento ---
    try:
        crew2 = Crew(agents=[agente2], tasks=[task2], verbose=False)
        output_b = kickoff_com_rotulo(
            crew2,
            {"example": example_b_efetivo, "requirements": requirements},
            "agent_2_1",
        )
        _debug_raw_output("c4/agent_2_1/proposta_b", str(output_b))
        output_b_limpo = extrair_csv_do_output(normalizar_output_llm(str(output_b)))
        original_b = output_b_limpo

        try:
            crew4b = Crew(agents=[agente4], tasks=[task4], verbose=False)
            refined_b = silent_kickoff(crew4b, {
                "original_architecture": output_b_limpo,
                "requirements": requirements
            })
            _debug_raw_output("c4/agent_4/refined_b", str(refined_b))
            output_b_limpo = extrair_csv_do_output(normalizar_output_llm(str(refined_b)))

            refined_services = set(parse_csv_architecture(output_b_limpo))
            original_services = set(parse_csv_architecture(original_b))

            if len(refined_services) < len(original_services):
                output_b_limpo = original_b
        except Exception:
            output_b_limpo = original_b

        resultados["proposta_b"] = output_b_limpo
        salvar_proposta(run_dir, "proposta_b", output_b_limpo)
    except Exception as e:
        print(f"✗ Erro no Agente 2.1: {type(e).__name__}: {e}")
        traceback.print_exc()
        resultados["proposta_b"] = None

    # --- Métricas preliminares ---
    metricas_pre = {}
    for key in ["proposta_a", "proposta_b"]:
        if resultados.get(key):
            try:
                services = parse_csv_architecture(resultados[key])
                metricas_pre[key] = calculate_metrics(services, reference_services)
            except Exception:
                metricas_pre[key] = None
        else:
            metricas_pre[key] = None

    for key in ["proposta_a", "proposta_b"]:
        if resultados.get(key):
            try:
                gen_inter = parse_csv_interactions(resultados[key])
                metricas_pre[f"{key}_inter"] = evaluate_interactions(gen_inter, interaction_reference)
            except Exception:
                metricas_pre[f"{key}_inter"] = None
        else:
            metricas_pre[f"{key}_inter"] = None

    # --- Agente 3 ---
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
            _debug_raw_output("c4/agent_3/consolidada", str(output_c))
            output_c_limpo = extrair_csv_do_output(normalizar_output_llm(str(output_c)))

            if _is_valid_architecture_csv(output_c_limpo):
                resultados["consolidada"] = output_c_limpo
            else:
                print("⚠️ Consolidação inválida. Usando Proposta A como fallback.")
                resultados["consolidada"] = resultados["proposta_a"]
            salvar_proposta(run_dir, "consolidada", resultados["consolidada"])
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
            metricas[key] = calculate_metrics(services, reference_services)
        else:
            metricas[key] = None

    for key in ["proposta_a", "proposta_b", "consolidada"]:
        if resultados.get(key):
            gen_inter = parse_csv_interactions(resultados[key])
            metricas[f"{key}_inter"] = evaluate_interactions(gen_inter, interaction_reference)
        else:
            metricas[f"{key}_inter"] = None

    especificacao_yaml = gerar_especificacao_yaml(system_name, resultados.get("consolidada", ""))
    (run_dir / "especificacao_arquitetural.yaml").write_text(especificacao_yaml, encoding="utf-8")
    resultados["especificacao_yaml"] = especificacao_yaml

    salvar_metricas(run_dir, metricas)
    salvar_sumario_json(run_dir, metricas)
    salvar_relatorio_md(run_dir, system_name, metricas)

    return resultados, metricas


@track_execution
def _executar_experimento_c0(llm, system_name: str, config: dict, timestamp: str, example: str):
    """Execute the C0 baseline with only Agent 1 and deterministic YAML output."""
    system_name = config["name"]
    requirements = config["requirements"]
    reference_services = config["reference_services"]
    interaction_reference = config["interaction_reference"]
    run_dir = criar_diretorio_run(system_name, timestamp)

    agente1 = criar_agente1(llm)
    task1 = criar_task_arquitetura(agente1)
    resultados = {"proposta_a": None, "proposta_b": None, "consolidada": None}

    try:
        crew1 = Crew(agents=[agente1], tasks=[task1], verbose=True)
        output_a = silent_kickoff(crew1, {"example": example, "requirements": requirements})
        _debug_raw_output("c0/agent_1/proposta_a", str(output_a))
        output_a_limpo = extrair_csv_do_output(normalizar_output_llm(str(output_a)))
        resultados["proposta_a"] = output_a_limpo
        resultados["consolidada"] = output_a_limpo
        salvar_proposta(run_dir, "proposta_a", output_a_limpo)
        salvar_proposta(run_dir, "consolidada", output_a_limpo)
    except Exception as error:
        print(f"✗ Erro no Agente 1: {type(error).__name__}: {error}")
        traceback.print_exc()

    metricas = {
        "proposta_a": None,
        "proposta_a_inter": None,
    }
    if resultados["proposta_a"]:
        services = parse_csv_architecture(resultados["proposta_a"])
        metricas["proposta_a"] = calculate_metrics(services, reference_services)
        generated_interactions = parse_csv_interactions(resultados["proposta_a"])
        metricas["proposta_a_inter"] = evaluate_interactions(
            generated_interactions,
            interaction_reference,
        )

    especificacao_yaml = gerar_especificacao_yaml(system_name, resultados["proposta_a"] or "")
    (run_dir / "especificacao_arquitetural.yaml").write_text(especificacao_yaml, encoding="utf-8")
    resultados["especificacao_yaml"] = especificacao_yaml

    salvar_metricas(run_dir, metricas)
    salvar_sumario_json(run_dir, metricas)
    salvar_relatorio_md(run_dir, system_name, metricas)
    return resultados, metricas


@track_execution
def _executar_experimento_c2(llm, system_name: str, config: dict, timestamp: str, example: str):
    """Execute C2 with proposals A/B going directly to consolidation."""
    system_name = config["name"]
    requirements = config["requirements"]
    reference_services = config["reference_services"]
    interaction_reference = config["interaction_reference"]
    run_dir = criar_diretorio_run(system_name, timestamp)

    agente1 = criar_agente1(llm)
    agente2 = criar_agente2(llm)
    agente3 = criar_agente3(llm)

    task1 = criar_task_arquitetura(agente1)
    task2 = criar_task_arquitetura_alternativa(agente2)
    task3 = criar_task_consolidacao(agente3)
    resultados = {"proposta_a": None, "proposta_b": None, "consolidada": None}

    # C2 intentionally skips the Agent 4 refinement blocks used by C1.
    try:
        crew1 = Crew(agents=[agente1], tasks=[task1], verbose=True)
        output_a = silent_kickoff(crew1, {"example": example, "requirements": requirements})
        _debug_raw_output("c2/agent_1/proposta_a", str(output_a))
        resultados["proposta_a"] = extrair_csv_do_output(normalizar_output_llm(str(output_a)))
        salvar_proposta(run_dir, "proposta_a", resultados["proposta_a"])
    except Exception as error:
        print(f"✗ Erro no Agente 1: {type(error).__name__}: {error}")
        traceback.print_exc()

    try:
        crew2 = Crew(agents=[agente2], tasks=[task2], verbose=False)
        output_b = silent_kickoff(crew2, {"example": example, "requirements": requirements})
        _debug_raw_output("c2/agent_2/proposta_b", str(output_b))
        resultados["proposta_b"] = extrair_csv_do_output(normalizar_output_llm(str(output_b)))
        salvar_proposta(run_dir, "proposta_b", resultados["proposta_b"])
    except Exception as error:
        print(f"✗ Erro no Agente 2: {type(error).__name__}: {error}")
        traceback.print_exc()

    metricas_pre = {}
    for key in ("proposta_a", "proposta_b"):
        if resultados.get(key):
            try:
                services = parse_csv_architecture(resultados[key])
                metricas_pre[key] = calculate_metrics(services, reference_services)
            except Exception:
                metricas_pre[key] = None
            try:
                interactions = parse_csv_interactions(resultados[key])
                metricas_pre[f"{key}_inter"] = evaluate_interactions(
                    interactions, interaction_reference
                )
            except Exception:
                metricas_pre[f"{key}_inter"] = None
        else:
            metricas_pre[key] = None
            metricas_pre[f"{key}_inter"] = None

    if resultados["proposta_a"] and resultados["proposta_b"]:
        try:
            crew3 = Crew(agents=[agente3], tasks=[task3], verbose=False)
            output_c = silent_kickoff(crew3, {
                "architecture_a": resultados["proposta_a"],
                "architecture_b": resultados["proposta_b"],
                "metrics_a": _format_metrics_for_prompt(
                    metricas_pre.get("proposta_a"), metricas_pre.get("proposta_a_inter")
                ),
                "metrics_b": _format_metrics_for_prompt(
                    metricas_pre.get("proposta_b"), metricas_pre.get("proposta_b_inter")
                ),
                "requirements": requirements,
            })
            _debug_raw_output("c2/agent_3/consolidada", str(output_c))
            output_c_limpo = extrair_csv_do_output(normalizar_output_llm(str(output_c)))
            resultados["consolidada"] = (
                output_c_limpo
                if _is_valid_architecture_csv(output_c_limpo)
                else resultados["proposta_a"]
            )
        except Exception:
            resultados["consolidada"] = resultados["proposta_a"]
        salvar_proposta(run_dir, "consolidada", resultados["consolidada"])

    metricas = {}
    for key in ("proposta_a", "proposta_b", "consolidada"):
        if resultados.get(key):
            try:
                metricas[key] = calculate_metrics(
                    parse_csv_architecture(resultados[key]), reference_services
                )
                metricas[f"{key}_inter"] = evaluate_interactions(
                    parse_csv_interactions(resultados[key]), interaction_reference
                )
            except Exception:
                metricas[key] = None
                metricas[f"{key}_inter"] = None
        else:
            metricas[key] = None
            metricas[f"{key}_inter"] = None

    especificacao_yaml = gerar_especificacao_yaml(system_name, resultados.get("consolidada", ""))
    (run_dir / "especificacao_arquitetural.yaml").write_text(especificacao_yaml, encoding="utf-8")
    resultados["especificacao_yaml"] = especificacao_yaml
    salvar_metricas(run_dir, metricas)
    salvar_sumario_json(run_dir, metricas)
    salvar_relatorio_md(run_dir, system_name, metricas)
    return resultados, metricas


def executar_pipeline(system_name: str,
                      requirements: str,
                      reference_services: list,
                      interaction_reference: set,
                      example: str = EXAMPLE_GENERIC,
                      tracer_run_id: str | None = None) -> tuple:
    llm = criar_llm()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    config = {
        "name": system_name,
        "requirements": requirements,
        "reference_services": reference_services,
        "interaction_reference": interaction_reference,
        "tracer_run_id": tracer_run_id or timestamp,
    }
    resultados, metricas = _executar_experimento(llm, system_name, config, timestamp, example)
    return resultados, metricas


def executar_pipeline_c4(system_name: str,
                         requirements: str,
                         reference_services: list,
                         interaction_reference: set,
                         example: str = EXAMPLE_GENERIC,
                         example_b: str | None = None,
                         tracer_run_id: str | None = None) -> tuple:
    """Run C4: the full C1 pipeline with Agent 2.1 instead of Agent 2.

    `example` is the few-shot of the Agent 1 proposal and `example_b` the one of
    the independent Agent 2.1 proposal. When `example_b` is omitted, the
    configuration uses EXAMPLE_ARCHITECT_B (a different-domain example) so the
    two independent proposals do not collapse into the same architecture.
    """
    llm = criar_llm()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    config = {
        "name": system_name,
        "requirements": requirements,
        "reference_services": reference_services,
        "interaction_reference": interaction_reference,
        "tracer_run_id": tracer_run_id or timestamp,
    }
    return _executar_experimento_c4(llm, system_name, config, timestamp, example, example_b)


def executar_pipeline_c0(system_name: str,
                         requirements: str,
                         reference_services: list,
                         interaction_reference: set,
                         example: str = EXAMPLE_GENERIC,
                         tracer_run_id: str | None = None) -> tuple:
    """Run the C0 single-agent baseline without changing the full pipeline."""
    llm = criar_llm()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    config = {
        "name": system_name,
        "requirements": requirements,
        "reference_services": reference_services,
        "interaction_reference": interaction_reference,
        "tracer_run_id": tracer_run_id or timestamp,
    }
    return _executar_experimento_c0(llm, system_name, config, timestamp, example)


def executar_pipeline_c2(system_name: str,
                         requirements: str,
                         reference_services: list,
                         interaction_reference: set,
                         example: str = EXAMPLE_GENERIC,
                         tracer_run_id: str | None = None) -> tuple:
    """Run C2 without Agent 4 while preserving the full pipeline executor."""
    llm = criar_llm()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    config = {
        "name": system_name,
        "requirements": requirements,
        "reference_services": reference_services,
        "interaction_reference": interaction_reference,
        "tracer_run_id": tracer_run_id or timestamp,
    }
    return _executar_experimento_c2(llm, system_name, config, timestamp, example)


@track_execution
def _executar_experimento_c3(llm, system_name: str, config: dict, timestamp: str, example: str):
    """Execute C3 with Agent 1, refinement by Agent 4, and YAML export."""
    system_name = config["name"]
    requirements = config["requirements"]
    reference_services = config["reference_services"]
    interaction_reference = config["interaction_reference"]
    run_dir = criar_diretorio_run(system_name, timestamp)

    agente1 = criar_agente1(llm)
    agente4 = criar_agente4(llm)
    task1 = criar_task_arquitetura(agente1)
    task4 = criar_task_refinamento(agente4)
    resultados = {"proposta_a": None, "proposta_b": None, "consolidada": None}

    # C3 intentionally does not instantiate or call Agents 2 and 3.
    try:
        crew1 = Crew(agents=[agente1], tasks=[task1], verbose=True)
        output_a = silent_kickoff(crew1, {"example": example, "requirements": requirements})
        _debug_raw_output("c3/agent_1/proposta_a", str(output_a))
        original_a = extrair_csv_do_output(normalizar_output_llm(str(output_a)))
        proposta_a_refinada = original_a

        # C3 has no independent proposal B or consolidation step.
        try:
            crew4 = Crew(agents=[agente4], tasks=[task4], verbose=False)
            _raw_refined_a = silent_kickoff(crew4, {
                "original_architecture": original_a,
                "requirements": requirements,
            })
            _debug_raw_output("c3/agent_4/refined_a", str(_raw_refined_a))
            refined_a = extrair_csv_do_output(normalizar_output_llm(str(_raw_refined_a)))
            refined_services = parse_csv_architecture(refined_a)
            original_services = parse_csv_architecture(original_a)
            if refined_a.strip() and refined_services and len(refined_services) >= len(original_services):
                proposta_a_refinada = refined_a
        except Exception:
            proposta_a_refinada = original_a

        resultados["proposta_a"] = proposta_a_refinada
        resultados["consolidada"] = proposta_a_refinada
        salvar_proposta(run_dir, "proposta_a", proposta_a_refinada)
        salvar_proposta(run_dir, "consolidada", proposta_a_refinada)
    except Exception as error:
        print(f"✗ Erro no Agente 1: {type(error).__name__}: {error}")
        traceback.print_exc()

    metricas = {"proposta_a": None, "proposta_a_inter": None}
    if resultados["proposta_a"]:
        try:
            metricas["proposta_a"] = calculate_metrics(
                parse_csv_architecture(resultados["proposta_a"]), reference_services
            )
            metricas["proposta_a_inter"] = evaluate_interactions(
                parse_csv_interactions(resultados["proposta_a"]), interaction_reference
            )
        except Exception:
            pass

    especificacao_yaml = gerar_especificacao_yaml(system_name, resultados["proposta_a"] or "")
    (run_dir / "especificacao_arquitetural.yaml").write_text(especificacao_yaml, encoding="utf-8")
    resultados["especificacao_yaml"] = especificacao_yaml
    salvar_metricas(run_dir, metricas)
    salvar_sumario_json(run_dir, metricas)
    salvar_relatorio_md(run_dir, system_name, metricas)
    return resultados, metricas


def executar_pipeline_c3(system_name: str,
                         requirements: str,
                         reference_services: list,
                         interaction_reference: set,
                         example: str = EXAMPLE_GENERIC,
                         tracer_run_id: str | None = None) -> tuple:
    """Run C3 with only Agent 1, Agent 4, and Agent 5."""
    llm = criar_llm()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    config = {
        "name": system_name,
        "requirements": requirements,
        "reference_services": reference_services,
        "interaction_reference": interaction_reference,
        "tracer_run_id": tracer_run_id or timestamp,
    }
    return _executar_experimento_c3(llm, system_name, config, timestamp, example)