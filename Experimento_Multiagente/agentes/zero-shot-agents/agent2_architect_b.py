"""
Agente 2: Alternative Architect (Arquiteto B)
Abordagem alternativa: Top-down, event-driven, escalabilidade
Foco: API Gateway, comunicação assíncrona, resiliência

Baseado no notebook multiagent_architecture_generation.ipynb - Fase 3
"""

from crewai import Agent, Task


def criar_agente2(llm):
    """
    Cria o Agente 2 - Alternative Architect (Arquiteto Alternativo)
    
    Abordagem DIFERENTE do arquiteto tradicional:
    - Começa pelo API Gateway e identifica serviços de borda
    - Comunicação event-driven entre serviços
    - Prioriza escalabilidade e isolamento de falhas
    - Considera serviços de infraestrutura (discovery, config, monitoring)
    
    Args:
        llm: Modelo de linguagem configurado (Google Gemini via CrewAI LLM)
    
    Returns:
        Agent: Agente CrewAI configurado
    """
    agente = Agent(
        role="Alternative Software Architect",
        goal="""
        Propor uma arquitetura de microsserviços ALTERNATIVA baseada em requisitos textuais.
        
        Sua abordagem é DIFERENTE do arquiteto tradicional:
        1. Comece pelo API Gateway e identifique os serviços de borda
        2. Pense em comunicação event-driven entre serviços
        3. Priorize escalabilidade e isolamento de falhas
        4. Considere serviços de infraestrutura (discovery, config, monitoring)
        
        Para cada microsserviço, você deve:
        1. Identificar um nome descritivo
        2. Listar as responsabilidades principais
        3. Especificar quais outros serviços ele se comunica
        """,
        backstory="""
        Você é um arquiteto de software sênior com visão inovadora.
        
        Sua experiência inclui:
        - Arquiteturas event-driven e message brokers
        - Sistemas distribuídos de alta escalabilidade
        - Microserviços com foco em resiliência (circuit breaker, retry)
        - Infraestrutura como código e service mesh
        
        Você frequentemente propõe soluções não convencionais que
        desafiam o status quo, sempre pensando em escalabilidade futura.
        """,
        llm=llm,
        verbose=True,
        memory=True,
    )
    return agente


def criar_task_arquitetura_alternativa(agente):
    """
    Cria a Task para gerar arquitetura ALTERNATIVA de microsserviços
    
    Args:
        agente: O agente que executará a task
    
    Returns:
        Task: Task CrewAI configurada
    """
    task = Task(
        description="""
        Analyze the following system requirements and propose an ALTERNATIVE microservices architecture.
        
        Your approach should be DIFFERENT from a traditional DDD decomposition.
        Think about event-driven communication, API Gateway patterns, and scalability.
        
        Your output MUST be EXACTLY in this CSV format (no markdown, no explanations):
        
        Microservice,Responsibilities,Communicates With
        Service Name,responsibility1;responsibility2;responsibility3,Service1;Service2;Service3
        
        Rules:
        - One row per microservice
        - Separate multiple items with semicolons (;)
        - NO markdown formatting, NO headers, NO extra text
        - Include infrastructure services (gateway, config, discovery)
        
        System Requirements:
        {requirements}
        """,
        expected_output="CSV format with alternative microservices architecture",
        agent=agente,
    )
    return task