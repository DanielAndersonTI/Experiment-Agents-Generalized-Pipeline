# Pipeline History and Evolution

**Multi-Agent Pipeline for Microservice Architecture Generation**

**Author:** Daniel Anderson de Souza Silva
**Partnership:** Virtus UFCG
**Main Model:** Google Gemini (`gemini/gemini-flash-latest`)
**Temperature:** `0.0`
**Current Artifact:** DAVINCI Architect
**Last Updated:** **August 20, 2026**

> **Historical note:** This document records the evolution of the multi-agent pipeline throughout its development. Some configurations, agent behaviors, and experimental results described in the historical sections are no longer part of the current implementation. The **Current State** section reflects the most recent version of the system as of **August 20, 2026**.

---

## 1. Overview

This document consolidates the history, architectural decisions, experimental iterations, lessons learned, and current state of the multi-agent pipeline developed for generating microservice architectures from textual system requirements.

The pipeline evolved through several experimental stages, beginning with relatively independent LLM-based architecture proposals and progressing toward a specialized multi-agent architecture composed of four roles:

1. **Software Architect (DDD)**
2. **Microservice Communication Specialist**
3. **Domain-Driven Refiner**
4. **Architecture Validator and Consolidator**

All agents currently operate with `temperature=0.0` and use a combination of Domain-Driven Design (DDD), bounded contexts, generalized few-shot prompting, architectural reasoning patterns, and requirements-based analysis.

The central objective of the project is to develop a **generalizable, reproducible, and reusable approach** for generating and evaluating microservice decompositions without relying on domain-specific knowledge of the systems used as benchmarks.

The pipeline has subsequently been operationalized through **DAVINCI Architect**, a local web application that allows the same process to be applied to different systems through structured inputs and automated execution.

---

# 2. Development Timeline

The evolution of the pipeline can be divided into several major stages.

| Period                            | Development Stage           | Main Change                                                      |
| --------------------------------- | --------------------------- | ---------------------------------------------------------------- |
| **July 9, 2026**                  | Initial experiments         | Agent 2 operated as an alternative architecture generator        |
| **July 21–23, 2026**              | Agent specialization        | Agent 2 was redesigned around communication inference            |
| **July 29, 2026**                 | Consolidation refinement    | Agent 3 and consolidation policies were modified                 |
| **July 30, 2026**                 | Deterministic configuration | All agents moved to `temperature=0.0`                            |
| **Late July 2026**                | Generalization              | Domain-specific references were progressively removed            |
| **Late July / early August 2026** | Interaction reasoning       | Abstract interaction-pattern library introduced for Agent 2      |
| **August 2026**                   | Pipeline stabilization      | Agent roles and consolidation strategy were progressively frozen |
| **August 19, 2026**               | Application layer           | DAVINCI Architect interface and automated reporting operational  |
| **August 20, 2026**               | Current state               | Reusable research prototype ready for systematic experimentation |

> **Important:** The July experiments should be interpreted as development experiments rather than as the final experimental configuration. Their purpose was to identify architectural problems, unstable behaviors, and effective design decisions.

---

# 3. Pipeline Architecture

The current pipeline contains four specialized agents.

## 3.1 Agent 1 — Software Architect (DDD)

Agent 1 generates the primary architecture proposal based exclusively on textual system requirements.

Its responsibilities include:

* Identifying business capabilities.
* Grouping related responsibilities.
* Applying Domain-Driven Design principles.
* Identifying bounded contexts.
* Defining candidate services.
* Proposing justified service interactions.
* Maintaining a conservative decomposition strategy.

The agent does not receive the ground-truth architecture of the evaluated system.

---

## 3.2 Agent 2 — Microservice Communication Specialist

Agent 2 produces an independent architecture proposal with particular emphasis on inter-service communication.

Its main objective is to identify interactions that can be justified directly from the requirements.

The agent uses a generalized library of architectural reasoning patterns covering concepts such as:

* Data dependency.
* Action dependency.
* Validation.
* Workflow dependencies.
* Existence constraints.
* Ownership.
* Cross-service operations.
* Unsupported transitive dependencies.
* Unnecessary full-mesh communication.

The examples are intentionally abstract and domain-independent to reduce the risk of benchmark-specific overfitting.

---

## 3.3 Agent 4 — Domain-Driven Refiner

