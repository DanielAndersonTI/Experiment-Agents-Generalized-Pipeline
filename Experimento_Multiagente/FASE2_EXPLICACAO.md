# Explicação: Primeiro Agente - Software Architect Agent

## 📋 O que foi criado?

Implementamos a **Fase 2** do experimento: o primeiro agente do sistema multiagente usando **CrewAI** e **LangChain**.

---

## 🔧 Componentes Implementados

### 1. **Software Architect Agent**

```python
software_architect_agent = Agent(
    role="Software Architect",
    goal="""...""",
    backstory="""...""",
    llm=llm,
    verbose=True,
    memory=True,
)
```

**O que é:** Um agente que encarna um arquiteto de software sênior.

**Parâmetros:**
- `role` - Define o papel/título do agente
- `goal` - O objetivo principal que o agente persegue
- `backstory` - Experiência e contexto do agente (melhora decisões)
- `llm` - Modelo de linguagem (nosso ChatOpenAI com temperatura 0.3)
- `verbose=True` - Exibe o raciocínio interno do agente
- `memory=True` - Mantém histórico de contexto entre mensagens

**Por que?** 
- Um "backstory" bem definido torna o LLM mais especializado
- `verbose=True` permite entender como o agente pensa
- `memory=True` ajuda o agente a manter consistência

---

### 2. **Task: Generate Microservices Architecture**

```python
generate_architecture_task = Task(
    description="""...""",
    expected_output="CSV format...",
    agent=software_architect_agent,
)
```

**O que é:** Uma tarefa específica que o agente deve executar.

**Parâmetros:**
- `description` - Instruções detalhadas (com placeholders `{requirements}`)
- `expected_output` - Formato esperado (guia o LLM)
- `agent` - Qual agente executa esta task

**Formato de Saída - CSV:**
```
Microservice,Responsibilities,Communicates With
Service1,resp1;resp2,Service2;Service3
Service2,resp3;resp4,Service1;Service3
```

Por que CSV?
- Fácil de parsear
- Estruturado para comparação automática
- Reproduz o formato do experimento original
- Sem ambiguidades de parsing

---

### 3. **Crew (Equipe)**

```python
crew = Crew(
    agents=[software_architect_agent],
    tasks=[task_with_requirements],
    verbose=True,
    process="sequential"
)

result = crew.kickoff()
```

**O que é:** Orquestrador que gerencia agentes e tasks.

**Por que Crew?**
- Coordena múltiplos agentes (teremos 3: A, B, Validador)
- Gerencia dependências entre tasks
- Mantém contexto compartilhado
- `sequential` = executa uma tarefa por vez

---

## 🔄 Fluxo de Execução

```
1. PetClinic Requirements (texto)
          ↓
2. Task com descrição + requirements
          ↓
3. Software Architect Agent (pensa + raciocina)
          ↓
4. LLM (OpenAI o3)
          ↓
5. Resposta em CSV
          ↓
6. Crew retorna resultado
          ↓
7. Salvo em: petclinic_architecture_output
```

---

## 📊 Exemplo de Saída Esperada

Para PetClinic, o agente deveria gerar algo como:

```
Microservice,Responsibilities,Communicates With
Customers Service,Manage clients;Link pets to owners,Visits Service;API Gateway
Vets Service,Manage veterinarians;View specialties,API Gateway
Visits Service,Register visits;View visit history,Customers Service;API Gateway
API Gateway,Route client requests to services,Customers Service;Vets Service;Visits Service
Config Server,Manage service configurations,All services
Discovery Server,Service registry using Eureka,All services
Admin Server,Monitor services,All services
```

---

## 🎯 Diferenças Importantes

### Zero-Shot vs Our Agent

**Experimento Original (Zero-Shot):**
```python
prompt = "Dados os requisitos... Gere microsserviços"
response = llm.invoke(prompt)
```

**Nossa Abordagem (Agent com CrewAI):**
```python
agent = Agent(role, goal, backstory, llm)  # Especialização
task = Task(description, expected_output)   # Instruções estruturadas
crew = Crew(agents, tasks)                  # Orquestração
result = crew.kickoff()                     # Execução
```

**Vantagens:**
- ✅ Agente "pensa" como arquiteto (backstory)
- ✅ Histórico mantido (`memory=True`)
- ✅ Execução pensada/raciocínio visível (`verbose=True`)
- ✅ Escalável para múltiplos agentes
- ✅ Estrutura preparada para Validador

---

## 🔗 Próximas Fases

### Fase 3: Segundo Agente (Architect B)

