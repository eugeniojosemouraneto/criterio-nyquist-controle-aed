"""
Testes unitários para os 4 Benchmarks e módulo de escalabilidade.
"""

import unittest
from core.benchmarks import BENCHMARKS, get_benchmark
from core.polynomial import Polynomial
from core.routh_hurwitz import RouthHurwitz
from core.nyquist import NyquistAnalyzer
from core.scalability import benchmark_order

class TestBenchmarksAndScalability(unittest.TestCase):
    def test_benchmarks_exist(self):
        keys = ["sistema_a", "sistema_b", "sistema_c", "sistema_d"]
        for k in keys:
            self.assertIn(k, BENCHMARKS)
            bm = get_benchmark(k)
            self.assertIn("name", bm)
            self.assertIn("den", bm)

    def test_benchmark_c_non_minimum_phase(self):
        # Sistema C tem zero no semiplano direito (s = +2)
        bm_c = get_benchmark("sistema_c")
        num = Polynomial(bm_c["num"])
        den = Polynomial(bm_c["den"])
        zeros = num.roots()
        self.assertTrue(any(z.real > 0 for z in zeros))

    def test_benchmark_d_delay(self):
        bm_d = get_benchmark("sistema_d")
        self.assertGreater(bm_d["tau"], 0.0)

    def test_scalability_orders(self):
        for n in [3, 5, 10]:
            res = benchmark_order(n, num_runs=2)
            self.assertEqual(res["order"], n)
            self.assertGreater(res["total_time_ms"], 0.0)
            self.assertLess(res["relative_error"], 1e-1)

if __name__ == "__main__":
    unittest.main()
