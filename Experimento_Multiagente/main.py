"""
Script Principal de Orquestração Multiagente
Executa os 3 agentes em sequência para gerar e consolidar arquiteturas
e salva todos os resultados na pasta result/<sistema>/run_<timestamp>/.

Uso:
    python main.py                     # Executa com PetClinic (padrão)
    python main.py --system bookstore  # Executa com Bookstore
    python main.py --all               # Executa com ambos os sistemas

Baseado no notebook: multiagent_architecture_generation.ipynb
"""

import os
import sys
import argparse
import csv
import json
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

from crewai import LLM, Crew

# Importar agentes
from agentes.agent1_architect_a import criar_agente1, criar_task_arquitetura
from agentes.agent2_architect_b import criar_agente2, criar_task_arquitetura_alternativa
from agentes.agent3_validator import criar_agente3, criar_task_consolidacao


# ============================================
# Configuração
# ============================================

RESULTS_ROOT = Path("result")


def carregar_config():
    """Carrega variáveis de ambiente do arquivo .env"""
    env_path = Path(__file__).parent / '.env'
    if env_path.exists():
        load_dotenv(env_path)
        print(f"✓ .env carregado de: {env_path}")
    else:
        load_dotenv()
        print("⚠ .env não encontrado, usando variáveis do sistema")

    api_key = os.getenv("OPENROUTER_API_KEY")
    model_name = os.getenv("OPENROUTER_MODEL", "deepseek/deepseek-chat-v3-0324:free")

    if not api_key:
        print("✗ ERRO: OPENROUTER_API_KEY não configurada!")
        print("  Copie .env.example para .env e adicione sua chave do OpenRouter.")
        sys.exit(1)

    return api_key, model_name


def criar_llm(api_key: str, model_name: str) -> LLM:
    """Cria o modelo LLM usando CrewAI com OpenRouter"""
    print(f"\n🔧 Inicializando modelo via OpenRouter: {model_name}")
    llm = LLM(
        model=f"openrouter/{model_name}",
        api_key=api_key,
        temperature=0.3,
    )
    print(f"✓ Modelo {model_name} inicializado com sucesso via OpenRouter")
    return llm


# ============================================
# Requisitos dos Sistemas
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
# Funções de Salvamento
# ============================================

def criar_diretorio_run(system_name: str, timestamp: str) -> Path:
    """Cria o diretório result/<sistema>/run_<timestamp>/ e retorna seu caminho."""
    run_dir = RESULTS_ROOT / system_name.lower() / f"run_{timestamp}"
    run_dir.mkdir(parents=True, exist_ok=True)
    return run_dir


def salvar_csv(filepath: Path, cabecalho: list, linhas: list):
    """Salva dados em formato CSV no caminho especificado."""
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(cabecalho)
        writer.writerows(linhas)
    print(f"  💾 Salvo: {filepath}")


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
    # Serviços
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

    # Interações
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
    print(f"  💾 Salvo: {filepath}")

def salvar_relatorio_md(run_dir: Path, system_name: str, metricas: dict):
    """Gera um relatório Markdown com as métricas e salva no diretório da execução."""
    linhas = [
        f"# Relatório de Execução – {system_name}",
        "",
        f"**Data/hora:** {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}",
        "",
        "## Métricas de Serviços",
        "",
        "| Proposta | Precision | Recall | F1‑Score | Match (TP) | Serviços Gerados |",
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
        "| Proposta | Precision | Recall | F1‑Score | TP | Total Gerado |",
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
    print(f"  💾 Relatório salvo: {filepath}")


# ============================================
# Funções de Avaliação
# ============================================

def parse_csv_architecture(csv_text: str):
    """Parse CSV output from agent into list of service names.
    Handles both 3-column and 4-column formats (Consolidated has a 'Source' column).
    Ignores headers, section markers and decision lines."""
    services = []
    try:
        lines = str(csv_text).strip().split('\n')
        for line in lines:
            line = line.strip()
            # Skip empty lines, headers, section markers and decision/comment lines
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
            # Accept lines with 3 or 4 fields (last field may be Source like "A+B")
            if len(parts) >= 3:
                service_name = parts[0].lower().replace(' ', '-')
                if service_name:
                    services.append(service_name)
    except Exception as e:
        print(f"  ⚠ Erro ao parsear CSV: {e}")
    return services

# ============================================
# Referências de Interações (exemplo para PetClinic)
# Baseado nos arquivos .dot do artigo original
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
    ("payment-service", "order-service"),
}


