"""
Testes unitários para o módulo core.root_locus.
"""

import unittest
import numpy as np
from core.polynomial import Polynomial
from core.root_locus import RootLocusAnalyzer

class TestRootLocus(unittest.TestCase):
    def test_benchmark_a_asymptotes(self):
        # G(s) = K / [(s+1)(s+2)(s+3)]
        # Polos em -1, -2, -3. Zeros: nenhum (m = 0).
        # n = 3, m = 0 => 3 assíntotas
        # Centroide: (-1 + -2 + -3) / 3 = -2.0
        # Ângulos: 180/3 = 60°, 3*180/3 = 180°, 5*180/3 = 300° (-60°)
        num = Polynomial([1.0])
        den = Polynomial([1.0, 6.0, 11.0, 6.0])
        rl = RootLocusAnalyzer(num, den, current_k=20.0, k_max=80.0)
        
        self.assertEqual(rl.n, 3)
        self.assertEqual(rl.m, 0)
        self.assertEqual(rl.num_asymptotes, 3)
        self.assertAlmostEqual(rl.centroid, -2.0, places=4)
        
        # Ângulos normalizados
        angles = sorted([round(a) for a in rl.asymptote_angles])
        self.assertEqual(angles, [-60, 60, 180])

    def test_branches_count(self):
        num = Polynomial([1.0])
        den = Polynomial([1.0, 6.0, 11.0, 6.0])
        rl = RootLocusAnalyzer(num, den, current_k=10.0)
        self.assertEqual(len(rl.branches), 3)

    def test_breakaway_points(self):
        # Entre -1 e -2 deve haver um ponto de dispersão no eixo real
        num = Polynomial([1.0])
        den = Polynomial([1.0, 6.0, 11.0, 6.0])
        rl = RootLocusAnalyzer(num, den)
        
        # P(s) = d(Den)/ds = 3s^2 + 12s + 11 = 0
        # Raízes analíticas: s = (-12 +- sqrt(144 - 132)) / 6 = (-12 +- sqrt(12))/6 = -2 +- 0.57735
        # s1 = -1.4226 (entre -1 e -2)
        self.assertGreater(len(rl.breakaway_points), 0)
        valid_break = any(-2.0 < pt < -1.0 for pt in rl.breakaway_points)
        self.assertTrue(valid_break)

if __name__ == "__main__":
    unittest.main()
