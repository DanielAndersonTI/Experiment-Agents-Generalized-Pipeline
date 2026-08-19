"""
Script Principal de Orquestração Multiagente – FEW-SHOT (Generalizado)

Executa os 4 agentes em sequência para gerar e consolidar arquiteturas
e salva todos os resultados em:
    result/<sistema>/result_generalized_fewshot/run_<timestamp>/

Uso:
    python main_fewshot.py --system petclinic
    python main_fewshot.py --system bookstore
    python main_fewshot.py --system mediastore
    python main_fewshot.py --system teastore
    python main_fewshot.py --all

A lógica do pipeline é genérica. Os dados específicos de cada sistema
(requisitos, ground truth, mapa de normalização) são declarados no dicionário
SYSTEMS, sem estruturas condicionais por sistema no fluxo principal.
"""

import os
import re
import sys
import argparse
import csv
import json
import contextlib
import io
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

from crewai import LLM, Crew

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
        print("✗ ERRO: GOOGLE_API_KEY não configurada!")
        print("  Defina GOOGLE_API_KEY no arquivo .env.")
        sys.exit(1)

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
# Requisitos dos Sistemas (dados de entrada)
# ============================================

PETCLINIC_REQUIREMENTS = """
Spring PetClinic Microservices - Requirements

1. Manage Clients:
   - Add, update, and delete client information.
   - View detailed information about existing clients.

2. Manage Pets:
   - Add, update, and delete pet information.
   - Link pets to their respective owners.

3. Manage Visits:
   - Register new visits for pets.
   - View visit history for a specific pet.

4. Manage Veterinarians:
   - Add, update, and delete vet information.
   - View specialties for each veterinarian.

5. Service Discovery:
   - Register and locate services using Eureka.

6. Centralized Configuration:
   - Manage service configurations through a Config Server.

7. API Gateway:
   - Route client requests to appropriate backend services.

8. Monitoring and Administration:
   - Monitor services and applications using Admin Server.
"""

BOOKSTORE_REQUIREMENTS = """
Bookstore Microservices - Requirements

1. Manage Products:
   - Add, update, and delete product entries.
   - List available products for purchase.

2. Manage Shopping Cart:
   - Add and remove products from the shopping cart.
   - View items currently in the cart.

3. Manage Orders:
   - Create orders from shopping cart items.
   - View order history and order details.

4. Manage Payments:
   - Process payments for completed orders.

5. Manage Deliveries:
   - Schedule and track delivery of orders.

6. Manage Customers:
   - Register and authenticate customer accounts.
   - Update and retrieve customer profile information.

7. Manage Authentication:
   - Provide secure authentication and authorization for users.
   - Integrate with other services to validate credentials and permissions.
"""


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
# Mapeamentos de Nomes (por sistema)
# ============================================