Agent 4 operates as a conservative refinement stage.

Its primary responsibility is to remove unsupported communications from the candidate architectures without changing their fundamental service decomposition.

The current refinement policy does not allow the agent to:

* Create services.
* Delete services.
* Split services.
* Merge services.
* Rename services.
* Invent unsupported interactions.

The refiner therefore acts primarily as a filtering stage over the architectural proposals.

---

## 3.4 Agent 3 — Architecture Validator and Consolidator

Agent 3 receives the refined proposals and produces the final architecture.

The consolidation strategy evolved throughout the experiments.

The current design follows an **asymmetric consolidation strategy**, in which Proposal A serves as the primary architectural basis while complementary interactions from Proposal B may be incorporated when supported by the requirements.

In later versions, preliminary evaluation metrics are also made available to the consolidation process, allowing the final decision to consider the measured quality of the candidate proposals.

The goal is not simply to merge the two architectures, but to preserve the strongest architectural structure while incorporating complementary evidence when justified.

---

# 4. Early Development

## 4.1 Initial Agent 2

The first versions of the pipeline treated Agent 2 as a second general-purpose architecture generator.

The objective was to obtain two independent architectural hypotheses and subsequently consolidate them.

However, this configuration produced substantial instability.

In several early PetClinic executions, Agent B generated incomplete or poorly structured service decompositions. Similar instability appeared in Bookstore, although the results were generally stronger.

The main problem identified was that two agents attempting to independently reconstruct the complete architecture did not necessarily provide complementary information.

---

# 5. Agent 2 Specialization

## 5.1 Communication Specialist

During **July 21–23, 2026**, Agent 2 was redesigned to focus specifically on communication inference.

Instead of treating both agents as equivalent architecture generators, the pipeline began assigning complementary responsibilities:

```text
Agent A
Software Architecture / DDD
        │
        ├──────────────┐
        │              │
        ▼              ▼
Service Decomposition   Agent B
                       Communication Specialist

```

This change was motivated by the observation that service identification and interaction identification represent different reasoning problems.

The specialization improved the usefulness of Proposal B as an independent source of architectural evidence.

---

# 6. Temperature and Reproducibility

## 6.1 Adoption of `temperature=0.0`

One of the most important configuration changes occurred in **late July 2026**.

Earlier experiments used configurations such as:

```text
temperature = 0.3
```

These executions showed greater variability and occasional hallucinated or structurally inconsistent outputs.

The pipeline was subsequently standardized to:

```text
temperature = 0.0
```

for all agents.

This became an important methodological decision because the research requires controlled and reproducible executions.

The move to temperature zero did not eliminate all variation originating from the underlying model or execution environment, but substantially reduced unnecessary stochasticity in the generation process.

---

# 7. Generalization of the Agents

During the second half of July 2026, the agents were progressively generalized.

The main objective was to prevent the pipeline from learning the architecture of the benchmark systems through its prompts.

References such as:

* PetClinic-specific services.
* Bookstore-specific services.
* Benchmark-specific interactions.
* Domain-specific decomposition rules.

were progressively removed from the agent definitions.

The resulting architecture treats few-shot examples primarily as **references for reasoning style, output structure, and level of detail**, rather than as knowledge about the target system.

---

# 8. Generalized Interaction Reasoning Library

One of the most significant modifications was the introduction of a generalized interaction-reasoning library for Agent 2.

The library contains approximately **90 abstract reasoning patterns** covering different forms of inter-service dependency.

Examples include:

* Data dependencies.
* Action dependencies.
* Validation dependencies.
* Workflow dependencies.
* Existence constraints.
* Ownership relationships.
* Legitimate cross-service communication.
* Transitivity errors.
* Full-mesh communication.
* Unsupported dependency propagation.

The purpose of this library was to provide architectural knowledge without encoding the specific architecture of the benchmark systems.

This represented an important transition from **domain-specific prompting** toward **general architectural reasoning**.

---

# 9. Experiment: Making Agent 2 Dependent on Agent 1

A configuration was tested in which Agent 2 received the architecture generated by Agent 1 as an explicit input.

The intention was to stabilize Agent B and transform it into a dedicated interaction-analysis specialist.

Although this produced more symmetrical outputs, it also made Agent B highly dependent on A and frequently redundant.

In practice, B tended to reproduce the architectural decisions already made by A rather than provide genuinely independent evidence.

