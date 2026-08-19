"""
Experimento Multiagente - Geração de Arquiteturas de Microsserviços
Executa Agente A, Agente B e Validador para PetClinic e Bookstore
Salva todos os resultados em arquivos
"""
import os
import sys
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
import pandas as pd
import json

# LangChain + Google Gemini
from langchain_google_genai import ChatGoogleGenerativeAI

# CrewAI
from crewai import Agent, Task, Crew

# ============================================================
# CONFIGURAÇÃO INICIAL
# ============================================================

# Carregar .env
load_dotenv()

# Criar pasta de resultados
RESULTS_DIR = Path("resultados")
RESULTS_DIR.mkdir(exist_ok=True)

# Timestamp para nomear arquivos
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

# Configurar LLM
llm = ChatGoogleGenerativeAI(
    model=os.getenv("GOOGLE_MODEL", "gemini-1.5-pro"),
    temperature=0.3,
    max_output_tokens=2000,
)

# ============================================================
# DEFINIÇÃO DOS AGENTES
# ============================================================

# Agente 1: Software Architect (DDD Tradicional)
software_architect = Agent(
    role="Software Architect",
    goal="""Propor uma arquitetura de microsserviços baseada em requisitos textuais...
    (copie o goal e backstory do notebook)""",
    backstory="""Você é um arquiteto de software sênior...""",
    llm=llm,
    verbose=True,
    memory=False,
)

# Agente 2: Alternative Architect
alternative_architect = Agent(
    role="Alternative Software Architect",
    goal="""Propor uma arquitetura ALTERNATIVA...""",
    backstory="""Você é um arquiteto com visão inovadora...""",
    llm=llm,
    verbose=True,
    memory=False,
)

# Agente 3: Validador
validator = Agent(
    role="Architecture Validator",
    goal="""Comparar duas propostas e gerar versão consolidada...""",
    backstory="""Você é um arquiteto líder...""",
    llm=llm,
    verbose=True,
    memory=False,
)

# ============================================================
# DEFINIÇÃO DAS TASKS
# ============================================================

# Task para gerar arquitetura (formato CSV)
generate_task = Task(
    description="""Analyze the following system requirements...
    System Requirements:
    {requirements}""",
    expected_output="CSV format with microservices",
    agent=software_architect,
)

# Task para gerar arquitetura alternativa
generate_alternative_task = Task(
    description="""Analyze the following system requirements...
    System Requirements:
    {requirements}""",
    expected_output="CSV format with alternative architecture",
    agent=alternative_architect,
)

# Task para consolidar
consolidate_task = Task(
    description="""Compare the two architecture proposals...
    ARCHITECTURE A:
    {architecture_a}
    
    ARCHITECTURE B:
    {architecture_b}""",
    expected_output="Consolidated architecture with decisions",
    agent=validator,
)

# ============================================================
# REQUISITOS DOS SISTEMAS
# ============================================================

petclinic_requirements = """
Spring PetClinic Microservices - Requirements
(copie o texto completo do notebook)
"""

bookstore_requirements = """
Bookstore Microservices - Requirements
(copie o texto completo do notebook)
"""

# ============================================================
# SERVIÇOS DE REFERÊNCIA (para avaliação)
# ============================================================

petclinic_reference = [
    "api-gateway", "config-server", "discovery-server",
    "admin-server", "customers-service", "vets-service", "visits-service",
]

bookstore_reference = [
    "api-gateway", "config-server", "discovery-server",
    "book-service", "order-service", "customer-service",
    "inventory-service", "shipping-service", "notification-service",
]

# ============================================================
# FUNÇÕES DE AVALIAÇÃO
# ============================================================

def parse_csv_architecture(csv_text):
    """Extrai nomes de serviços do CSV gerado"""
    services = []
    for line in csv_text.strip().split('\n'):
        line = line.strip()
        if not line or line.startswith('Microservice'):
            continue
        parts = line.split(',')
        if parts:
            services.append(parts[0].strip().lower().replace(' ', '-'))
    return services

def normalize(name):
    """Normaliza nome do serviço para comparação"""
    return name.lower().strip().replace(' ', '-').replace('_', '-').removesuffix('-service')

def calculate_metrics(generated, reference):
    """Calcula Precision, Recall, F1"""
    gen_set = {normalize(s) for s in generated}
    ref_set = {normalize(s) for s in reference}
    
    tp = gen_set & ref_set
    fp = gen_set - ref_set
    fn = ref_set - gen_set
    
    precision = len(tp) / len(gen_set) if gen_set else 0.0
    recall = len(tp) / len(ref_set) if ref_set else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
    
    return {
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1_score": round(f1, 4),
        "true_positives": sorted(tp),
        "false_positives": sorted(fp),
        "false_negatives": sorted(fn),
        "generated_count": len(gen_set),
        "reference_count": len(ref_set),
        "match_count": len(tp),
    }

# ============================================================
# FUNÇÃO PRINCIPAL: executar experimento para um sistema
# ============================================================

