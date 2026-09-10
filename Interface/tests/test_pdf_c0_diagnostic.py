"""Diagnostic test for the C0 PDF report path."""

import json
import threading
import unittest
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from unittest.mock import patch
from urllib.request import urlopen

import Interface.server as server_module
from Interface.server import build_pdf_report, create_server


class C0PdfDiagnosticTests(unittest.TestCase):
    def c0_run(self):
        return {
            "run_id": "c0-diagnostic",
            "generated_at": "2026-09-03 00:00:00",
            "systems": [{"system_name": "7ep"}],
            "proposals": [{
                "system": "7ep",
                "agent_a": "Microservice,Responsibilities,Communicates With\nCatalog Service,Manage catalog,",
                "agent_b": None,
                "consolidated": "Microservice,Responsibilities,Communicates With\nCatalog Service,Manage catalog,",
                "specification": "",
            }],
            "service_metrics": [],
            "interaction_metrics": [],
            "best_results": [],
        }

    def test_c0_report_and_endpoint(self):
        run = self.c0_run()
        try:
            pdf = build_pdf_report(run)
        except Exception:
            print("\nBUILD_PDF_REPORT FAILED - traceback:")
            raise

        self.assertTrue(pdf.startswith(b"%PDF-"))
        self.assertGreater(len(pdf), 1000)
        print(f"build_pdf_report: OK ({len(pdf)} bytes)")

        with patch.object(server_module, "LATEST_RUN", run):
            http_server = create_server(port=0)
            thread = threading.Thread(target=http_server.handle_request)
            thread.start()
            try:
                response = urlopen(f"http://127.0.0.1:{http_server.server_port}/api/report/pdf")
                body = response.read()
                print(json.dumps({
                    "status": response.status,
                    "content_type": response.headers.get("Content-Type"),
                    "content_length": len(body),
                    "pdf_header": body[:5].decode("ascii"),
                }, indent=2))
                self.assertEqual(response.status, 200)
                self.assertEqual(response.headers.get_content_type(), "application/pdf")
                self.assertTrue(body.startswith(b"%PDF-"))
            except Exception:
                print("\nPDF ENDPOINT FAILED - server traceback may be above:")
                raise
            finally:
                thread.join(timeout=5)
                http_server.server_close()


if __name__ == "__main__":
    unittest.main(verbosity=2)