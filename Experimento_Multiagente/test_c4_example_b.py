"""C4 wiring tests: independent proposals, separate few-shots, agent labels.

These tests run fully offline: the LLM, the agents, the crews and the kickoffs
are replaced by fakes, so only the orchestration of `_executar_experimento_c4`
(including the `track_execution` wrapper, the Agent 2.1 label and the few-shot
provenance file) is exercised.
"""

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from Experimento_Multiagente import main_fewshot

# main_fewshot imports the tracker as a top-level module (it inserts its own
# directory in sys.path), so the ContextVar must be read from that same module
# instance instead of importing execution_tracker again.
tracker_module = sys.modules[main_fewshot.set_agent_label.__module__]

PROPOSAL = (
    "Microservice,Responsibilities,Communicates With\n"
    "Alpha Service,Handle alpha work,Beta Service\n"
    "Beta Service,Handle beta work,Alpha Service"
)
REFINED = (
    "Microservice,Responsibilities,Communicates With\n"
    "Alpha Service,Handle alpha work with extra detail,Beta Service\n"
    "Beta Service,Handle beta work with extra detail,Alpha Service"
)
CONSOLIDATED = (
    "Microservice,Responsibilities,Communicates With\n"
    "Alpha Service,Handle alpha work consolidated,Beta Service\n"
    "Beta Service,Handle beta work consolidated,Alpha Service"
)
YAML_OUTPUT = "services:\n  - Alpha Service\n  - Beta Service\n"


class FakeCrew:
    """Minimal Crew stand-in that records the agents of each created crew."""

    crews = []

    def __init__(self, agents, tasks, verbose):
        FakeCrew.crews.append(self)
        self.agents = agents
        self.tasks = tasks
        self.verbose = verbose


class C4ExampleBTests(unittest.TestCase):
    def setUp(self):
        FakeCrew.crews = []
        self.registros = []
        # Agent 2 (specialist) must stay untouched by C4, so the factory is a
        # real mock kept alive after the patch contexts are stopped.
        self.agente2_factory = Mock(name="criar_agente2")

    def _fake_kickoff(self, crew, inputs):
        """Capture each proposal kickoff and answer the different crew stages."""
        if "example" in inputs:
            self.registros.append({
                "rotulo": tracker_module._CURRENT_AGENT_LABEL.get(),
                "example": inputs["example"],
                "requirements": inputs["requirements"],
            })
        if "original_architecture" in inputs:
            return REFINED
        if "architecture_a" in inputs:
            return CONSOLIDATED
        return PROPOSAL

    def _config(self):
        return {
            "name": "7ep",
            "requirements": "Library requirements.",
            "reference_services": ["alpha", "beta"],
            "interaction_reference": set(),
            "tracer_run_id": "test-c4",
        }

    def _patches(self, directory):
        return [
            patch.object(main_fewshot, "RESULTS_ROOT", Path(directory)),
            patch.object(main_fewshot, "DEBUG_RAW_OUTPUT", False),
            patch.object(main_fewshot, "criar_agente1", return_value="agent1"),
            patch.object(main_fewshot, "criar_agente2", new=self.agente2_factory),
            patch.object(main_fewshot, "criar_agente2_1", return_value="agent2_1"),
            patch.object(main_fewshot, "criar_agente3", return_value="agent3"),
            patch.object(main_fewshot, "criar_agente4", return_value="agent4"),
            patch.object(main_fewshot, "criar_task_arquitetura", return_value="task1"),
            patch.object(main_fewshot, "criar_task_arquitetura_2_1", return_value="task2"),
            patch.object(main_fewshot, "criar_task_consolidacao", return_value="task3"),
            patch.object(main_fewshot, "criar_task_refinamento", return_value="task4"),
            patch.object(main_fewshot, "Crew", FakeCrew),
            patch.object(main_fewshot, "silent_kickoff", side_effect=self._fake_kickoff),
            patch.object(main_fewshot, "gerar_especificacao_yaml", return_value=YAML_OUTPUT),
        ]

    def _run_c4(self, **kwargs):
        with tempfile.TemporaryDirectory() as temporary_dir:
            patches = self._patches(temporary_dir)
            for context in patches:
                context.start()
            try:
                example = kwargs.pop("example")
                results, metrics = main_fewshot._executar_experimento_c4(
                    object(), "7ep", self._config(), "c4-test", example, **kwargs
                )
                run_dir = (
                    Path(temporary_dir) / "7ep" / "result_generalized_fewshot" / "run_c4-test"
                )
                provenance = json.loads(
                    (run_dir / "fewshot_c4.json").read_text(encoding="utf-8")
                )
                saved = {
                    "proposta_a": (run_dir / "proposta_a.csv").read_text(encoding="utf-8"),
                    "proposta_b": (run_dir / "proposta_b.csv").read_text(encoding="utf-8"),
                    "consolidada": (run_dir / "consolidada.csv").read_text(encoding="utf-8"),
                    "yaml": (run_dir / "especificacao_arquitetural.yaml").read_text(
                        encoding="utf-8"
                    ),
                }
            finally:
                for context in reversed(patches):
                    context.stop()
        return results, metrics, provenance, saved

    def test_second_proposal_uses_its_own_fewshot_and_the_agent_2_1_label(self):
        results, metrics, provenance, saved = self._run_c4(
            example=main_fewshot.EXAMPLE_GENERIC
        )

        self.assertEqual(len(self.registros), 2)
        self.assertEqual(self.registros[0]["example"], main_fewshot.EXAMPLE_GENERIC)
        self.assertEqual(self.registros[0]["requirements"], "Library requirements.")
        self.assertIsNone(self.registros[0]["rotulo"])
        self.assertEqual(self.registros[1]["example"], main_fewshot.EXAMPLE_ARCHITECT_B)
        self.assertEqual(self.registros[1]["rotulo"], "agent_2_1")
        self.assertNotEqual(self.registros[0]["example"], self.registros[1]["example"])

        # C4 must call Agent 2.1 instead of the Agent 2 specialist.
        self.agente2_factory.assert_not_called()
        self.assertEqual(FakeCrew.crews[0].agents, ["agent1"])
        self.assertEqual(FakeCrew.crews[2].agents, ["agent2_1"])

        self.assertFalse(provenance["mesmo_fewshot"])
        self.assertEqual(provenance["proposta_a_agente"], "agent_1")
        self.assertEqual(provenance["proposta_b_agente"], "agent_2_1")
        self.assertNotEqual(
            provenance["proposta_a_fewshot_sha256"], provenance["proposta_b_fewshot_sha256"]
        )
        self.assertIn("Alpha Service", saved["proposta_a"])
        self.assertIn("Alpha Service", saved["proposta_b"])
        self.assertIn("consolidated", saved["consolidada"])
        self.assertEqual(saved["yaml"], YAML_OUTPUT)
        self.assertEqual(results["especificacao_yaml"], YAML_OUTPUT)
        self.assertEqual(
            set(metrics),
            {"proposta_a", "proposta_b", "consolidada",
             "proposta_a_inter", "proposta_b_inter", "consolidada_inter"},
        )
        self.assertIsNotNone(metrics["proposta_a"])
        self.assertIsNotNone(metrics["proposta_b"])

    def test_explicit_example_b_reuses_the_same_fewshot(self):
        _, _, provenance, _ = self._run_c4(
            example=main_fewshot.EXAMPLE_GENERIC,
            example_b=main_fewshot.EXAMPLE_GENERIC,
        )

        self.assertEqual(self.registros[0]["example"], self.registros[1]["example"])
        self.assertTrue(provenance["mesmo_fewshot"])
        self.assertEqual(
            provenance["proposta_a_fewshot_sha256"], provenance["proposta_b_fewshot_sha256"]
        )