def parse_csv_interactions(csv_text: str, system: str = "petclinic") -> set:
    """Extrai pares (origem, destino) normalizados do CSV de arquitetura."""
    interactions = set()
    for line in csv_text.strip().split('\n'):
        line = line.strip()
        if not line or line.startswith('Microservice') or line.startswith('===') or line.startswith('-'):
            continue
        parts = [p.strip() for p in line.split(',')]
        if len(parts) >= 3:
            origem = normalize_service_name(parts[0], system)
            destinos_str = parts[2] if len(parts) == 3 else parts[2]  # lidar com coluna Source na consolidada
            destinos = [normalize_service_name(d.strip(), system) for d in destinos_str.split(';') if d.strip()]
            for destino in destinos:
                # Par canônico: ordem alfabética para evitar duplicatas bidirecionais
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

# ============================================
# Mapeamento de nomes equivalentes (sinônimos)
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
    "eventbus": "discovery-server",   # ou remover se não quiser forçar
    "discoveryservice": "discovery-server",
    "ownerprofileservice": "customers-service",
    "ownerdashboardservice": "customers-service",
    "petcatalogservice": "pets-service",
    "visitschedulingservice": "visits-service",
    "vetmanagementservice": "vets-service",
    "pethistoryservice": "visits-service",
    "servicediscovery": "discovery-server",
        # Termos com espaços convertidos para hífen
    "eureka-server": "discovery-server",
    "owner": "customers-service",
    "owner-service": "customers-service",
    "pet-service": "pets-service",
    "visit-service": "visits-service",
    "vet-service": "vets-service",
    # Infraestrutura alternativa
    "config-server": "config-server",      # já deve existir, confirme
    "admin-server": "admin-server",        # idem
    "api-gateway": "api-gateway",          # idem
    "service-discovery": "discovery-server",
    # Agente B / alternativos
    "eventbroker": "discovery-server",     # ou remova se preferir tratá-lo como extra legítimo
    "messagebroker": "discovery-server",
    "apigatewayservice": "api-gateway",
    "eurekaservice": "discovery-server",
    "gatewayservice": "api-gateway",
    "client": "customers-service",
    "config": "config-server",
       
}

BOOKSTORE_NAME_MAP = {
    # Variações de domínio
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
    # Infraestrutura (não existe na referência, mas normaliza para evitar variações)
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
}


def normalize_service_name(name: str, system: str = "petclinic") -> str:
    """
    Normaliza o nome do serviço para comparação, usando mapeamento de sinônimos.
    
    Args:
        name: Nome original do serviço gerado.
        system: "petclinic" ou "bookstore" para escolher o mapa correto.
    
    Returns:
        Nome normalizado (deve corresponder a um nome da lista de referência).
    """
    name = name.lower().strip()
    name = name.replace(' ', '-').replace('_', '-')
    name = name.removesuffix('-service')
    name = name.removesuffix('-microservice')
    name = name.removesuffix('-ms')
    
    if system == "petclinic":
        name = PETCLINIC_NAME_MAP.get(name, name)
    elif system == "bookstore":
        name = BOOKSTORE_NAME_MAP.get(name, name)
    
    return name


def calculate_metrics(generated_services, reference_services, system_name: str = "petclinic"):
    """Calculate Precision, Recall, and F1-Score."""
    gen_normalized = set(normalize_service_name(s, system_name) for s in generated_services)
    ref_normalized = set(normalize_service_name(s, system_name) for s in reference_services)

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
    """Print a formatted evaluation report."""
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
# Referências
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
# Execução do Experimento
# ============================================

