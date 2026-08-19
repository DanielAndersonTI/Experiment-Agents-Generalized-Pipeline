import os
from dotenv import load_dotenv

from crewai import Agent, Task, Crew, LLM


# Carrega variáveis do .env
load_dotenv()


# Verifica API KEY
api_key = os.getenv("OPENROUTER_API_KEY")
model_name = os.getenv("OPENROUTER_MODEL", "deepseek/deepseek-chat-v3-0324:free")

if not api_key:
    raise Exception("OPENROUTER_API_KEY não encontrada no arquivo .env")

print("✓ API KEY do OpenRouter encontrada")


# Configura LLM via OpenRouter
llm = LLM(
    model=f"openrouter/{model_name}",
    api_key=api_key,
    temperature=0.2
)


# Criando agente simples
agente = Agent(
    role="Analista de Sistemas",
    goal="Analisar arquitetura de software",
    backstory="""
    Você é especialista em engenharia de software
    e arquitetura de sistemas distribuídos.
    """,
    llm=llm,
    verbose=True
)


# Tarefa
tarefa = Task(
    description="""
    Explique em poucas linhas a arquitetura
    de microsserviços do Spring Petclinic.
    """,
    expected_output="""
    Uma explicação técnica contendo:
    - serviços existentes
    - comunicação
    - benefícios
    """,
    agent=agente
)


# Executa
crew = Crew(
    agents=[agente],
    tasks=[tarefa],
    verbose=True
)


resultado = crew.kickoff()

print("\n========== RESULTADO ==========\n")
print(resultado)