PETCLINIC_NAME_MAP = {
    "apigateway": "api-gateway",
    "api-gateway": "api-gateway",
    "gateway": "api-gateway",
    "gateway-service": "api-gateway",
    "configserver": "config-server",
    "config-server": "config-server",
    "configservice": "config-server",
    "configuration-service": "config-server",
    "eurekaserver": "discovery-server",
    "discoveryserver": "discovery-server",
    "discovery-service": "discovery-server",
    "discovery": "discovery-server",
    "eureka": "discovery-server",
    "adminserver": "admin-server",
    "admin-server": "admin-server",
    "adminservice": "admin-server",
    "admin": "admin-server",
    "ownerservice": "customers-service",
    "owner-service": "customers-service",
    "clientservice": "customers-service",
    "client-service": "customers-service",
    "customer-service": "customers-service",
    "customers-service": "customers-service",
    "customer": "customers-service",
    "petservice": "pets-service",
    "pet-service": "pets-service",
    "pet": "pets-service",
    "veterinarianservice": "vets-service",
    "vetservice": "vets-service",
    "vet-service": "vets-service",
    "veterinarian": "vets-service",
    "vet": "vets-service",
    "visitservice": "visits-service",
    "visit-service": "visits-service",
    "visit": "visits-service",
    "customers": "customers-service",
    "vets": "vets-service",
    "visits": "visits-service",
    "clientcommandservice": "customers-service",
    "clientqueryservice": "customers-service",
    "petcommandservice": "pets-service",
    "petqueryservice": "pets-service",
    "visitcommandservice": "visits-service",
    "visitqueryservice": "visits-service",
    "vetcommandservice": "vets-service",
    "vetqueryservice": "vets-service",
    "eventbus": "discovery-server",
    "discoveryservice": "discovery-server",
    "ownerprofileservice": "customers-service",
    "ownerdashboardservice": "customers-service",
    "petcatalogservice": "pets-service",
    "visitschedulingservice": "visits-service",
    "vetmanagementservice": "vets-service",
    "pethistoryservice": "visits-service",
    "servicediscovery": "discovery-server",
    "eureka-server": "discovery-server",
    "discovery-service-(eureka)": "discovery-server",
    "owner": "customers-service",
    "owner-service": "customers-service",
    "pet-service": "pets-service",
    "visit-service": "visits-service",
    "vet-service": "vets-service",
    "config-server": "config-server",
    "admin-server": "admin-server",
    "api-gateway": "api-gateway",
    "service-discovery": "discovery-server",
    "eventbroker": "discovery-server",
    "messagebroker": "discovery-server",
    "apigatewayservice": "api-gateway",
    "eurekaservice": "discovery-server",
    "gatewayservice": "api-gateway",
    "client": "customers-service",
    "config": "config-server",
    "client-onboarding": "customers-service",
    "client-onboarding-service": "customers-service",
    "client-profile": "customers-service",
    "client-profile-service": "customers-service",
    "pet-management": "pets-service",
    "pet-management-service": "pets-service",
    "pet-registry": "pets-service",
    "pet-registry-service": "pets-service",
    "visit-scheduling": "visits-service",
    "visit-scheduling-service": "visits-service",
    "clinic-operations": "visits-service",
    "clinic-operations-service": "visits-service",
    "vet-roster": "vets-service",
    "vet-roster-service": "vets-service",
    "veterinary-roster": "vets-service",
    "veterinary-roster-service": "vets-service",
    "admin-monitoring": "admin-server",
    "admin-monitoring-service": "admin-server",
}

BOOKSTORE_NAME_MAP = {
    "authservice": "auth-service",
    "auth": "auth-service",
    "cartservice": "cart-service",
    "cart": "cart-service",
    "shoppingcartservice": "cart-service",
    "shopping-cart-service": "cart-service",
    "shopping-cart": "cart-service",
    "customerservice": "customer-service",
    "customer": "customer-service",
    "deliveryservice": "delivery-service",
    "delivery": "delivery-service",
    "deliverymanagementservice": "delivery-service",
    "delivery-management": "delivery-service",
    "orderservice": "order-service",
    "order": "order-service",
    "orderplacementservice": "order-service",
    "order-placement": "order-service",
    "orderqueryservice": "order-service",
    "order-query": "order-service",
    "orderfulfillmentservice": "order-service",
    "order-fulfillment": "order-service",
    "paymentservice": "payment-service",
    "payment": "payment-service",
    "paymentprocessingservice": "payment-service",
    "payment-processing": "payment-service",
    "productservice": "product-service",
    "product": "product-service",
    "productcatalogservice": "product-service",
    "product-catalog": "product-service",
    "bookservice": "product-service",
    "book": "product-service",
    "apigateway": "api-gateway",
    "api-gateway": "api-gateway",
    "gateway": "api-gateway",
    "configserver": "config-server",
    "config-service": "config-server",
    "config": "config-server",
    "discoveryserver": "discovery-server",
    "service-discovery": "discovery-server",
    "service-discovery-(eureka)": "discovery-server",
    "discovery": "discovery-server",
    "adminserver": "admin-server",
    "admin-service": "admin-server",
    "admin": "admin-server",
    "eventbroker": "discovery-server",
    "event-broker": "discovery-server",
    "authenticationservice": "auth-service",
    "authentication": "auth-service",
    "identity": "auth-service",
    "identity-service": "auth-service",
    "identity-&-auth": "auth-service",
    "identity-&-auth-service": "auth-service",
    "customer-profile": "customer-service",
    "customer-profile-service": "customer-service",
    "product-command": "product-service",
    "product-command-service": "product-service",
    "catalog-read": "product-service",
    "catalog-read-projection": "product-service",
    "inventory-write": "product-service",
    "inventory-write-service": "product-service",
    "ephemeral-cart": "cart-service",
    "ephemeral-cart-service": "cart-service",
    "cart-&-checkout": "cart-service",
    "cart-&-checkout-service": "cart-service",
    "order-orchestrator": "order-service",
    "order-orchestrator-service": "order-service",
    "order-saga-orchestrator": "order-service",
    "payment-processor": "payment-service",
    "payment-processor-service": "payment-service",
    "payment-gateway-integration": "payment-service",
    "payment-gateway-integration-service": "payment-service",
    "fulfillment": "delivery-service",
    "fulfillment-service": "delivery-service",
    "logistics-&-delivery": "delivery-service",
    "logistics-&-delivery-service": "delivery-service",
}


