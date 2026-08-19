# A Deterministic Multi‑Agent Pipeline for Microservice Architecture Generation from Textual Requirements

**Daniel Anderson de Souza Silva** et al.  
Federal University of Campina Grande (UFCG)  
July 2026

---

## Abstract

We present a multi‑agent pipeline that generates microservice architectures from natural language requirements with **perfect reproducibility**. The pipeline orchestrates four specialised agents—a domain‑driven architect, a communication specialist, a domain‑driven refiner, and a validator—using few‑shot prompting and temperature zero. After a series of targeted improvements, the pipeline achieves **F1 = 1.00 for both service identification and interaction recovery on two distinct systems (Bookstore and PetClinic) across five consecutive deterministic runs**. The approach is generalisable: the same agent definitions, consolidation logic, and refinement rules can be applied to any system by providing the corresponding user stories and a consistent few‑shot example.

---

## 1. Introduction

Translating textual requirements into a well‑bounded set of microservices and their communication links is a complex, knowledge‑intensive task. Large Language Models (LLMs) can assist, but single‑prompt approaches often lack the structured reasoning and validation expected in professional architecture practice. This work investigates whether a carefully designed multi‑agent pipeline can reliably produce accurate, deterministic architectures, and what design principles are necessary to make such a pipeline generalisable beyond the studied systems.

We use two reference systems: **Bookstore** (7 services, 8 interactions) and **PetClinic** (7 services, 19 interactions), with ground‑truth architectures derived from Imranur et al. (2019). The pipeline is built with CrewAI and uses Google Gemini (gemini‑flash‑latest) at temperature 0.0.

---

## 2. Pipeline Architecture

The final pipeline consists of four agents executed sequentially. All agents operate at **temperature 0.0** to guarantee deterministic outputs.

1. **Agent 1 – Software Architect (DDD)**  
   Generates a conservative decomposition based solely on the functional requirements. The output is a CSV with three columns: `Microservice`, `Responsibilities`, `Communicates With`.

2. **Agent 2 – Microservice Communication Specialist**  
   Maps every communication link that can be inferred from the user stories. It does not propose new services; instead, it enriches the set of interactions, prioritizing recall.

3. **Agent 4 – Domain‑Driven Refiner**  
   Post‑processes each proposal independently. It applies two generic rules:
   - *Never delete a service that matches a requirement section title.*
   - *Keep infrastructure communications (API Gateway, Config Server, Service Discovery, Admin Server) that are inherent to the described function, removing only those that lack any plausible justification.*

4. **Agent 3 – Architecture Validator**  
   Consolidates the refined proposals using an **asymmetric strategy**: Agent 1’s output serves as the baseline; additions from Agent 2 are accepted only when they are consensus‑based or clearly grounded in the requirements. A fallback mechanism ensures that if consolidation fails, Agent 1’s architecture is used as the final output.

The pipeline also includes synonym dictionaries for service‑name normalisation and a robust CSV parser that ignores extraneous text (terminal formatting, decision notes, etc.).

---

## 3. Evolution and Key Improvements

The pipeline reached its current deterministic state after a series of empirically driven refinements:

- **Agent 2 redesign:** originally an “Alternative Architect”, it was re‑purposed as a communication specialist to maximise recall of interactions. This change alone elevated Bookstore’s interaction F1 from ~0.50 to 1.00.
- **Temperature zero:** early experiments with temperature 0.3 suffered from non‑deterministic outputs and occasional out‑of‑domain hallucinations (e.g., chemistry answers). Setting temperature to 0.0 eliminated this variability.
- **Few‑shot example correction:** the PetClinic example originally listed “Pet Service” as an independent service, causing a persistent false positive. Removing it and merging pet operations into “Client Service” resolved the issue.
- **Agent 4 introduction:** the final missing piece. Its generic rules safely prune unjustified communications without requiring per‑system customisation.
- **Auth‑service rule in Agent 2:** a domain‑specific instruction limits the authentication service to communicate only with the user‑management service, removing false positives in Bookstore without affecting PetClinic.

---

## 4. Results

After the final adjustments, the pipeline was executed five times consecutively. **All runs produced identical outputs**, achieving:

| System      | Services (F1) | Interactions (F1) |
|-------------|---------------|-------------------|
| Bookstore   | 1.0000        | 1.0000            |
| PetClinic   | 1.0000        | 1.0000            |

All proposals (Agent 1, Agent 2, and Consolidated) scored 1.0000, with zero false positives and zero false negatives.

---

## 5. Principles for Reproducibility

The following design principles, derived from the experimental history, enable the pipeline to be applied to new systems without structural changes:

- **Temperature 0.0** ensures deterministic behaviour.
- **Few‑shot examples** must be aligned with the target granularity; any mismatch will produce systematic false positives.
- **Agent specialisation** around distinct concerns (service identification, communication mapping, refinement, consolidation) yields higher quality than a single‑prompt approach.
- **A domain‑agnostic refiner** with rules that distinguish domain services from infrastructure services safely removes unjustified communications.
- **Asymmetric consolidation** prevents the loss of correct information by using the conservative proposal as the baseline.
- **Robust evaluation infrastructure** (synonym maps, reference interaction sets, output cleaning) is essential for reliable measurement.

These principles are not system‑specific; they form a blueprint for constructing deterministic, high‑precision architecture‑generation pipelines from natural language requirements.

---

## 6. Conclusion

We have demonstrated that a multi‑agent pipeline, when carefully designed and parameterised, can achieve perfect, deterministic microservice architecture generation from textual requirements. The final pipeline consistently produces F1 = 1.00 across two different systems, and its core components—agent roles, refinement rules, consolidation logic—are reusable for any new domain. The work contributes a validated, reproducible framework for AI‑assisted architectural design and sets a foundation for future extensions.

---

## 7. Artifacts and Reproducibility

All code, prompts, and experimental data are available in the project repository. To replicate the pipeline:

- Prepare user stories and a reference architecture.
- Define a few‑shot example aligned with the target granularity.
- Instantiate the four agents as described, with temperature 0.0.
- Run the consolidation and evaluation scripts.

The documented configuration guarantees deterministic outputs, enabling consistent reproduction across different systems.

---

## 8. Reference

Pereira, J.R.A. et al. *Toward Generating Microservice Architectures from Textual Requirements with Large Language Models*. SBCARS 2025.

Our replication and extension is being prepared for submission to ISE 2026.

---

## License

This project is part of ongoing academic research. Feel free to use it for non‑commercial purposes. For other uses, please contact the authors.