This configuration was therefore discarded.

The current architecture preserves **independence between the primary proposals** before the refinement and consolidation stages.

---

# 10. Evolution of the Consolidation Strategy

The consolidation stage underwent several modifications.

## 10.1 Initial Consolidation

Early versions tended to preserve Proposal A as the primary result even when Proposal B contained stronger evidence in some dimensions.

This could cause useful interactions identified by B to be lost.

---

## 10.2 Complementary Interaction Recovery

A subsequent strategy allowed valid interactions present in B but absent from A to be incorporated into the final architecture when supported by the requirements.

This improved the ability of the consolidated architecture to recover complementary information.

---

## 10.3 Metric-Aware Consolidation

A later modification moved part of the evaluation process into the pipeline itself.

Before invoking the final validator, `main_fewshot.py` calculates preliminary metrics for Proposals A and B.

The resulting information can then be provided to the consolidation stage.

The objective is to make the final decision more evidence-based instead of relying exclusively on qualitative LLM judgment.

---

# 11. Evaluation Infrastructure

The pipeline includes automated evaluation components for:

* Service identification.
* Interaction identification.
* Precision.
* Recall.
* F1-score.

It also supports normalization of service names before evaluation.

Results are stored using timestamped execution directories:

```text
result/
└── <system>/
    └── result_generalized_fewshot/
        └── run_<timestamp>/
```

Typical artifacts include:

```text
proposta_a.csv
proposta_b.csv
consolidada.csv
metricas_servicos.csv
metricas_interacoes.csv
sumario.json
report.md
```

This structure allows individual executions to be preserved and compared retrospectively.

---

# 12. Historical Experimental Results

## 12.1 Best Results Observed During Development

The strongest results observed during the development process included:

| System    | Best Proposal             | Services F1 | Interaction Precision | Interaction Recall | Interaction F1 |
| --------- | ------------------------- | ----------: | --------------------: | -----------------: | -------------: |
| PetClinic | Proposal B                |      1.0000 |                1.0000 |             0.9474 |         0.9730 |
| Bookstore | Proposal A / Consolidated |      1.0000 |                1.0000 |             0.8750 |         0.9333 |

These values represent **development-stage best observations**, rather than the final statistical result of the complete experimental study.

---

# 13. PetClinic Development History

The following table records selected PetClinic executions performed during the development process.

