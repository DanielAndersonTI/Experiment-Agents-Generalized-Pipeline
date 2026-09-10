Consolidated Report of C0–C3 Experiments
Overview
The experiments aimed to isolate, through ablation, the contribution of each DAVINCI Architect pipeline component in generating microservice architectures from textual requirements. Three runs were executed for each configuration (C0, C1, C2, C3), always using the Gemini model, few-shot prompting, temperature 0.0, and the same eight systems. The main metrics were Precision, Recall, and F1-score for services and interactions, complemented by token cost and duration.

The results show that service identification is robust across all configurations, with F1 often equal to 1.0000. The recurring exceptions are Cargo-Tracker and TNTConcept, whose requirements omit implicit capabilities that even the full pipeline cannot consistently recover. In contrast, interaction recovery is the main differentiator between configurations and reveals the value of specialized agents.

C0 — Single Agent
C0 used only Agent 1 (DDD Architect), without refinement, specialized communication, or consolidation. Service results were very good: F1 1.0000 in six systems, 0.9091 in Cargo-Tracker, and 0.9231 in TNTConcept. For interactions, however, performance was unstable and sometimes disastrous. For example, Cargo-Tracker alternated between F1 0.0000 and 0.8421 across the three runs. AcmeAir varied from 0.6154 to 1.0000. This demonstrates that a single agent is insufficient to handle implicit dependencies in complex domains.

The total cost of C0 was drastically lower: about 47k to 65k tokens per run, compared to over 400k in C1. This energy efficiency, however, comes at the cost of greater variability and lower interaction coverage.

C1 — Full Pipeline
C1 (Agents 1, 2, 4, 3, and 5) presented the best overall results, especially for interactions. In systems such as 7ep, AcmeAir, Jokul, PetClinic, and JPetStore, interaction F1 remained consistently above 0.90, often 1.0000. In problematic systems, Cargo-Tracker reached 0.8421 in two of three runs, and TNTConcept ranged from 0.7761 to 0.8000. Metric-based consolidation was decisive in several cases: for example, in 7ep in the second run, Agent 3 combined A's service base with B's interactions and raised F1 from 0.9524 to 1.0000.

C1 cost was the highest among the configurations, ranging from 412k to 501k tokens per run. Agent 2 (Communication Specialist) was the largest consumer, accounting for about 46–58% of the total. Even so, the quality gain in interactions justifies the computational investment in most scenarios.

C2 — Without Refinement
C2 removed Agent 4, keeping Agents 1, 2, 3, and 5. Services remained stable, and interactions generally did not suffer significant degradation compared to C1. In some cases, the consolidated result even outperformed C1: DayTrader7 had F1 0.9565 in C2 Test 2, against 0.9091 in C1. Cargo-Tracker maintained 0.8421 in two runs and 0.7273 in another (when consolidation failed by combining incorrectly).

These results suggest that the refiner plays a marginal role when Agents 1 and 2 already produce reasonably clean proposals. The cost of C2 ranged from 323k to 424k tokens, that is, lower than C1, without relevant quality loss. The main observed weakness was parsing errors in YAML when Agent 3 generated noisy output, but this is a post-processing robustness problem, not a consequence of removing the refiner itself.

C3 — Without Communication Specialist
C3 removed Agent 2 and, as a consequence, also did not use Agent 3 (since there was no longer more than one proposal to consolidate). The flow was Agent 1 → Agent 4 → deterministic YAML. Services remained robust, except for an over-decomposition episode in Cargo-Tracker in Test 2, when Agent 1 created extra services such as Location Management Service and Voyage Management Service, reducing service F1 to 0.7692.

For interactions, C3 was clearly inferior to C1 and C2. Cargo-Tracker scored zero interactions in Test 1, AcmeAir dropped to 0.5714, PetClinic to 0.6667, and JPetStore to 0.4286 in Test 2. Only Jokul and DayTrader7 maintained performance close to C1. This confirms that the Communication Specialist is essential to capture functional dependencies that are not explicit in the requirements.

The cost of C3 ranged from 108k to 134k tokens, approximately double C0, but much lower than C1. However, the cost-benefit ratio is unfavorable: it spends more than the single agent, but interaction quality remains far below the full pipeline.

Comparison and Implications
The analysis of the four configurations allows answering the research questions clearly.