def run_experiment(system_name, requirements, reference_services):
    """Executa o experimento completo para um sistema"""
    print(f"\n{'='*60}")
    print(f"EXPERIMENTO: {system_name}")
    print(f"{'='*60}")
    
    resultados = {}
    
    # --- Proposta A ---
    print(f"\n[1/3] Gerando Proposta A (Software Architect)...")
    crew_a = Crew(agents=[software_architect], tasks=[generate_task], verbose=True)
    output_a = crew_a.kickoff(inputs={"requirements": requirements})
    
    # Salvar proposta A
    file_a = RESULTS_DIR / f"{system_name}_proposta_A_{timestamp}.txt"
    with open(file_a, "w", encoding="utf-8") as f:
        f.write(str(output_a))
    print(f"  Salvo em: {file_a}")
    
    # --- Proposta B ---
    print(f"\n[2/3] Gerando Proposta B (Alternative Architect)...")
    crew_b = Crew(agents=[alternative_architect], tasks=[generate_alternative_task], verbose=True)
    output_b = crew_b.kickoff(inputs={"requirements": requirements})
    
    # Salvar proposta B
    file_b = RESULTS_DIR / f"{system_name}_proposta_B_{timestamp}.txt"
    with open(file_b, "w", encoding="utf-8") as f:
        f.write(str(output_b))
    print(f"  Salvo em: {file_b}")
    
    # --- Consolidação ---
    print(f"\n[3/3] Consolidando arquiteturas...")
    crew_v = Crew(agents=[validator], tasks=[consolidate_task], verbose=True)
    output_consolidated = crew_v.kickoff(inputs={
        "architecture_a": str(output_a),
        "architecture_b": str(output_b)
    })
    
    # Salvar consolidada
    file_c = RESULTS_DIR / f"{system_name}_consolidada_{timestamp}.txt"
    with open(file_c, "w", encoding="utf-8") as f:
        f.write(str(output_consolidated))
    print(f"  Salvo em: {file_c}")
    
    # --- Avaliação ---
    print(f"\n[AVALIAÇÃO] Calculando métricas...")
    
    services_a = parse_csv_architecture(str(output_a))
    services_b = parse_csv_architecture(str(output_b))
    services_c = parse_csv_architecture(str(output_consolidated))
    
    metrics_a = calculate_metrics(services_a, reference_services)
    metrics_b = calculate_metrics(services_b, reference_services)
    metrics_c = calculate_metrics(services_c, reference_services)
    
    # Criar DataFrame comparativo
    df = pd.DataFrame({
        "Métrica": ["Precision", "Recall", "F1-Score", "Serviços Gerados", "Match (TP)"],
        "Proposta A": [metrics_a["precision"], metrics_a["recall"], metrics_a["f1_score"], metrics_a["generated_count"], metrics_a["match_count"]],
        "Proposta B": [metrics_b["precision"], metrics_b["recall"], metrics_b["f1_score"], metrics_b["generated_count"], metrics_b["match_count"]],
        "Consolidada": [metrics_c["precision"], metrics_c["recall"], metrics_c["f1_score"], metrics_c["generated_count"], metrics_c["match_count"]],
    })
    
    # Salvar tabela
    file_table = RESULTS_DIR / f"{system_name}_metricas_{timestamp}.csv"
    df.to_csv(file_table, index=False)
    print(f"  Tabela salva em: {file_table}")
    
    # Salvar JSON completo
    resultados = {
        "system": system_name,
        "timestamp": timestamp,
        "metrics": {
            "proposta_a": metrics_a,
            "proposta_b": metrics_b,
            "consolidada": metrics_c,
        },
        "files": {
            "proposta_a": str(file_a),
            "proposta_b": str(file_b),
            "consolidada": str(file_c),
        }
    }
    
    file_json = RESULTS_DIR / f"{system_name}_resultados_{timestamp}.json"
    with open(file_json, "w", encoding="utf-8") as f:
        json.dump(resultados, f, indent=2, ensure_ascii=False)
    print(f"  JSON completo salvo em: {file_json}")
    
    # Exibir resumo
    print(f"\n{'='*60}")
    print(f"RESUMO - {system_name}")
    print(f"{'='*60}")
    print(df.to_string(index=False))
    
    return resultados

# ============================================================
# EXECUÇÃO PRINCIPAL
# ============================================================

if __name__ == "__main__":
    print("█"*70)
    print("EXPERIMENTO MULTIAGENTE - ARQUITETURAS DE MICROSSERVIÇOS")
    print("█"*70)
    
    # Executar PetClinic
    resultados_petclinic = run_experiment("PetClinic", petclinic_requirements, petclinic_reference)
    
    # Executar Bookstore
    resultados_bookstore = run_experiment("Bookstore", bookstore_requirements, bookstore_reference)
    
    print(f"\n{'█'*70}")
    print("EXPERIMENTO CONCLUÍDO!")
    print(f"Todos os resultados em: {RESULTS_DIR.absolute()}")
    print(f"{'█'*70}")