| Date/Time   | Development Stage                          | Services A | Services B | Services Cons. | Interactions A | Interactions B | Interactions Cons. |
| ----------- | ------------------------------------------ | ---------: | ---------: | -------------: | -------------: | -------------: | -----------------: |
| 09/07 21:10 | Original Agent 2 — DeepSeek, 0.3           |     0.9333 |     0.0000 |         0.9333 |         0.8095 |         0.0000 |             0.7727 |
| 09/07 21:38 | Original Agent 2                           |     1.0000 |     0.4706 |         1.0000 |         1.0000 |         0.1875 |             1.0000 |
| 09/07 21:44 | Original Agent 2                           |     0.9333 |     0.4706 |         0.9333 |         0.8444 |         0.1667 |             0.8444 |
| 09/07 21:49 | Original Agent 2                           |     1.0000 |     0.3750 |         1.0000 |         0.7333 |         0.0889 |             0.7059 |
| 09/07 22:21 | Original Agent 2                           |     0.9333 |     0.8750 |         0.9333 |         0.8372 |         0.7234 |             0.8182 |
| 09/07 22:38 | Original Agent 2                           |     0.9333 |     0.8750 |         0.9333 |         0.8372 |         0.7727 |             0.8372 |
| 21/07 00:15 | Original Agent 2                           |     0.5455 |     0.9333 |         0.5455 |         0.0870 |         0.7805 |             0.0870 |
| 22/07 21:50 | Modified Agent 2 — DeepSeek, 0.3           |     0.8000 |     0.2500 |         0.0000 |         0.6809 |         0.3571 |             0.0000 |
| 22/07 22:22 | Modified Agent 2                           |     0.8000 |     0.0000 |         0.0000 |         0.6809 |         0.0000 |             0.0000 |
| 22/07 23:08 | Modified Agent 2                           |     0.9333 |     0.5455 |         0.5000 |         0.8636 |         0.0909 |             0.0870 |
| 22/07 23:20 | Modified Agent 2                           |     0.8000 |     0.8000 |         0.7500 |         0.6809 |         0.6809 |             0.6667 |
| 22/07 23:45 | Modified Agent 2                           |     0.9333 |     0.9333 |         0.8750 |         0.8636 |         0.8636 |             0.8444 |
| 22/07 23:54 | Modified Agent 2                           |     0.9333 |     0.9333 |         0.9333 |         0.8636 |         0.8636 |             0.8636 |
| 23/07 00:07 | Modified Agent 2                           |     0.0000 |     0.9333 |         0.5455 |         0.0000 |         0.8636 |             0.0909 |
| 29/07 23:09 | Agent 3 — Temperature 0.0, DeepSeek        |     0.9333 |     0.9333 |         0.8750 |         0.8636 |         0.8636 |             0.8444 |
| 29/07 23:14 | Agent 3 — Temperature 0.0                  |     0.9333 |     0.9333 |         0.8750 |         0.8636 |         0.8636 |             0.8444 |
| 29/07 23:21 | Agent 3 — Temperature 0.0                  |     0.9333 |     0.9333 |         0.8750 |         0.8636 |         0.8636 |             0.8444 |
| 29/07 23:23 | Agent 3 — Temperature 0.0                  |     0.9333 |     0.9333 |         0.0000 |         0.8636 |         0.8636 |             0.0000 |
| 30/07 00:09 | All Agents — Temperature 0.0, DeepSeek     |     0.9333 |     0.9333 |         0.9333 |         0.8636 |         0.8636 |             0.8636 |
| 30/07 00:12 | All Agents — Temperature 0.0, DeepSeek     |     0.9333 |     0.9333 |         0.9333 |         0.8636 |         0.8636 |             0.8636 |
| 30/07 00:17 | All Agents — Temperature 0.0, DeepSeek     |     0.9333 |     0.0000 |         0.8750 |         0.8636 |         0.0000 |             0.8444 |
| 30/07 00:24 | All Agents — Temperature 0.0, DeepSeek     |     0.0000 |     0.0000 |         0.0000 |         0.0000 |         0.0000 |             0.0000 |
| 30/07 01:31 | All Agents — Temperature 0.0, Gemini Flash |     0.9333 |     0.9333 |         0.9333 |         0.8636 |              — |                  — |
| 30/07 01:35 | All Agents — Temperature 0.0, Gemini Flash |          — |     0.9333 |              — |              — |         0.8636 |                  — |

> **Date convention:** The historical records above preserve the original `DD/MM` notation used during development. All dates refer to **2026**.

---

# 14. Bookstore Development History

