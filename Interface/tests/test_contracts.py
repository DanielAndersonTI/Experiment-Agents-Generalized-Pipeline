"""Mock API contract tests for the VIRTUS interface."""

import json
import threading
import unittest
from unittest.mock import patch
from urllib.request import Request, urlopen

from Interface.server import create_server
from Interface.utils.parsers import parse_name_map, parse_reference_interactions, parse_reference_services


SYSTEM = {
	"system_name": "Contract Demo",
	"architecture_target": "Microservices",
	"requirements": "Manage records.",
	"reference_services": "Record Service",
	"reference_interactions": "Record -> Audit",
	"name_normalization_map": "Record=Record Service",
}

MOCK_RUN = {
	"ok": True,
	"run_id": "mock-run",
	"metrics": {
		"proposta_a": {"precision": 0.9, "recall": 0.8, "f1_score": 0.85},
		"proposta_b": {"precision": 0.8, "recall": 0.9, "f1_score": 0.85},
		"consolidada": {"precision": 0.88, "recall": 0.86, "f1_score": 0.87},
		"proposta_a_inter": {"precision": 0.8, "recall": 0.7, "f1_score": 0.75},
		"proposta_b_inter": {"precision": 0.7, "recall": 0.8, "f1_score": 0.75},
		"consolidada_inter": {"precision": 0.82, "recall": 0.81, "f1_score": 0.815},
	},
	"results": {
		"proposta_a": "Microservice,Responsibilities,Communicates With\nA,Manage A,B",
		"proposta_b": "Microservice,Responsibilities,Communicates With\nB,Manage B,A",
		"consolidada": "Microservice,Responsibilities,Communicates With\nA,Manage A,B",
	},
}


class ContractTests(unittest.TestCase):
	@classmethod
	def setUpClass(cls):
		cls.server = create_server(port=0)
		cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
		cls.thread.start()
		cls.base = f"http://127.0.0.1:{cls.server.server_port}"

	@classmethod
	def tearDownClass(cls):
		cls.server.shutdown()
		cls.server.server_close()

	def run_payload(self, payload):
		request = Request(self.base + "/api/pipeline/run", data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"})
		return urlopen(request)

	def test_success_contract(self):
		with patch("Interface.server.run_real_pipeline", return_value=MOCK_RUN):
			result = json.loads(self.run_payload({"systems": [SYSTEM]}).read())
		for key in ("ok", "run_id", "generated_at", "systems", "proposals", "service_metrics", "interaction_metrics", "best_results", "report_available"):
			self.assertIn(key, result)
		self.assertTrue(result["ok"])
		self.assertEqual(len(result["proposals"]), 1)
		self.assertIn("Microservice,Responsibilities,Communicates With", result["proposals"][0]["agent_a"])

	def test_report_contains_complete_execution_sections(self):
		with patch("Interface.server.run_real_pipeline", return_value=MOCK_RUN):
			self.run_payload({"systems": [SYSTEM]}).read()
		report = urlopen(self.base + "/api/report/pdf").read()
		for marker in (
				b"DAVINCI Architect",
				b"Multi-Agent Software Architect",
			b"Run ID / Test Number:",
			b"Generated:",
			b"SECTION 1 - INPUTS PROVIDED",
			b"SECTION 2 - AGENT PROPOSALS",
			b"Agent A \\(Software Architect\\)",
			b"Agent B \\(Communication Specialist\\)",
			b"SECTION 3 - FINAL ARCHITECTURE RECOMMENDED BY THE PIPELINE",
			b"Final Architecture Recommended by the Pipeline",
			b"Consolidated Architecture CSV",
			b"SECTION 4 - EVALUATION METRICS",
			b"Evaluation Metrics",
			b"SECTION 5 - BEST RESULTS",
			b"Developed by Daniel Anderson",
			b"In partnership with Virtus UFCG",
			b"Contact: daniel.silva@virtus-cc.ufcg.edu.br",
			b"2026 DAVINCI Architect. All rights reserved.",
		):
			self.assertIn(marker, report)

	def test_parsers_accept_interface_formats(self):
		self.assertEqual(parse_reference_services("A\nB, C"), ["A", "B", "C"])
		self.assertEqual(parse_reference_interactions("A <-> B; C -> D; E, F"), {("A", "B"), ("C", "D"), ("E", "F")})
		self.assertEqual(parse_name_map("alias -> Canonical; other, Main"), {"alias": "Canonical", "other": "Main"})