RQ1 — Does the multi-agent pipeline improve service and interaction identification compared to a single agent?
For services, the improvement is small because even C0 already gets most correct. For interactions, the improvement is substantial: C1 and C2 consistently outperform C0, especially in Cargo-Tracker, TNTConcept, AcmeAir, and JPetStore. The difference is most evident when the single agent fails completely (F1 0.0000) and the full pipeline recovers F1 0.8421.

RQ2 — Which components contribute most to quality?
The Communication Specialist (Agent 2) is the component with the greatest impact on interaction recovery. Its removal (C3) causes significant drops. The Consolidator (Agent 3) is also critical: it selects the best proposal and, when possible, combines complementary interactions. The Refiner (Agent 4) plays a secondary role; its removal (C2) does not significantly harm quality and even reduces cost.

RQ3 — What is the trade-off between quality, stability, and cost?
C1 offers the best quality and stability, but at the highest cost. C0 is the cheapest and least stable. C2 emerges as a promising intermediate configuration: quality close to C1 with lower cost. C3 has the worst cost-benefit, since it does not deliver C1/C2 quality and still costs double C0.

Preliminary Conclusions
The C0–C3 experiments show that it is not the number of agents that matters, but proper specialization and orchestration. The Communication Specialist and the Consolidator are the components that really add value. The Refiner, although useful in theory, did not show clear benefit in the tested systems and may be dispensable in simplified versions of the pipeline.

System robustness depends strongly on requirement clarity. Systems with well-structured requirements (Jokul, PetClinic, DayTrader7) achieve high quality even with simpler configurations. Systems with implicit capabilities (Cargo-Tracker, TNTConcept) require the full pipeline to mitigate gaps.

## Agent A (DDD Architect) Contribution

Agent A, also called the DDD Architect, is the foundation of all configurations and is primarily responsible for identifying services from the requirements. In isolation (C0), it already achieves a service F1 of 1.0000 in six of the eight systems and an interaction F1 above 0.90 in well-structured systems such as Jokul, DayTrader7, and 7ep. However, in domains with implicit dependencies, its interaction performance fluctuates sharply: in Cargo-Tracker, for example, it scored zero interactions in two of the three C0 executions (F1 0.0000), while in the full pipeline (C1) it achieved 0.8421 in most executions. This shows that Agent A provides a conservative and precise decomposition, but it is not sufficient to capture all necessary communications when the requirements are not fully explicit. The addition of the Communication Specialist (Agent 2) and the Consolidator (Agent 3) is what allows the pipeline to mitigate these gaps, raising interaction F1 by up to 84 percentage points in extreme cases such as Cargo-Tracker.

## Quantified Impact of Configuration Changes

| Comparison | Interaction F1 Effect | Service F1 Effect | Cost (tokens) |
|---|---|---|---|
| C0 → C1 (add Agents 2,3,4) | Average gain of ~20 percentage points; in Cargo-Tracker, from 0.0000 to 0.8421; in AcmeAir, from 0.6154 to 1.0000 | No relevant change (remains ~1.00) | Increase of ~6–8× (from ~50k to ~450k) |
| C1 → C2 (remove Refiner) | Nearly neutral; occasional small variations (e.g., DayTrader7 rose from 0.9091 to 0.9565 in one run) | Neutral | Reduction of ~20–25% (from ~412k–501k to ~323k–424k) |
| C1 → C3 (remove Communication Specialist) | Severe drop in problematic systems: Cargo-Tracker fell from 0.8421 to 0.0000 in one run; JPetStore fell from 0.9412 to 0.4286; AcmeAir fell from 1.0000 to 0.5714 | Occasionally worsens (Cargo-Tracker dropped to 0.7692 in one run) | Reduction to ~108k–134k (about 1/4 of C1) |

## Ideal Configuration Summary

For the **best balance between quality and cost**, configuration **C2 (without the Refiner)** is the most advantageous: it maintains interaction F1 close to C1 while reducing token cost by approximately 20–25%. If the goal is **absolute minimum cost**, C0 is unbeatable, but it is only acceptable for systems with very well-defined requirements, since interaction loss can be severe in complex domains. C1 remains the choice when **robustness and interaction coverage are priorities**, despite the higher computational expenditure.

