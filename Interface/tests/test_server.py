"""HTTP route tests for the VIRTUS interface."""

import json
import threading
import unittest
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import Interface.server as server_module
from Interface.server import create_server


class ServerRouteTests(unittest.TestCase):
	@classmethod
	def setUpClass(cls):
		server_module.LATEST_RUN = None
		cls.server = create_server(port=0)
		cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
		cls.thread.start()
		cls.base = f"http://127.0.0.1:{cls.server.server_port}"

	@classmethod
	def tearDownClass(cls):
		cls.server.shutdown()
		cls.server.server_close()

	def request_json(self, path, payload):
		request = Request(self.base + path, data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"})
		return urlopen(request)

	def test_home_page_and_system_creation(self):
		home = urlopen(self.base + "/").read()
		self.assertIn(b"/img/Logo-DAVINCI.png", home)
		self.assertIn(b"og:image", home)
		self.assertEqual(urlopen(self.base + "/img/Logo-DAVINCI.png").headers.get_content_type(), "image/png")
		response = self.request_json("/api/systems", {"current_count": 0})
		self.assertTrue(json.loads(response.read())["ok"])

	def test_system_limit_is_rejected(self):
		with self.assertRaises(HTTPError) as context:
			self.request_json("/api/systems", {"current_count": 10})
		self.assertEqual(context.exception.code, 400)

	def test_report_requires_successful_run(self):
		with self.assertRaises(HTTPError) as context:
			urlopen(self.base + "/api/report/pdf")
		self.assertEqual(context.exception.code, 404)