def executar_experimento(llm, system_name: str, requirements: str, reference_services: list, timestamp: str):
    """
    Executa o experimento completo para um sistema:
    1. Agente 1 (Architect A) -> Gera proposta
    2. Agente 2 (Architect B) -> Gera proposta alternativa
    3. Agente 3 (Validator) -> Consolida propostas
    4. Avaliação -> Precision, Recall, F1
    """
    print(f"\n{'█'*70}")
    print(f"EXPERIMENTO: {system_name}")
    print(f"{'█'*70}\n")

    # Criar diretório de saída
    run_dir = criar_diretorio_run(system_name, timestamp)
    print(f"📁 Resultados serão salvos em: {run_dir}\n")

    # --- Criar Agentes ---
    print("📋 CRIANDO AGENTES...")
    agente1 = criar_agente1(llm)
    agente2 = criar_agente2(llm)
    agente3 = criar_agente3(llm)
    print(f"  ✓ {agente1.role}")
    print(f"  ✓ {agente2.role}")
    print(f"  ✓ {agente3.role}")

    # --- Criar Tasks ---
    print("\n📝 CRIANDO TASKS...")
    task1 = criar_task_arquitetura(agente1)
    task2 = criar_task_arquitetura_alternativa(agente2)
    task3 = criar_task_consolidacao(agente3)
    print("  ✓ Tasks criadas")

    resultados = {}

    # --- Executar Agente 1 ---
    print(f"\n{'='*60}")
    print(f"EXECUTANDO AGENTE 1: {agente1.role}")
    print(f"{'='*60}")

    try:
        crew1 = Crew(
            agents=[agente1],
            tasks=[task1],
            verbose=True,
        )
        output_a = crew1.kickoff(inputs={"requirements": requirements})
        resultados["proposta_a"] = str(output_a)
        salvar_proposta(run_dir, "proposta_a", str(output_a))
        print(f"\n✅ Proposta A gerada com sucesso!")
    except Exception as e:
        print(f"✗ Erro no Agente 1: {str(e)}")
        resultados["proposta_a"] = None

    # --- Executar Agente 2 ---
    print(f"\n{'='*60}")
    print(f"EXECUTANDO AGENTE 2: {agente2.role}")
    print(f"{'='*60}")

    try:
        crew2 = Crew(
            agents=[agente2],
            tasks=[task2],
            verbose=True,
        )
        output_b = crew2.kickoff(inputs={"requirements": requirements})
        resultados["proposta_b"] = str(output_b)
        salvar_proposta(run_dir, "proposta_b", str(output_b))
        print(f"\n✅ Proposta B gerada com sucesso!")
    except Exception as e:
        print(f"✗ Erro no Agente 2: {str(e)}")
        resultados["proposta_b"] = None

    # --- Executar Agente 3 (Validador) ---
    if resultados["proposta_a"] and resultados["proposta_b"]:
        print(f"\n{'='*60}")
        print(f"EXECUTANDO AGENTE 3: {agente3.role}")
        print(f"{'='*60}")

        try:
            crew3 = Crew(
                agents=[agente3],
                tasks=[task3],
                verbose=True,
            )
            output_c = crew3.kickoff(
                inputs={
                    "architecture_a": resultados["proposta_a"],
                    "architecture_b": resultados["proposta_b"],
                }
                
            )
            resultados["consolidada"] = str(output_c)
            salvar_proposta(run_dir, "consolidada", str(output_c))
            print(f"\n✅ Arquitetura Consolidada gerada com sucesso!")
        except Exception as e:
            print(f"✗ Erro no Agente 3: {str(e)}")
            resultados["consolidada"] = None
    else:
        print("\n⚠ Propostas A e/ou B não disponíveis. Pulando consolidação.")
        resultados["consolidada"] = None

    # --- Avaliação ---
    print(f"\n{'='*60}")
    print("AVALIAÇÃO DOS RESULTADOS")
    print(f"{'='*60}")

    metricas = {}
    for key, label in [("proposta_a", "PROPOSTA A - Software Architect"),
                       ("proposta_b", "PROPOSTA B - Alternative Architect"),
                       ("consolidada", "ARQUITETURA CONSOLIDADA")]:
        if resultados.get(key):
            services = parse_csv_architecture(resultados[key])
            print(f"\n📋 Serviços extraídos de {label}: {services}")
            metrics = calculate_metrics(services, reference_services, system_name.lower())
            metricas[key] = metrics
            print_evaluation_report(metrics, f"{system_name} - {label}")
        else:
            metricas[key] = None
    # --- Avaliação de Interações ---
    print(f"\n{'='*60}")
    print("AVALIAÇÃO DE INTERAÇÕES (RQ2)")
    print(f"{'='*60}")

    inter_ref = PETCLINIC_INTERACTIONS_REFERENCE if system_name.lower() == "petclinic" else BOOKSTORE_INTERACTIONS_REFERENCE

    for key, label in [("proposta_a", "PROPOSTA A"), ("proposta_b", "PROPOSTA B"), ("consolidada", "ARQUITETURA CONSOLIDADA")]:
        if resultados.get(key):
            gen_inter = parse_csv_interactions(resultados[key], system_name.lower())
            inter_metrics = evaluate_interactions(gen_inter, inter_ref)
            print(f"\n{label}:")
            print(f"  Precisão: {inter_metrics['precision']:.4f} | Recall: {inter_metrics['recall']:.4f} | F1: {inter_metrics['f1_score']:.4f}")
            print(f"  TP: {inter_metrics['tp_count']} | FP: {inter_metrics['fp_count']} | FN: {inter_metrics['fn_count']}")
            # adicionar ao dicionário de métricas para salvar
            metricas[f"{key}_inter"] = inter_metrics

    # Salvar métricas e sumário
    salvar_metricas(run_dir, metricas)
    salvar_sumario_json(run_dir, metricas)
    salvar_relatorio_md(run_dir, system_name, metricas)

    # --- Comparação Final ---
    print(f"\n{'█'*70}")
    print(f"COMPARAÇÃO FINAL - {system_name}")
    print(f"{'█'*70}\n")

    if all(metricas.values()):
        print(f"{'Métrica':<20} {'Proposta A':<15} {'Proposta B':<15} {'Consolidada':<15}")
        print(f"{'-'*20} {'-'*15} {'-'*15} {'-'*15}")
        print(f"{'Precision':<20} {metricas['proposta_a']['precision']:<15.4f} {metricas['proposta_b']['precision']:<15.4f} {metricas['consolidada']['precision']:<15.4f}")
        print(f"{'Recall':<20} {metricas['proposta_a']['recall']:<15.4f} {metricas['proposta_b']['recall']:<15.4f} {metricas['consolidada']['recall']:<15.4f}")
        print(f"{'F1-Score':<20} {metricas['proposta_a']['f1_score']:<15.4f} {metricas['proposta_b']['f1_score']:<15.4f} {metricas['consolidada']['f1_score']:<15.4f}")
        print(f"{'Serviços':<20} {metricas['proposta_a']['generated_count']:<15} {metricas['proposta_b']['generated_count']:<15} {metricas['consolidada']['generated_count']:<15}")
        print(f"{'Match (TP)':<20} {metricas['proposta_a']['match_count']:<15} {metricas['proposta_b']['match_count']:<15} {metricas['consolidada']['match_count']:<15}")

        scores = {
            'Proposta A': metricas['proposta_a']['f1_score'],
            'Proposta B': metricas['proposta_b']['f1_score'],
            'Consolidada': metricas['consolidada']['f1_score'],
        }
        best = max(scores, key=scores.get)
        print(f"\n🏆 Melhor proposta: {best} (F1 = {scores[best]:.4f})")
    else:
        print("Métricas insuficientes para comparação.")

    print(f"\n{'█'*70}\n")
    return resultados, metricas