class ExecutarPipelineC4Tests(unittest.TestCase):
    def test_public_entrypoint_forwards_both_fewshots(self):
        executor = Mock(return_value=({"proposta_a": None}, {}))
        with patch.object(main_fewshot, "criar_llm", return_value="llm"), \
             patch.object(main_fewshot, "_executar_experimento_c4", executor):
            main_fewshot.executar_pipeline_c4(
                "7ep", "Requirements.", ["alpha"], set(),
                example="EXAMPLE_A", example_b="EXAMPLE_B", tracer_run_id="tracer-1",
            )

        args = executor.call_args.args
        self.assertEqual(args[0], "llm")
        self.assertEqual(args[1], "7ep")
        self.assertEqual(args[2]["requirements"], "Requirements.")
        self.assertEqual(args[2]["tracer_run_id"], "tracer-1")
        self.assertEqual(args[4], "EXAMPLE_A")
        self.assertEqual(args[5], "EXAMPLE_B")


class ExampleConstantsTests(unittest.TestCase):
    def test_example_architect_b_is_a_distinct_well_formed_csv(self):
        lines = [line for line in main_fewshot.EXAMPLE_ARCHITECT_B.strip().splitlines() if line]
        self.assertEqual(len(lines), 5)
        for line in lines:
            columns = line.split(",")
            self.assertEqual(len(columns), 3)
            self.assertTrue(columns[0].strip())
            self.assertTrue(columns[1].strip())
        self.assertNotIn("|", main_fewshot.EXAMPLE_ARCHITECT_B)
        self.assertNotEqual(
            main_fewshot.EXAMPLE_ARCHITECT_B.strip(), main_fewshot.EXAMPLE_GENERIC.strip()
        )


if __name__ == "__main__":
    unittest.main()