| Date/Time   | Services A | Services B | Services Cons. | Interactions A | Interactions B | Interactions Cons. |
| ----------- | ---------: | ---------: | -------------: | -------------: | -------------: | -----------------: |
| 09/07 21:11 |     0.8571 |     0.1111 |         0.8571 |         0.5714 |         0.0000 |             0.5714 |
| 09/07 21:33 |     0.8571 |     0.0000 |         0.8571 |         0.5000 |         0.0000 |             0.5000 |
| 09/07 21:40 |     1.0000 |     0.5556 |         1.0000 |         0.7500 |         0.0000 |             0.7500 |
| 09/07 21:45 |     1.0000 |     0.1000 |         1.0000 |         0.5714 |         0.0000 |             0.5714 |
| 09/07 21:51 |     1.0000 |     0.0000 |         1.0000 |         0.8235 |         0.0000 |             0.8235 |
| 09/07 22:22 |     1.0000 |     0.3333 |         1.0000 |         0.6087 |         0.0000 |             0.6087 |
| 09/07 22:39 |     1.0000 |     0.6316 |         1.0000 |         0.5714 |         0.0385 |             0.5714 |
| 21/07 00:16 |     1.0000 |     0.7368 |         0.9333 |         0.8750 |         0.2540 |             0.7619 |
| 22/07 17:13 |     1.0000 |     0.7143 |         1.0000 |         0.8750 |         0.3158 |             0.8750 |
| 22/07 17:49 |     1.0000 |     1.0000 |         1.0000 |         0.8750 |         0.7143 |             0.8750 |
| 22/07 18:42 |     1.0000 |     1.0000 |         1.0000 |         0.8000 |         0.7143 |             0.8000 |
| 22/07 20:00 |     1.0000 |     1.0000 |         1.0000 |         0.8750 |         0.8750 |             0.8750 |
| 22/07 21:27 |     1.0000 |     1.0000 |         1.0000 |         1.0000 |         1.0000 |             1.0000 |
| 22/07 23:12 |     1.0000 |     1.0000 |         1.0000 |         1.0000 |         1.0000 |             1.0000 |
| 22/07 23:57 |     1.0000 |     1.0000 |         1.0000 |         1.0000 |         1.0000 |             1.0000 |
| 23/07 00:08 |     1.0000 |     1.0000 |         1.0000 |         1.0000 |         1.0000 |             1.0000 |
| 29/07 23:09 |     1.0000 |     1.0000 |         1.0000 |         1.0000 |         1.0000 |             1.0000 |
| 29/07 23:15 |     1.0000 |     1.0000 |         1.0000 |         1.0000 |         1.0000 |             1.0000 |
| 29/07 23:18 |     1.0000 |     1.0000 |         1.0000 |         1.0000 |         1.0000 |             1.0000 |
| 29/07 23:21 |     1.0000 |     1.0000 |         1.0000 |         1.0000 |         1.0000 |             1.0000 |
| 30/07 00:09 |     1.0000 |     1.0000 |         1.0000 |         1.0000 |         1.0000 |             1.0000 |
| 30/07 00:17 |     1.0000 |     1.0000 |         1.0000 |         1.0000 |         0.9412 |             1.0000 |
| 30/07 01:32 |     1.0000 |     1.0000 |         1.0000 |         1.0000 |         0.7619 |             1.0000 |
| 30/07 01:36 |     1.0000 |     1.0000 |         1.0000 |         1.0000 |         0.7273 |             1.0000 |

> **Date convention:** The historical records above preserve the original `DD/MM` notation used during development. All dates refer to **2026**.

---

# 15. Lessons Learned

The development process produced several important observations.

1. **Temperature `0.0` is important for controlled experiments.**
   Reducing unnecessary stochasticity improved reproducibility and made changes to the pipeline easier to investigate.

2. **Agent specialization provides complementary reasoning.**
   Separating service decomposition from interaction analysis provides a more meaningful division of responsibilities than asking multiple agents to independently perform exactly the same task.

3. **Agent 2 should remain independent from Agent 1.**
   Making B directly dependent on A reduced its ability to provide independent architectural evidence.

4. **Excessive conservatism reduces the value of Agent 2.**
   The communication specialist needs sufficient freedom to recover interactions that may not appear in the primary proposal.

5. **Abstract architectural examples are preferable to benchmark-specific examples.**
   The interaction library can provide useful reasoning patterns without revealing the expected architecture of the target system.

6. **Large domain-specific decomposition libraries can negatively affect Agent 1.**
   Increasing the number of examples does not necessarily improve architectural reasoning and can interfere with the conservative DDD strategy.

7. **Changes should be isolated whenever possible.**
   Simultaneously changing several agents makes it difficult to determine which modification caused an observed improvement or degradation.

8. **The conservative refiner serves a distinct role.**
   Separating refinement from generation allows unsupported communications to be filtered without fundamentally changing the service decomposition.

9. **Consolidation requires an explicit policy.**
   Simply merging two LLM-generated architectures can introduce errors. The consolidation process must define how conflicting and complementary proposals are handled.

10. **Ground truth must not be provided to the generation agents.**
    Reference services, interactions, and benchmark-specific information must remain restricted to evaluation.

---

# 16. Overfitting and Generalization

## 16.1 Definition of Overfitting

Within this project, overfitting occurs when an agent receives information that effectively reveals the expected architecture of the target system.

Examples include:

* Explicitly naming expected services.
* Providing known benchmark interactions.
* Providing the decomposition of PetClinic or Bookstore.
* Using examples that closely reproduce the target system.

The following are **not considered benchmark-specific overfitting**:

* Teaching DDD principles.
* Teaching bounded contexts.
* Teaching ownership.
* Teaching generic dependency patterns.
* Teaching common architectural mistakes.
* Teaching when a service interaction should not be created.

---

## 16.2 Generalization Strategy

The current approach uses several mechanisms to reduce benchmark-specific dependency:

