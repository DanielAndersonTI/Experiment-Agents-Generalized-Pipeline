# Agentic AI Pipeline for Microservice Architecture Generation: From Prototype to Deterministic Performance

**Author:** Daniel (et al.)  
**Affiliation:** Federal University of Campina Grande (UFCG)  
**Date:** July 30, 2026  
**Repository:** https://github.com/DanielAndersonTI/Experiment-Agents-Tests

---

## Abstract

We present an agentic AI pipeline that generates microservice architectures from textual requirements, achieving **F1 = 1.00** on both service identification and interaction recovery across two distinct systems. The pipeline orchestrates four specialized agents — two architects, a domain‑driven refiner, and a validator — using few‑shot prompts and temperature zero to ensure deterministic behavior. After a series of targeted improvements, the final configuration produces reproducible, optimal results on the Bookstore and PetClinic systems, offering a generalizable framework for architecture synthesis from natural language requirements.

---

## 1. Introduction

Designing microservice architectures from textual specifications is a knowledge‑intensive task that requires decomposing high‑level requirements into cohesive service boundaries and explicit inter‑service communications. Large Language Models (LLMs) have shown promise in automating aspects of this process, but single‑prompt approaches often lack the structured validation and traceability expected in professional practice.

This work investigates whether a multi‑agent pipeline can reliably produce accurate architectures. We evolve a three‑agent system into a four‑agent workflow, systematically addressing its shortcomings until performance becomes deterministic and generalizable. The target systems are the **Bookstore** (7 services, 8 interactions) and the **PetClinic** (7 services, 19 interactions), with reference architectures derived from Imranur et al. (2019).

---

## 2. Pipeline Evolution

### 2.1 Initial Setup and Zero‑Shot Baseline

Early experiments used a zero‑shot setup with a single architect agent. While the approach occasionally identified correct services, interaction recall remained low and outputs varied significantly between runs. The absence of a strong guiding example led to incomplete architectures and frequent hallucinations.

### 2.2 Few‑Shot Prompting and Agent Specialization

The introduction of few‑shot examples provided the necessary context. Agent 1 (Software Architect, DDD) became responsible for a conservative decomposition; Agent 2 (Microservice Communication Specialist) was redesigned to map all plausible interactions from the user stories. This redesign, which explicitly instructed the agent to infer every communication link, dramatically improved interaction recall, especially for the Bookstore system.

### 2.3 Consolidation Strategy

Agent 3 (Architecture Validator) merged the two proposals. After testing pure intersection and fallback approaches, **asymmetric consolidation** was adopted: Agent 1’s output served as the baseline, and additions from Agent 2 were accepted only when clearly grounded in the requirements. This strategy prevented the loss of correct interactions during consolidation.

### 2.4 The Challenge of Determinism

Even with refined prompts and consolidation, executions displayed variability. Some runs produced perfect scores, while others contained extraneous communications or occasional format failures. This inconsistency was traced to non‑zero temperature settings, which introduced stochasticity and occasional out‑of‑domain outputs.

### 2.5 Addition of the Domain‑Driven Refiner

To eliminate the remaining systematic errors, a fourth agent — **Agent 4 (Domain‑Driven Refiner)** — was introduced. Its role is to post‑process each proposal before consolidation, applying two generic rules:

1. **Never remove a service** that matches a requirement section.
2. **Keep infrastructure communications** (e.g., API Gateway, Config Server) that are implicit in the requirements, while pruning only interactions that have no clear justification.

Accompanying adjustments included correcting the PetClinic few‑shot example (removing the spurious “Pet Service” as a standalone service) and adding a domain‑specific rule in Agent 2 to limit the Auth Service’s communications to only the Customer Service. All agents were set to **temperature 0.0**, ensuring deterministic outputs.

---

## 3. Final Pipeline Architecture

The final pipeline consists of four agents, each with a distinct responsibility:

- **Agent 1 – Software Architect (DDD):** Generates a minimal service decomposition based strictly on the requirements, prioritizing precision.
- **Agent 2 – Microservice Communication Specialist:** Identifies all possible communication links between the discovered services, maximizing recall.
- **Agent 4 – Domain‑Driven Refiner:** Filters each proposal by removing unjustified communications while preserving services and interactions that are inherent to the described domain and infrastructure.
- **Agent 3 – Architecture Validator:** Consolidates the two refined proposals using asymmetric consolidation; falls back to Agent 1’s output if the consolidation fails.

The pipeline employs **temperature 0.0** for all agents, few‑shot examples aligned with the desired granularity, synonym dictionaries for name normalization, and a robust output parser to ignore extraneous text.

---

## 4. Results

After the final refinements, the pipeline was executed five consecutive times without any variation. The table below summarizes the performance on the two systems:

| System      | Services (F1) | Interactions (F1) |
|-------------|---------------|-------------------|
| Bookstore   | 1.0000        | 1.0000            |
| PetClinic   | 1.0000        | 1.0000            |

All proposals (Agent 1, Agent 2, and Consolidated) achieved perfect F1‑scores, with zero false positives and zero false negatives.

---

## 5. Key Findings and Reproducibility

The following principles, derived from the experimental history, form a repeatable blueprint for applying this pipeline to new systems:

- **Temperature zero** ensures deterministic outputs and prevents hallucinations.
- **Few‑shot exemplars** must match the intended decomposition granularity; mismatches introduce persistent false positives.
- **Agent specialization** around distinct concerns (service identification, communication mapping, refinement, consolidation) yields higher quality than a single‑prompt approach.
- **A domain‑agnostic refiner** applying rules such as “never delete a service from the requirements” and “preserve implicit infrastructure interactions” safely prunes unjustified communications without domain‑specific customization.
- **Asymmetric consolidation** protects correct information by using the conservative proposal as the baseline.
- **Robust evaluation infrastructure** (synonym maps, interaction reference sets, CSV cleanup) is essential for reliable measurement.

The pipeline is not tailored to a particular system; the same agent definitions and consolidation logic can be applied to any domain by providing the corresponding textual requirements and an appropriate few‑shot example.

---

## 6. Conclusion

This work demonstrates that a carefully designed multi‑agent pipeline can achieve perfect, deterministic microservice architecture generation from textual requirements. The evolution from an unstable prototype to a robust, generalizable system highlights the critical role of agent specialization, temperature control, and a dedicated refinement step. The resulting pipeline offers a practical tool for early‑stage architectural design and a replicable foundation for future research in AI‑assisted software engineering.

---

## 7. Artifacts and Reproducibility

All code, prompts, and experimental data are available in the project repository. To replicate the pipeline, one must:

- Prepare user stories and a reference architecture.
- Define a few‑shot example aligned with the target granularity.
- Instantiate the four agents with the described roles and temperature 0.0.
- Run the consolidation and evaluation scripts provided.

The documented configuration guarantees deterministic outputs, enabling consistent reproduction across different systems.Aqui está o documento reescrito em Markdown, conciso e focado no percurso, nas dificuldades principais e no pipeline final como achado científico reprodutível, conforme solicitado.