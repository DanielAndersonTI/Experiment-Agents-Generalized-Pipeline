"""
Agente 3: Validator Agent (Validador) – Few-Shot
Responsável por comparar duas propostas de arquitetura e gerar uma versão consolidada.

Abordagem orientada por métricas: recebe as métricas de A e B e escolhe a
melhor base, podendo combinar interações complementares quando suportadas.

Versão generalizada para diferentes sistemas e domínios.
"""

from crewai import Agent, Task


def criar_agente3(llm):
    agente = Agent(
        role="Architecture Validator",
        goal="""
        Comparar duas propostas de arquitetura de microsserviços usando as
        métricas de avaliação (Precision, Recall e F1) e produzir uma versão
        consolidada final.

        Você deve:
        1. Analisar as métricas de Serviços e Interações das propostas A e B.
        2. Usar as métricas para decidir qual proposta possui a melhor base
           de serviços.
        3. Usar as métricas para decidir qual proposta possui as interações
           de melhor qualidade.
        4. Se uma proposta for claramente superior tanto em serviços quanto
           em interações, utilize-a integralmente como base.
        5. Se uma proposta for melhor em serviços e a outra melhor em
           interações, utilize a base de serviços da melhor em serviços e,
           quando possível, incorpore interações complementares da melhor
           em interações, desde que os serviços envolvidos existam na base
           e que a interação seja fortemente sustentada pelos requisitos.
        6. Não inventar serviços ou interações.
        7. Preservar as responsabilidades exatamente como estiverem na base
           de serviços escolhida.
        """,
        backstory="""
        Você é um arquiteto de software sênior com ampla experiência em revisão,
        validação e consolidação de arquiteturas de microsserviços.

        Sua especialidade inclui:
        - Revisão de arquiteturas de software;
        - Domain-Driven Design;
        - Identificação de bounded contexts;
        - Análise de métricas de Precision, Recall e F1;
        - Seleção da melhor proposta entre alternativas;
        - Combinação conservadora de serviços e interações.

        Você utiliza as métricas de avaliação como evidência objetiva para
        decidir qual proposta deve servir de base e quais interações podem ser
        incorporadas. Você não adiciona interações apenas porque elas são
        plausíveis; elas precisam ser suportadas pelos requisitos e pelas
        métricas das propostas.

        Você não assume previamente quais domínios, entidades, serviços ou
        tecnologias existem no sistema analisado.
        """,
        llm=llm,
        verbose=True,
        memory=True,
    )
    return agente


def criar_task_consolidacao(agente):
    task = Task(
        description="""
        Compare the two architecture proposals below and generate a
        consolidated final architecture.

        You will receive:

        1. Architecture A
        2. Architecture B
        3. Evaluation metrics for A
        4. Evaluation metrics for B
        5. The system requirements

        Use the metrics to decide which proposal has the strongest services and
        which has the strongest interactions.

        IMPORTANT RULES:

        - If Architecture A has better services AND better interactions metrics,
          use Architecture A as the final architecture.

        - If Architecture B has better services AND better interactions metrics,
          use Architecture B as the final architecture.

        - If one proposal is better in services while the other is better in
          interactions, use the services from the proposal with the best service
          F1-score as the base.

          Then, from the proposal with the best interaction F1-score, add only
          interactions whose participating services already exist in the chosen
          base and whose dependency is strongly supported by the requirements.

        - Do NOT invent new services.

        - Do NOT change responsibilities.

        - Do NOT add interactions that would introduce false positives or that
          are not clearly justified.

        - If no interaction is justified for a service, leave the third column
          empty.

        - Preserve the original service names from the chosen base.

        ARCHITECTURE A:
        {architecture_a}

        ARCHITECTURE B:
        {architecture_b}

        METRICS FOR A:
        {metrics_a}

        METRICS FOR B:
        {metrics_b}

        SYSTEM REQUIREMENTS:
        {requirements}

        OUTPUT FORMAT:

        Microservice,Responsibilities,Communicates With
        Service Name,responsibility1;responsibility2,Service1;Service2

        Rules:
        - One row per microservice.
        - Separate responsibilities with semicolons (;).
        - Separate communicating services with semicolons (;).
        - Do NOT use markdown formatting.
        - Do NOT include explanations or additional text.
        - Do NOT include section titles or comments.
        - Do NOT include a Source column.

        Produce the consolidated CSV now.
        """,
        expected_output=(
            "CSV containing the consolidated microservices, their "
            "responsibilities, and their justified communications."
        ),
        agent=agente,
    )
    return task