# ============================================
# Referências de Serviços
# ============================================

PETCLINIC_REFERENCE = [
    "api-gateway",
    "config-server",
    "discovery-server",
    "admin-server",
    "customers-service",
    "vets-service",
    "visits-service",
]

BOOKSTORE_REFERENCE = [
    "auth-service",
    "cart-service",
    "customer-service",
    "delivery-service",
    "order-service",
    "payment-service",
    "product-service",
]


# ============================================
# Referências de Interações
# ============================================

PETCLINIC_INTERACTIONS_REFERENCE = {
    ("admin-server", "api-gateway"),
    ("admin-server", "config-server"),
    ("admin-server", "customers-service"),
    ("admin-server", "discovery-server"),
    ("admin-server", "vets-service"),
    ("admin-server", "visits-service"),
    ("api-gateway", "config-server"),
    ("api-gateway", "customers-service"),
    ("api-gateway", "discovery-server"),
    ("api-gateway", "vets-service"),
    ("api-gateway", "visits-service"),
    ("config-server", "customers-service"),
    ("config-server", "discovery-server"),
    ("config-server", "vets-service"),
    ("config-server", "visits-service"),
    ("customers-service", "discovery-server"),
    ("customers-service", "visits-service"),
    ("discovery-server", "vets-service"),
    ("discovery-server", "visits-service"),
}

BOOKSTORE_INTERACTIONS_REFERENCE = {
    ("auth-service", "customer-service"),
    ("cart-service", "customer-service"),
    ("cart-service", "order-service"),
    ("cart-service", "product-service"),
    ("customer-service", "order-service"),
    ("delivery-service", "order-service"),
    ("order-service", "payment-service"),
    ("order-service", "product-service"),
}


# ============================================
# Configuração Central dos Sistemas
# ============================================

SYSTEMS = {
    "petclinic": {
        "name": "PetClinic",
        "requirements": PETCLINIC_REQUIREMENTS,
        "reference_services": PETCLINIC_REFERENCE,
        "interaction_reference": PETCLINIC_INTERACTIONS_REFERENCE,
        "name_map": PETCLINIC_NAME_MAP,
    },
    "bookstore": {
        "name": "Bookstore",
        "requirements": BOOKSTORE_REQUIREMENTS,
        "reference_services": BOOKSTORE_REFERENCE,
        "interaction_reference": BOOKSTORE_INTERACTIONS_REFERENCE,
        "name_map": BOOKSTORE_NAME_MAP,
    },
    "mediastore": {
        "name": "MediaStore",
        "requirements": "",
        "reference_services": [],
        "interaction_reference": set(),
        "name_map": {},
    },
    "teastore": {
        "name": "TeaStore",
        "requirements": "",
        "reference_services": [],
        "interaction_reference": set(),
        "name_map": {},
    },
}


# ============================================
# Função auxiliar para silenciar o CrewAI
# ============================================

def silent_kickoff(crew: Crew, inputs: dict):
    """Executa crew.kickoff silenciando stdout/stderr do CrewAI."""
    buf_out = io.StringIO()
    buf_err = io.StringIO()
    with contextlib.redirect_stdout(buf_out), contextlib.redirect_stderr(buf_err):
        return crew.kickoff(inputs=inputs)


