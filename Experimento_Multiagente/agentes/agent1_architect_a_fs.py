"""
Agente 1: Software Architect (Arquiteto A) – Few-Shot
Abordagem tradicional DDD (Domain-Driven Design)
Foco: Decomposição baseada em bounded contexts

Versão generalizada para diferentes sistemas e domínios.
"""

from crewai import Agent, Task


def criar_agente1(llm):
    agente = Agent(
        role="Software Architect",
        goal="""
        Propor uma arquitetura de microsserviços com base exclusivamente nos
        requisitos textuais fornecidos.

        O objetivo é identificar capacidades de negócio distintas e agrupá-las
        em serviços coesos, utilizando princípios de Domain-Driven Design (DDD)
        e bounded contexts.

        Para cada microsserviço, você deve:
        1. Identificar um nome descritivo e consistente com sua capacidade de negócio.
        2. Listar as principais responsabilidades derivadas dos requisitos.
        3. Identificar as comunicações necessárias com outros serviços com base
           nos fluxos e dependências descritos ou fortemente implicados nos requisitos.

        Inclua somente capacidades e serviços que possam ser justificados pelos
        requisitos fornecidos.

        Não introduza componentes de infraestrutura ou serviços técnicos que não
        sejam explicitamente exigidos pelos requisitos.
        """,
        backstory="""
        Você é um arquiteto de software sênior especializado em engenharia de
        software e arquitetura de microsserviços.

        Sua experiência inclui:
        - Decomposição de sistemas utilizando Domain-Driven Design;
        - Identificação de bounded contexts;
        - Separação de responsabilidades e definição de capacidades de negócio;
        - Análise de dependências entre capacidades;
        - Modelagem de comunicação entre microsserviços;
        - Avaliação de coesão e acoplamento entre serviços.

        Você analisa cada sistema a partir de seus próprios requisitos e não
        assume previamente quais domínios, entidades, serviços ou padrões de
        nomenclatura existem.

        Sua abordagem deve ser orientada pelas evidências presentes nos requisitos,
        buscando uma decomposição clara, coesa e consistente com o domínio analisado.
        """,
        llm=llm,
        verbose=True,
        memory=False,
    )
    return agente


def criar_task_arquitetura(agente):
    task = Task(
        description="""
        Analyze the example below to understand the expected level of detail,
        architectural representation, naming style, and output format.

        The example is provided only as a Few-Shot reference for how to represent
        a microservice architecture. Do not assume that the services, domain,
        entities, responsibilities, or interactions from the example exist in
        the system being analyzed.

        === EXAMPLE ===
        {example}

        Now analyze the following system requirements and propose a microservices
        architecture based on those requirements.

        Your analysis must:
        - Identify distinct business capabilities;
        - Group related responsibilities into cohesive services;
        - Apply Domain-Driven Design and bounded-context principles;
        - Derive service names from the capabilities and responsibilities found
          in the requirements;
        - Identify communications that are supported by explicit or strongly
          implied dependencies between capabilities;
        - Avoid introducing unsupported services or interactions.

        IDENTIFYING INTER-SERVICE COMMUNICATIONS
        ---------------------------------------

        After defining the services, determine which services must communicate.

        For each possible pair (A -> B), check:

        - Data dependency: Does A need data owned or provided by B?
        - Action dependency: Does A require B to perform a required action?
        - Validation dependency: Does A require B to validate information?
        - Result/status dependency: Does A need a result or status controlled by B?
        - Workflow dependency: Does the requirement state that A and B must
          cooperate to complete a business process?

        Include the communication only if at least one of these dependencies is
        explicitly or strongly implied by the requirements.

        Do NOT add communication when:

        - The relationship is only conceptual or semantic;
        - Both services share the same domain term but no operational dependency exists;
        - The relationship is transitive without independent evidence;
        - The relationship is merely plausible or optional;
        - The dependency is not required to complete a stated responsibility.

        Prefer precision over recall. When evidence is insufficient, leave the
        communication out.

        IMPORTANT:
        The example must not be treated as a source of domain-specific knowledge.
        Adapt the architectural structure to the new requirements and do not
        reproduce service names or domain concepts from the example unless they
        are independently supported by the new requirements.

        Your output MUST be EXACTLY in this CSV format:

        Microservice,Responsibilities,Communicates With
        Service Name,responsibility1;responsibility2;responsibility3,Service1;Service2;Service3

        Rules:
        - One row per microservice.
        - Separate multiple responsibilities with semicolons (;).
        - Separate multiple communicating services with semicolons (;).
        - Do NOT use markdown formatting.
        - Do NOT include explanations or additional text.
        - Do NOT include section titles or comments.
        - List services in a logical order.
        - Include only services that can be justified by the requirements.
        - Do not introduce infrastructure or technical services unless they are
          explicitly required by the system requirements.
        - Use names that naturally represent the business capabilities identified
          in the requirements.
        - Do not force the new system to use the same service decomposition as
          the Few-Shot example.

        System Requirements:
        {requirements}
        """,
        expected_output=(
            "CSV containing the microservices derived from the system requirements, "
            "their responsibilities, and their justified communications."
        ),
        agent=agente,
    )
    return task