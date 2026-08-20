# Input Data Guide

This document explains the role of each input required by the VIRTUS Microservice Architecture Workbench and how to collect it.

---

## Why These Inputs Are Used

### System Requirements

The textual requirements describe what the system must do. They are the **only input used during architecture generation**. The LLM agents read the requirements to:

- identify distinct business capabilities;
- group related responsibilities into cohesive services;
- infer necessary communications between services.

Requirements must be as complete and precise as possible, because they are the sole source of evidence for the generated architecture.

### Reference Services

The reference services list represents the expected set of microservices for the system. It is **not used during generation**. It is used only after generation to evaluate how well the proposed services match the expected decomposition.

Evaluation metrics such as Precision, Recall, and F1-score compare the generated service names with this reference list.

### Reference Interactions

The reference interactions describe which pairs of services are expected to communicate. Like the reference services, they are used **only for evaluation**. Each interaction is an unordered pair of service names, e.g., `order-service <-> payment-service`.

They allow the calculation of interaction-level metrics and help determine whether the pipeline identified the necessary dependencies.

### Name Normalization Map

Different agents may generate slightly different service names for the same concept (e.g., `api-gateway`, `gateway`, `apigateway`). The normalization map maps these variations to a canonical name.

This map is used **only during evaluation** to avoid penalizing valid services or interactions that use alternative names. It does not influence the generation process.

---

## How to Collect These Inputs

### System Requirements

Gather requirements from:

- product owners;
- domain experts;
- user stories;
- functional specification documents;
- existing documentation or legacy system analysis.

Write them as a numbered list of functional capabilities, including any explicit technical requirements (e.g., service discovery, centralized configuration, API gateway, monitoring) if they are part of the system specification.

Organize the requirements as clearly as possible, because the quality of the generated architecture depends heavily on the completeness and precision of this text.

### Reference Services

To build the reference service list:

1. Identify the major business capabilities of the system.
2. Apply Domain-Driven Design (DDD) or bounded-context analysis to group related responsibilities.
3. Name each resulting service using a clear, consistent convention.
4. Use this list as the ground truth for service evaluation.

If you do not have a predefined target architecture, you can derive it from the same business capabilities used during analysis.

### Reference Interactions

To build the reference interaction set:

1. Analyze the business workflows and processes described in the requirements.
2. Determine which services must exchange data or trigger actions to complete those workflows.
3. Record each required pair as an unordered interaction (e.g., `service-a <-> service-b`).
4. Include only interactions that are clearly necessary; avoid adding speculative links.

### Name Normalization Map

The normalization map can be built by anticipating common naming variations:

- synonyms (e.g., `customer` → `customer-service`);
- abbreviation or concatenation (e.g., `apigateway` → `api-gateway`);
- plural/singular differences;
- naming choices made by different architects.

Map each alternative to the canonical service name used in the reference list. This prevents valid services or interactions from being penalized only because of superficial differences in writing.

---

## Summary

| Input | Used for generation? | Used for evaluation? |
|-------|----------------------|----------------------|
| System Requirements | Yes | No |
| Reference Services | No | Yes |
| Reference Interactions | No | Yes |
| Name Normalization Map | No | Yes |

The VIRTUS Workbench uses only the requirements to generate candidate architectures, while the reference data and normalization map are used exclusively to compute the evaluation metrics shown in the results.