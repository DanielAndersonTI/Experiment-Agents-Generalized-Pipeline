"""
Agente 1: Software Architect (Arquiteto A)
Abordagem tradicional DDD (Domain Driven Design)
Foco: Decomposição baseada em bounded contexts

Baseado no notebook multiagent_architecture_generation.ipynb - Fase 2
"""

from crewai import Agent, Task


def criar_agente1(llm):
    """
    Cria o Agente 1 - Software Architect (Arquiteto Tradicional)
    
    Especialização: Microsserviços, Domain Driven Design (DDD),
    Decomposição baseada em responsabilidades
    
    Args:
        llm: Modelo de linguagem configurado (Google Gemini via CrewAI LLM)
    
    Returns:
        Agent: Agente CrewAI configurado
    """
    agente = Agent(
        role="Software Architect",
        goal="""
        Propor uma arquitetura de microsserviços baseada em requisitos textuais.
        Inclua SOMENTE serviços explicitamente descritos nos requisitos funcionais.
        Não adicione infraestrutura (gateway, discovery, config, admin) a menos que seja um requisito explícito.

        Para cada microsserviço, você deve:
        1. Identificar um nome descritivo baseado em responsabilidades de negócio
        2. Listar as responsabilidades principais
        3. Especificar quais outros serviços ele se comunica

        Use princípios de Domain Driven Design (DDD) e bounded contexts.
        """,
        backstory="""
        Você é um arquiteto de software sênior especializado em microsserviços.
        
        Sua experiência inclui:
        - Decomposição de monólitos usando Domain Driven Design
        - Identificação de bounded contexts
        - Design de comunicação entre serviços
        - Análise de responsabilidades de negócio
        
        Você pensa criteriosamente sobre a estrutura de um sistema,
        buscando separação clara de responsabilidades e coesão máxima.
        """,
        llm=llm,
        verbose=True,
        memory=False,
    )
    return agente


def criar_task_arquitetura(agente):
    """
    Cria a Task para gerar arquitetura de microsserviços
    
    Args:
        agente: O agente que executará a task
    
    Returns:
        Task: Task CrewAI configurada
    """
    task = Task(
        description="""
        Analyze the following system requirements and propose a microservices architecture.
        
        Your output MUST be EXACTLY in this CSV format (no markdown, no explanations):
        
        Microservice,Responsibilities,Communicates With
        Service Name,responsibility1;responsibility2;responsibility3,Service1;Service2;Service3
        
        Rules:
        - One row per microservice
        - Separate multiple items with semicolons (;)
        - NO markdown formatting, NO headers, NO extra text
        - List services in a logical order
        - Consider DDD bounded contexts
        - Include ONLY the services explicitly described in the requirements — do NOT add infrastructure unless it is a functional requirement.
        
        System Requirements:
        {requirements}
        """,
        expected_output="CSV format with microservices, their responsibilities, and communications",
        agent=agente,
    )
    return task