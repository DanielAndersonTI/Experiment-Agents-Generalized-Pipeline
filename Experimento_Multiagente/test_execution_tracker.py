import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from Experimento_Multiagente import execution_tracker as tracker_module
from crewai.events import LLMCallCompletedEvent, LLMCallStartedEvent
from Experimento_Multiagente import main_fewshot


class ExecutionTrackerTests(unittest.TestCase):
    def test_records_real_usage_and_missing_usage_without_estimation(self):
        tracker = tracker_module.ExecutionTracker("test-execution")
        tracker.start()
        tracker_module._on_started(
            None,
            LLMCallStartedEvent(call_id="call-1", model="gemini/test", agent_role="Software Architect"),
        )
        tracker_module._on_completed(
            None,
            LLMCallCompletedEvent(
                call_id="call-1", model="gemini/test", agent_role="Software Architect",
                response="ok", call_type="llm_call", messages=[],
                usage={"prompt_tokens": 3, "completion_tokens": 2, "total_tokens": 5},
            ),
        )
        tracker_module._on_started(
            None,
            LLMCallStartedEvent(call_id="call-2", model="openai/test", agent_role="Communication Specialist"),
        )
        tracker_module._on_completed(
            None,
            LLMCallCompletedEvent(
                call_id="call-2", model="openai/test", agent_role="Communication Specialist",
                response="ok", call_type="llm_call", messages=[], usage=None,
            ),
        )
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            tracker.finish(output)
            metadata = json.loads((output / "execution_metadata.json").read_text(encoding="utf-8"))

        self.assertEqual(metadata["llm_usage"]["total_calls"], 2)
        self.assertEqual(metadata["llm_usage"]["total_tokens"], 5)
        self.assertEqual(metadata["calls"][0]["prompt_tokens"], 3)
        self.assertIsNone(metadata["calls"][1]["total_tokens"])
        self.assertEqual(metadata["agents"]["agent_1"]["calls"], 1)
        self.assertEqual(metadata["agents"]["agent_2"]["calls"], 1)
        self.assertGreaterEqual(metadata["execution"]["duration_ms"], 0)

    def test_c3_uses_refined_proposal_without_agents_2_or_3(self):
        original = "Microservice,Responsibilities,Communicates With\nCatalog,Manage books,Reader;Loan\nReader,Manage readers,Loan"
        refined = "Microservice,Responsibilities,Communicates With\nCatalog,Manage books,Loan\nReader,Manage readers,Loan"
        crews = []

        class FakeCrew:
            def __init__(self, agents, tasks, verbose):
                crews.append(agents[0])

        with tempfile.TemporaryDirectory() as directory:
            yaml_output = "services:\n  - Catalog\n  - Reader\n"
            with patch.object(main_fewshot, "RESULTS_ROOT", Path(directory)), \
                 patch.object(main_fewshot, "criar_agente1", return_value="agent1"), \
                 patch.object(main_fewshot, "criar_agente4", return_value="agent4"), \
                 patch.object(main_fewshot, "criar_task_arquitetura", return_value="task1"), \
                 patch.object(main_fewshot, "criar_task_refinamento", return_value="task4"), \
                 patch.object(main_fewshot, "Crew", FakeCrew), \
                 patch.object(main_fewshot, "silent_kickoff", side_effect=[original, refined]), \
                 patch.object(main_fewshot, "gerar_especificacao_yaml", return_value=yaml_output):
                results, metrics = main_fewshot._executar_experimento_c3(
                    object(),
                    "7ep",
                    {
                        "name": "7ep",
                        "requirements": "requirements",
                        "reference_services": ["catalog", "reader"],
                        "interaction_reference": set(),
                        "tracer_run_id": "test-c3",
                    },
                    "c3-test",
                    "example",
                )

            run_dir = Path(directory) / "7ep" / "result_generalized_fewshot" / "run_c3-test"
            self.assertEqual(crews, ["agent1", "agent4"])
            self.assertEqual(results["proposta_a"], refined)
            self.assertEqual(results["consolidada"], refined)
            self.assertEqual(metrics.keys(), {"proposta_a", "proposta_a_inter"})
            self.assertEqual(
                (run_dir / "proposta_a.csv").read_text(encoding="utf-8"),
                (run_dir / "consolidada.csv").read_text(encoding="utf-8"),
            )
            self.assertEqual(
                (run_dir / "especificacao_arquitetural.yaml").read_text(encoding="utf-8"),
                yaml_output,
            )


if __name__ == "__main__":
    unittest.main()
