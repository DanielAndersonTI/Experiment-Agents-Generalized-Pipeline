"""
Script de teste rapido: Executa apenas o Agente 1 (Software Architect) com PetClinic
Para testar se a configuracao esta funcionando
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Adiciona diretorio atual ao path para importar agentes
sys.path.insert(0, str(Path(__file__).parent))

from crewai import LLM, Crew
from agentes.agent1_architect_a import criar_agente1, criar_task_arquitetura

# Carregar .env
env_path = Path(__file__).parent / '.env'
load_dotenv(env_path)

api_key = os.getenv("OPENROUTER_API_KEY")
model_name = os.getenv("OPENROUTER_MODEL", "deepseek/deepseek-chat-v3-0324:free")

if not api_key:
    print("ERRO: OPENROUTER_API_KEY nao configurada!")
    sys.exit(1)

print("="*60)
print("TESTE: AGENTE 1 - SOFTWARE ARCHITECT")
print("Sistema: Spring PetClinic")
print("="*60)

# Criar LLM
print(f"\n[OK] Inicializando modelo: {model_name}")
llm = LLM(
    model=f"openrouter/{model_name}",
    api_key=api_key,
    temperature=0.3,
)
print("[OK] Modelo inicializado")

# Criar agente e task
print("\n[OK] Criando Agente 1...")
agente1 = criar_agente1(llm)
print(f"  Role: {agente1.role}")

task1 = criar_task_arquitetura(agente1)
print("  Task criada")

# Requisitos PetClinic
petclinic_requirements = """
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

# Executar
print(f"\n{'='*60}")
print("EXECUTANDO AGENTE 1...")
print(f"{'='*60}")

try:
    crew = Crew(
        agents=[agente1],
        tasks=[task1],
        verbose=True,
    )

    resultado = crew.kickoff(inputs={"requirements": petclinic_requirements})

    print(f"\n{'='*60}")
    print("RESULTADO:")
    print(f"{'='*60}")
    print(resultado)
    print(f"\n[OK] Agente 1 executado com sucesso!")

except KeyboardInterrupt:
    print("\n\n[!] Execucao interrompida pelo usuario (loop detectado)")
    sys.exit(0)
except Exception as e:
    print(f"\n[ERRO] {str(e)}")
    import traceback
    traceback.print_exc()