# ============================================
# Execução do Experimento
# ============================================

def executar_experimento(llm, system_key: str, config: dict, timestamp: str, example: str):
    """
    Executa o experimento completo para um sistema.
    Retorna (resultados, metricas) com o terminal silencioso.
    """

    system_name = config["name"]
    requirements = config["requirements"]
    reference_services = config["reference_services"]
    interaction_reference = config["interaction_reference"]
    name_map = config["name_map"]

    run_dir = criar_diretorio_run(system_key, timestamp)

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

    # --- Executar Agente 3 (Validador) ---
    if resultados["proposta_a"] and resultados["proposta_b"]:
        try:
            crew3 = Crew(agents=[agente3], tasks=[task3], verbose=False)
            output_c = silent_kickoff(crew3, {
                "architecture_a": resultados["proposta_a"],
                "architecture_b": resultados["proposta_b"],
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

    # --- Avaliação ---
    metricas = {}
    for key in ["proposta_a", "proposta_b", "consolidada"]:
        if resultados.get(key):
            services = parse_csv_architecture(resultados[key])
            metrics = calculate_metrics(services, reference_services, name_map)
            metricas[key] = metrics
        else:
            metricas[key] = None

    for key in ["proposta_a", "proposta_b", "consolidada"]:
        if resultados.get(key):
            gen_inter = parse_csv_interactions(resultados[key], name_map)
            inter_metrics = evaluate_interactions(gen_inter, interaction_reference)
            metricas[f"{key}_inter"] = inter_metrics
        else:
            metricas[f"{key}_inter"] = None

    salvar_metricas(run_dir, metricas)
    salvar_sumario_json(run_dir, metricas)
    salvar_relatorio_md(run_dir, system_name, metricas)

    return resultados, metricas


# ============================================
# Impressão Final Consolidada
# ============================================

def _fmt(value):
    return "—" if value is None else f"{value:.4f}"


def _best_proposals(m_a, m_b, m_c):
    """Retorna lista de tuplas (rótulo, métrica) com maior F1, incluindo empates."""
    candidates = [("A", m_a), ("B", m_b), ("Consolidada", m_c)]
    valid = [(label, m) for label, m in candidates if m is not None]
    if not valid:
        return []
    max_f1 = max(m["f1_score"] for _, m in valid)
    return [(label, m) for label, m in valid if m["f1_score"] == max_f1]


def _format_best(best_list):
    if not best_list:
        return "—"
    return ", ".join(f"{label} (F1 {m['f1_score']:.4f})" for label, m in best_list)


def imprimir_resultados_finais(resultados_sistemas):
    """
    Exibe os resultados finais de forma consolidada e legível.

    Apresenta:
    1. Resumo final de Serviços (RQ1)
    2. Resumo final de Interações (RQ2)
    3. Melhores resultados por sistema
    """

    # =========================================================
    # RESUMO FINAL — SERVIÇOS (RQ1)
    # =========================================================
    print("\n" + "=" * 100)
    print("RESUMO FINAL — SERVIÇOS (RQ1)")
    print("=" * 100)

    print(
        f"{'Sistema':<15}"
        f"{'Proposta':<15}"
        f"{'Precision':<13}"
        f"{'Recall':<13}"
        f"{'F1-Score':<13}"
    )
    print("-" * 100)

    for system_key, metricas in resultados_sistemas.items():
        if not metricas:
            continue

        propostas = [
            ("A", metricas.get("proposta_a")),
            ("B", metricas.get("proposta_b")),
            ("Consolidada", metricas.get("consolidada")),
        ]

        for proposta, m in propostas:
            if m:
                print(
                    f"{SYSTEMS[system_key]['name']:<15}"
                    f"{proposta:<15}"
                    f"{m['precision']:<13.4f}"
                    f"{m['recall']:<13.4f}"
                    f"{m['f1_score']:<13.4f}"
                )
            else:
                print(
                    f"{SYSTEMS[system_key]['name']:<15}"
                    f"{proposta:<15}"
                    f"{'—':<13}"
                    f"{'—':<13}"
                    f"{'—':<13}"
                )

    # =========================================================
    # RESUMO FINAL — INTERAÇÕES (RQ2)
    # =========================================================
    print("\n" + "=" * 100)
    print("RESUMO FINAL — INTERAÇÕES (RQ2)")
    print("=" * 100)

    print(
        f"{'Sistema':<15}"
        f"{'Proposta':<15}"
        f"{'Precision':<13}"
        f"{'Recall':<13}"
        f"{'F1-Score':<13}"
    )
    print("-" * 100)

    for system_key, metricas in resultados_sistemas.items():
        if not metricas:
            continue

        propostas_inter = [
            ("A", metricas.get("proposta_a_inter")),
            ("B", metricas.get("proposta_b_inter")),
            ("Consolidada", metricas.get("consolidada_inter")),
        ]

        for proposta, m in propostas_inter:
            if m:
                print(
                    f"{SYSTEMS[system_key]['name']:<15}"
                    f"{proposta:<15}"
                    f"{m['precision']:<13.4f}"
                    f"{m['recall']:<13.4f}"
                    f"{m['f1_score']:<13.4f}"
                )
            else:
                print(
                    f"{SYSTEMS[system_key]['name']:<15}"
                    f"{proposta:<15}"
                    f"{'—':<13}"
                    f"{'—':<13}"
                    f"{'—':<13}"
                )

    # =========================================================
    # MELHORES RESULTADOS POR SISTEMA
    # =========================================================
    print("\n" + "=" * 100)
    print("MELHORES RESULTADOS POR SISTEMA")
    print("=" * 100)

    print(
        f"{'Sistema':<15}"
        f"{'Melhor Serviços':<35}"
        f"{'Melhor Interações':<35}"
    )
    print("-" * 100)

    for system_key, metricas in resultados_sistemas.items():
        if not metricas:
            continue

        best_serv = _best_proposals(
            metricas.get("proposta_a"),
            metricas.get("proposta_b"),
            metricas.get("consolidada"),
        )
        best_inter = _best_proposals(
            metricas.get("proposta_a_inter"),
            metricas.get("proposta_b_inter"),
            metricas.get("consolidada_inter"),
        )

        print(
            f"{SYSTEMS[system_key]['name']:<15}"
            f"{_format_best(best_serv):<35}"
            f"{_format_best(best_inter):<35}"
        )


# ============================================
# Main
# ============================================

def main():
    parser = argparse.ArgumentParser(
        description="Experimento Multiagente Few-Shot Generalizado"
    )
    parser.add_argument(
        "--system", "-s",
        choices=list(SYSTEMS.keys()),
        default="petclinic",
        help="Sistema para executar o experimento"
    )
    parser.add_argument(
        "--all", "-a",
        action="store_true",
        help="Executar experimento com todos os sistemas cadastrados"
    )
    args = parser.parse_args()

    print("=" * 60)
    print("MULTIAGENT ARCHITECTURE GENERATION (FEW-SHOT GENERALIZADO)")
    print("=" * 60)

    llm = criar_llm()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    if args.all:
        sistemas_para_executar = list(SYSTEMS.keys())
    else:
        sistemas_para_executar = [args.system]

    resultados_sistemas = {}

    for system_key in sistemas_para_executar:
        config = SYSTEMS[system_key]

        if not config["requirements"] or not config["reference_services"]:
            print(f"\n⚠ {config['name']}: não configurado. Ignorando.")
            continue

        print(f"\n▶ Executando {config['name']}...")
        try:
            _, metricas = executar_experimento(
                llm,
                system_key,
                config,
                timestamp,
                EXAMPLE_GENERIC,
            )
            resultados_sistemas[system_key] = metricas
            print(f"  ✓ {config['name']} concluído")
        except Exception as e:
            print(f"  ✗ {config['name']} falhou: {e}")

    imprimir_resultados_finais(resultados_sistemas)

    print("\n" + "=" * 60)
    print("✅ EXPERIMENTO CONCLUÍDO")
    print("=" * 60)


if __name__ == "__main__":
    main()