```python
software_architect_agent_b = Agent(
    role="Alternative Software Architect",
    goal="""LIGEIRAMENTE DIFERENTE - 
    Use abordagem alternativa (focus em escalabilidade)""",
    backstory="""Especialista em performance e escalabilidade...""",
    llm=llm,
)
```

**Por quê?**
- Mesma tarefa, abordagens diferentes
- Gera propostas alternativas independentes
- Base para o Validador comparar

### Fase 4: Agente Validador

```python
validator_agent = Agent(
    role="Architecture Validator",
    goal="""Compare as duas propostas de arquitetura
    e consolide em uma arquitetura final""",
)

consolidation_task = Task(
    description="""Dado Arquitetura A e Arquitetura B,
    analise, compare, e proponha versão consolidada""",
)
```

### Fase 5: Avaliação

```python
# Parsear CSV → grafo
# Comparar com referência (bookstore_ref.dot, petclinic_ref.dot)
# Calcular Precision, Recall, F1
```

---

## 🐛 Possíveis Erros ao Executar

| Erro | Causa | Solução |
|------|-------|---------|
| "API Key invalid" | OPENAI_API_KEY não configurada | Adicionar à `.env` |
| "Model not found" | "o3" requer acesso especial | Usar "gpt-4o" ou "gpt-4-turbo" |
| "Rate limit exceeded" | Muitas chamadas muito rápido | Aguardar alguns segundos |
| "Timeout" | Resposta muito lenta | Aumentar timeout ou reduzir max_tokens |

---

## 📌 Código-Chave para Reutilizar

Quando criar **Architect B** (Fase 3), use este padrão:

```python
# Apenas mude role, goal, backstory
architect_b_agent = Agent(
    role="Alternative Software Architect",  # ← DIFERENTE
    goal="""Considere escalabilidade e performance...""",  # ← DIFERENTE
    backstory="""Especialista em padrões modernos...""",  # ← DIFERENTE
    llm=llm,
    verbose=True,
    memory=True,
)

# Task é IDÊNTICA
task_b = Task(
    description=generate_architecture_task.description,  # ← IGUAL
    expected_output=generate_architecture_task.expected_output,  # ← IGUAL
    agent=architect_b_agent,  # ← OUTRO AGENTE
)

# Crew é IGUAL
crew_b = Crew(
    agents=[architect_b_agent],
    tasks=[task_b],
    verbose=True,
)
```

---

## 🎓 Conceitos Aplicados

| Conceito | Onde | Por que |
|----------|------|--------|
| **CrewAI** | Orquestração de agentes | Permite múltiplos agentes colaborarem |
| **Agent** | Define especialização | Backstory melhora qualidade de resposta |
| **Task** | Define trabalho específico | Separação de responsabilidades |
| **LLM** | Motor de resposta | LangChain + OpenAI |
| **DDD** | Instruções ao agente | Melhora qualidade arquitetural |
| **CSV Format** | Output estruturado | Fácil parsing automático |
| **Verbose Mode** | Depuração | Entender raciocínio do agente |

---

## ✅ Validação: Como Saber que Funcionou?

1. ✓ `Software Architect Agent criado com sucesso` (print)
2. ✓ `Task 'Generate Microservices Architecture' criada` (print)
3. ✓ Agente exibe pensamentos (verbose=True)
4. ✓ Resultado em formato CSV
5. ✓ Microsserviços com responsabilidades sensatas
6. ✓ Comunicações lógicas entre serviços

---

## 📚 Estrutura Final do Notebook

```
Fase 1: Setup & Ambiente ✓
  ├─ Importações
  ├─ dotenv
  ├─ OpenAI/LangChain
  └─ Teste de conexão

Fase 2: Primeiro Agente ✓ (NOVO)
  ├─ CrewAI imports
  ├─ Software Architect Agent
  ├─ Task: Generate Architecture
  ├─ PetClinic requirements
  ├─ Execução do Crew
  └─ Status

Fase 3: Segundo Agente (PRÓXIMA)
  ├─ Architect B (com variação)
  └─ Task análoga

Fase 4: Validador (DEPOIS)
  ├─ Validator Agent
  └─ Consolidation Task

Fase 5: Avaliação (FINAL)
  ├─ Parser CSV → Grafo
  ├─ Comparador
  └─ Métricas (Precision, Recall, F1)
```

---

## 🚀 Próximo Comando do Usuário

Esperamos por:
- "Criar segundo agente"
- "Adicionar validador"
- "Implementar avaliação"
- "Executar experimento completo"

Notebook está pronto para extensão! 🎯
