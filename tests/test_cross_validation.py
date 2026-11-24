"""
Testes unitários de Validação Cruzada (Fase 3 do Projeto).
Confronta diretamente os cálculos do código próprio com a biblioteca python-control.
"""

import unittest
from core.cross_validation import validate_system, run_all_benchmarks_validation, CONTROL_AVAILABLE

class TestCrossValidation(unittest.TestCase):
    def setUp(self):
        if not CONTROL_AVAILABLE:
            self.skipTest("Biblioteca python-control não instalada no ambiente.")

    def test_benchmark_a_cross_validation(self):
        res = validate_system("sistema_a", custom_k=20.0)
        self.assertTrue(res["control_available"])
        self.assertTrue(res["status_match"])
        
        # Margem de Ganho: diferença deve ser mínima (< 0.2 dB)
        diff_gm = res["differences"].get("gain_margin_db_diff", 0.0)
        self.assertLess(diff_gm, 0.2)
        
        # Margem de Fase: diferença deve ser mínima (< 1.0 grau)
        diff_pm = res["differences"].get("phase_margin_deg_diff", 0.0)
        self.assertLess(diff_pm, 1.0)

    def test_benchmark_b_cross_validation(self):
        # Sistema B: planta instável com polo em +1
        res = validate_system("sistema_b", custom_k=18.0)
        self.assertTrue(res["status_match"])
        # Ambos devem identificar os mesmos polos
        self.assertEqual(len(res["custom_code"]["poles"]), len(res["python_control"]["poles"]))

    def test_benchmark_c_cross_validation(self):
        # Sistema C: fase não-mínima
        res = validate_system("sistema_c", custom_k=3.0)
        self.assertTrue(res["status_match"])

    def test_all_benchmarks_suite(self):
        suite = run_all_benchmarks_validation()
        self.assertTrue(suite["overall_success"])

if __name__ == "__main__":
    unittest.main()
