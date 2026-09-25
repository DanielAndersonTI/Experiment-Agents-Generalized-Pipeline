"""Configuration dispatch tests for the interface pipeline adapter."""

import unittest
from unittest.mock import patch

from Interface.utils import pipeline_runner
from Interface.utils.parsers import parse_reference_interactions

SYSTEM = {
    "system_name": "Dispatch Demo",
    "requirements": "Manage records.",
    "reference_services": "Record Service",
    "reference_interactions": "Record -> Audit",
}

METRICS = {"proposta_a": {"f1_score": 0.9}, "proposta_b": {"f1_score": 0.8}}


class PipelineModeDispatchTests(unittest.TestCase):
    def call_mode(self, mode):
        calls = {}

        def fake_entrypoint(system_name, requirements, reference_services,
                            interaction_reference, tracer_run_id=None):
            calls.update({
                "system_name": system_name,
                "requirements": requirements,
                "reference_services": reference_services,
                "interaction_reference": interaction_reference,
                "tracer_run_id": tracer_run_id,
            })
            return {"proposta_a": "csv-a", "proposta_b": "csv-b", "consolidada": "csv-c"}, METRICS

        entrypoints = {
            "c0": "executar_pipeline_c0",
            "c1": "executar_pipeline",
            "c2": "executar_pipeline_c2",
            "c3": "executar_pipeline_c3",
            "c4": "executar_pipeline_c4",
        }
        attribute = entrypoints[mode]
        with patch.object(pipeline_runner, attribute, new=fake_entrypoint):
            result = pipeline_runner.run_real_pipeline(
                {**SYSTEM, "mode": mode}, tracer_run_id="tracer-1"
            )
        return result, calls

    def test_each_mode_dispatches_to_its_own_entrypoint(self):
        for mode in ("c0", "c1", "c2", "c3", "c4"):
            with self.subTest(mode=mode):
                result, calls = self.call_mode(mode)
                self.assertTrue(result["ok"])
                self.assertEqual(result["metrics"], METRICS)
                self.assertEqual(calls["system_name"], "Dispatch Demo")
                self.assertEqual(calls["reference_services"], ["Record Service"])
                # The adapter must forward exactly what the parsers produced
                # (unordered pairs are normalized by the parser).
                self.assertEqual(
                    calls["interaction_reference"],
                    parse_reference_interactions(SYSTEM["reference_interactions"]),
                )
                self.assertEqual(calls["tracer_run_id"], "tracer-1")

    def test_missing_mode_defaults_to_c0(self):
        result, calls = self.call_mode("c0")
        self.assertTrue(result["ok"])
        self.assertEqual(calls["system_name"], "Dispatch Demo")


if __name__ == "__main__":
    unittest.main()
