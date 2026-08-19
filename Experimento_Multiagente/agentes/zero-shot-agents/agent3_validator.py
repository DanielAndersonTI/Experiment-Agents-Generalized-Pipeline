"""
Agente 3: Validator Agent (Validador)
Responsável por comparar duas propostas de arquitetura e gerar versão consolidada

Baseado no notebook multiagent_architecture_generation.ipynb - Fase 4
"""

from crewai import Agent, Task


def criar_agente3(llm):
    """
    Cria o Agente 3 - Architecture Validator (Validador)
    
    Responsabilidades:
    1. Analisar ambas as propostas (Architect A e Architect B)
    2. Identificar serviços comuns entre elas
    3. Identificar serviços únicos de cada proposta
    4. Consolidar em uma arquitetura final que combine o melhor de ambas
    5. Explicar as decisões de consolidação
    
    Args:
        llm: Modelo de linguagem configurado (Google Gemini via CrewAI LLM)
    
    Returns:
        Agent: Agente CrewAI configurado
    """
    agente = Agent(
        role="Architecture Validator",
        goal="""
        Comparar duas propostas de arquitetura de microsserviços e gerar uma versão consolidada.
        
        Você deve:
        1. Analisar ambas as propostas (Architect A e Architect B)
        2. Identificar serviços comuns entre elas
        3. Identificar serviços únicos de cada proposta
        4. Consolidar em uma arquitetura final que combine o melhor de ambas
        5. Explicar as decisões de consolidação
        """,
        backstory="""
        Você é um arquiteto líder com vasta experiência em revisão de designs.
        
        Sua especialidade:
        - Revisão e validação de arquiteturas de software
        - Identificação de overlaps e gaps em propostas
        - Tomada de decisão baseada em trade-offs
        - Comunicação clara de decisões arquiteturais
        
        Você consegue enxergar o melhor de diferentes abordagens
        e combiná-las em uma solução coesa e bem fundamentada.
        """,
        llm=llm,
        verbose=True,
        memory=True,
    )
    return agente


def criar_task_consolidacao(agente):
    task = Task(
        description="""
        Compare the two architecture proposals below and generate a consolidated version.

CRITICAL FORMAT RULES:
- Your ENTIRE output must begin with the exact line:
  === CONSOLIDATED ARCHITECTURE ===
- Then output one CSV line per service with these columns:
  Microservice,Responsibilities,Communicates With,Source
- After the last service, output the line:
  === DECISIONS ===
- Then add bullet-point explanations (one per line, starting with "- ").
- Do NOT add any other text, no markdown code blocks, no extra commentary.
- If the two architectures are completely identical (same services, same interactions),
  simply output the same architecture with Source column "A+B" for every service,
  and in DECISIONS state: "Both proposals are identical; no consolidation needed."
- Never generate content unrelated to microservice architecture.

ARCHITECTURE A:
{architecture_a}

ARCHITECTURE B:
{architecture_b}
""",
    expected_output="Consolidated architecture CSV with decisions",
    agent=agente,
)
    return task