* Few-shot examples are used primarily as references for reasoning and output structure.
* Interaction examples are domain-independent.
* Agent 1 focuses on business capabilities rather than predefined services.
* Agent 4 applies generic architectural constraints.
* Ground-truth architecture is used exclusively for evaluation.
* The same pipeline can receive requirements from different systems.

---

# 17. Current State — August 20, 2026

> **This section represents the current state of the project as of August 20, 2026. It supersedes earlier descriptions of the pipeline where configurations have changed.**

The pipeline has moved beyond the exploratory stage and is now implemented as a reusable execution workflow.

The current architecture consists of:

```text
System Requirements
        │
        ├──────────────────────┐
        ▼                      ▼
   Agent 1                 Agent 2
Software Architect      Communication
     (DDD)               Specialist
        │                      │
        └──────────┬───────────┘
                   ▼
              Agent 4
               Refiner
                   │
                   ▼
              Agent 3
        Validator / Consolidator
                   │
                   ▼
          Final Architecture
                   │
          ┌────────┴────────┐
          ▼                 ▼
       Services        Interactions
          │                 │
          └────────┬────────┘
                   ▼
              Evaluation

```

All agents currently operate with:

```text
temperature = 0.0
```

The system is currently configured around Google Gemini and supports automated evaluation and report generation.

---

## 17.1 Current Results and Progress — August 20, 2026

By the end of **August 20, 2026**, the pipeline had been converted from the earlier exploratory version into a real, interface-driven system. The main technical changes made on this date were:

* **Metric-aware consolidation:** `main_fewshot.py` now calculates preliminary service and interaction metrics for Proposals A and B before invoking Agent 3. These metrics are passed to the final validator so that the consolidated architecture is selected based on evidence, not only on qualitative LLM preference.
* **Explicit interaction reasoning for Agent 1:** Agent 1’s task now includes a dedicated section on identifying inter-service communications. It distinguishes data, action, validation, result/status, and workflow dependencies, while rejecting conceptual, transitive, optional, or unsupported relationships.
* **Independent refinement:** Agent 4 is still applied separately to Proposal A and Proposal B before consolidation.
* **Removal of the CLI entry point from `main_fewshot.py`:** the pipeline now exposes `executar_pipeline(...)` as the public function called by the web interface.

The most recent executions of the day demonstrated that the consolidation strategy is now capable of preserving or improving the best individual proposal. In the last run of the day, the final consolidated results were:

| System    | Consolidated Services F1 | Consolidated Interactions F1 |
| --------- | -----------------------: | ---------------------------: |
| PetClinic |                   1.0000 |                       0.9143 |
| Bookstore |                   1.0000 |                       0.8571 |

These values reflect the actual output of the DAVINCI Architect interface using the real pipeline, not mock data. The interaction results varied across runs, with PetClinic interactions ranging from approximately 0.70 to 0.91 and Bookstore interactions ranging from approximately 0.63 to 0.86 depending on the individual proposals generated in each execution. This variability is consistent with the known sensitivity of LLM-based inference, even at `temperature=0.0`.

The work performed up to this date therefore established a reusable research prototype that:

* Executes the full multi-agent pipeline through a local web interface.
* Accepts arbitrary systems through structured inputs.
* Computes both service and interaction metrics when reference data is available.
* Produces a consolidated architecture that can be equal to or better than the best individual proposal.

The next step is to **apply the same pipeline to additional systems beyond PetClinic and Bookstore**, such as MediaStore and TeaStore, and to conduct systematic comparisons against a single-LLM baseline across multiple executions. This will allow the research to evaluate whether the gains observed in the reference systems generalize to unseen domains.

---

# 18. DAVINCI Architect

During **August 2026**, the pipeline was operationalized through a local web application named **DAVINCI Architect**.

The application provides a reusable interface over the experimental pipeline.

Users can provide:

* System name.
* System requirements.
* Reference services.
* Reference interactions.
* Name normalization mappings.
* Architecture target.

The interface currently supports up to **five systems per execution**.

The application automatically:

1. Processes the submitted requirements.
2. Executes the multi-agent pipeline.
3. Generates candidate architectures.
4. Refines the proposals.
5. Consolidates the proposals.
6. Calculates evaluation metrics when reference data is available.
7. Stores the execution results.
8. Generates a complete report.

---

# 19. Research Prototype Architecture

