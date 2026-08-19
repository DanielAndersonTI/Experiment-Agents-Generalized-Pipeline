import os
from dotenv import load_dotenv

from crewai import LLM
from agentes.agent1 import criar_agente1


load_dotenv()

api_key = os.getenv("OPENROUTER_API_KEY")
model_name = os.getenv("OPENROUTER_MODEL", "deepseek/deepseek-chat-v3-0324:free")

if not api_key:
    raise Exception("OPENROUTER_API_KEY não encontrada")


llm = LLM(
    model=f"openrouter/{model_name}",
    api_key=api_key,
    temperature=0.2
)


agente1 = criar_agente1(llm)


print("\n===== AGENTE 1 =====")
print(agente1.role)
print(agente1.goal)
print("====================")


resposta = agente1.execute_task(
    "Analise a arquitetura do Spring Petclinic e liste seus principais serviços."
)


print("\n===== RESPOSTA =====")
print(resposta)