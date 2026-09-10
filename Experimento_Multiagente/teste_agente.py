import os
from dotenv import load_dotenv

from crewai import Agent, Task, Crew, LLM


# Carrega variáveis do .env
load_dotenv()


# Verifica API KEY
api_key = os.getenv("DEEPSEEK_API_KEY")
model_name = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")

if not api_key:
    raise Exception("DEEPSEEK_API_KEY não encontrada no arquivo .env")

print("✓ API KEY do DeepSeek encontrada")


# Configura LLM via DeepSeek
llm = LLM(
    model=f"deepseek/{model_name}",
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