# ============================================
# Main
# ============================================

def main():
    parser = argparse.ArgumentParser(
        description="Experimento Multiagente - Geração de Arquiteturas de Microsserviços"
    )
    parser.add_argument(
        "--system", "-s",
        choices=["petclinic", "bookstore"],
        default="petclinic",
        help="Sistema para executar o experimento (default: petclinic)"
    )
    parser.add_argument(
        "--all", "-a",
        action="store_true",
        help="Executar experimento com todos os sistemas"
    )
    args = parser.parse_args()

    # Carregar configuração
    print("="*60)
    print("MULTIAGENT ARCHITECTURE GENERATION")
    print("="*60)
    print("\n⚙️  Carregando configuração...")
    api_key, model_name = carregar_config()

    # Criar LLM
    llm = criar_llm(api_key, model_name)

    # Timestamp único para esta execução
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Executar experimentos
    if args.all:
        print("\n📋 Executando experimento para TODOS os sistemas...")
        executar_experimento(
            llm, "PETCLINIC", PETCLINIC_REQUIREMENTS, PETCLINIC_REFERENCE, timestamp
        )
        executar_experimento(
            llm, "BOOKSTORE", BOOKSTORE_REQUIREMENTS, BOOKSTORE_REFERENCE, timestamp
        )
    else:
        system = args.system
        if system == "petclinic":
            executar_experimento(
                llm, "PETCLINIC", PETCLINIC_REQUIREMENTS, PETCLINIC_REFERENCE, timestamp
            )
        else:
            executar_experimento(
                llm, "BOOKSTORE", BOOKSTORE_REQUIREMENTS, BOOKSTORE_REFERENCE, timestamp
            )

    print("\n✅ Experimento concluído com sucesso!")
    print(f"   Resultados salvos em: {RESULTS_ROOT.absolute()}")


if __name__ == "__main__":
    main()