The application separates the experimental pipeline from the presentation layer.

```text
DAVINCI Architect
│
├── Web Interface
│
├── Input Processing
│
├── Pipeline Runner
│       │
│       └── main_fewshot.py
│               │
│               ├── Agent 1
│               ├── Agent 2
│               ├── Agent 4
│               └── Agent 3
│
├── Evaluation
│
├── Result Storage
│
└── Report Generation

```

This separation allows the underlying pipeline to continue being used independently of the web interface.

It also makes the application suitable for future extensions to other software engineering tasks.

---

# 20. Reusability

The current implementation is no longer restricted to manually configured executions for PetClinic and Bookstore.

The interface was designed to accept new systems through structured inputs.

The intended workflow is:

```text
New System
    │
    ▼
Textual Requirements
    │
    ▼
DAVINCI Architect
    │
    ▼
Same Multi-Agent Pipeline
    │
    ▼
Architecture
    │
    ▼
Evaluation

```

This represents an important transition from an experiment-specific implementation toward a **reusable research artifact**.

The current system should therefore be described as a research prototype rather than as a universally validated architecture-generation platform. Generalization beyond the evaluated systems remains an empirical question that must be investigated through additional experiments.

---

# 21. Current Experimental Direction

As of **August 20, 2026**, the main development phase is considered substantially stabilized.

The research focus is moving from continuous modification of the pipeline toward systematic experimentation.

The central comparison is:

```text
Single LLM
     │
     ▼
Architecture
     │
     ▼
Evaluation

```

versus:

```text
Multi-Agent Pipeline
     │
     ├── Agent 1
     ├── Agent 2
     ├── Agent 4
     └── Agent 3
            │
            ▼
       Architecture
            │
            ▼
         Evaluation

```

The comparison should consider not only architectural quality but also the additional computational and operational cost introduced by the multi-agent approach.

Relevant dimensions include:

* Service Precision.
* Service Recall.
* Service F1.
* Interaction Precision.
* Interaction Recall.
* Interaction F1.
* Number of LLM calls.
* Execution time.
* Model usage/cost.
* Reproducibility.
* Human intervention required.

This allows the research to investigate whether the additional complexity of an agentic architecture produces sufficient benefits compared with a single-LLM approach.

---

# 22. Current Status

As of **August 20, 2026**, the project has reached the following state:

* Four specialized agents implemented.
* DDD-based architecture generation.
* Independent communication specialist.
* Conservative refinement stage.
* Metric-aware consolidation.
* Generalized prompting.
* Domain-independent interaction reasoning library.
* Temperature standardized to `0.0`.
* Automated service evaluation.
* Automated interaction evaluation.
* Name normalization.
* Timestamped execution results.
* Automated report generation.
* Local web interface.
* Multi-system input support.
* PDF report generation.
* Automated interface tests.
* Complete controlled comparison against a single-LLM baseline.
* Final systematic evaluation across the selected experimental systems.

---

# 23. Conclusion

The multi-agent pipeline evolved from an exploratory architecture-generation experiment into a structured and reusable research prototype.

The main development trajectory was:

```text
Independent LLM proposals
          ↓
Agent specialization
          ↓
DDD-based decomposition
          ↓
Communication reasoning
          ↓
Generalization
          ↓
Refinement
          ↓
Metric-aware consolidation
          ↓
Automated evaluation
          ↓
DAVINCI Architect

```

The development process demonstrated that simply increasing the number of agents or providing more examples does not automatically improve architectural quality. The main improvements came from **specialization, controlled prompting, generalized architectural knowledge, conservative refinement, and explicit consolidation policies**.

As of **August 20, 2026**, the technical implementation has reached a sufficiently stable state to support systematic experimental evaluation. The remaining research question is therefore not merely whether the pipeline can generate architectures, but whether the additional complexity and cost of the multi-agent approach provide measurable advantages over simpler LLM-based alternatives.

The **DAVINCI Architect** application serves as the reusable operational layer for this research, allowing the same pipeline to be executed across different systems while maintaining a standardized process for input, generation, evaluation, result storage, and reporting.

---

# Credits

**Developed by Daniel Anderson de Souza Silva**

In partnership with **Virtus UFCG**

Contact: `daniel.silva@virtus-cc.ufcg.edu.br`

© 2026 DAVINCI Architect. All rights reserved.
