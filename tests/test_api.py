"""
Testes unitários das rotas e APIs do Flask (app.py).
"""

import unittest
import json
from app import app

class TestAPI(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()
        self.client.testing = True

    def test_pages_render(self):
        routes = ["/", "/benchmarks", "/scalability", "/documentacao", "/favicon.ico"]
        for r in routes:
            resp = self.client.get(r)
            self.assertEqual(resp.status_code, 200, f"Falha na rota {r}")

    def test_api_benchmark_lookup(self):
        resp = self.client.get("/api/benchmark/sistema_a")
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.data)
        self.assertTrue(data["success"])
        self.assertEqual(data["benchmark"]["id"], "sistema_a")

    def test_api_analyze_benchmark(self):
        payload = {
            "benchmark_id": "sistema_a",
            "gain": 20.0,
            "tau": 0.0
        }
        resp = self.client.post("/api/analyze", data=json.dumps(payload), content_type="application/json")
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.data)
        self.assertTrue(data["success"])
        self.assertIn("nyquist", data)
        self.assertIn("routh", data)
        self.assertIn("root_locus", data)
        self.assertIn("bode", data)
        self.assertIn("step_response", data)
        self.assertTrue(data["nyquist"]["is_stable"])

    def test_api_analyze_with_delay(self):
        payload = {
            "benchmark_id": "sistema_d",
            "gain": 2.5,
            "tau": 0.5
        }
        resp = self.client.post("/api/analyze", data=json.dumps(payload), content_type="application/json")
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.data)
        self.assertTrue(data["success"])
        self.assertIsNotNone(data["pade_comparison"])

    def test_api_scalability(self):
        payload = {"orders": [3, 5]}
        resp = self.client.post("/api/scalability", data=json.dumps(payload), content_type="application/json")
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.data)
        self.assertTrue(data["success"])
        self.assertEqual(len(data["data"]["benchmark_results"]), 2)

    def test_api_cross_validation_routes(self):
        resp_all = self.client.get("/api/cross-validation")
        self.assertEqual(resp_all.status_code, 200)
        data_all = json.loads(resp_all.data)
        self.assertTrue(data_all["success"])
        self.assertIn("benchmarks", data_all["data"])

        resp_single = self.client.get("/api/cross-validation/sistema_a?gain=20.0")
        self.assertEqual(resp_single.status_code, 200)
        data_single = json.loads(resp_single.data)
        self.assertTrue(data_single["success"])
        self.assertTrue(data_single["data"]["status_match"])

if __name__ == "__main__":
    unittest.main()
