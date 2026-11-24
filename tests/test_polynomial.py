"""
Testes unitários para o módulo core.polynomial.
"""

import unittest
import numpy as np
from core.polynomial import Polynomial

class TestPolynomial(unittest.TestCase):
    def test_creation_and_string(self):
        p = Polynomial([1.0, 6.0, 11.0, 6.0])
        self.assertEqual(p.degree, 3)
        self.assertIn("s^3", p.to_string())
        self.assertIn("6s^2", p.to_string())

    def test_evaluate(self):
        # P(s) = s^2 + 3s + 2 = (s+1)(s+2)
        p = Polynomial([1.0, 3.0, 2.0])
        # P(-1) = 0, P(0) = 2, P(1) = 6
        self.assertAlmostEqual(p.evaluate(-1.0), 0.0)
        self.assertAlmostEqual(p.evaluate(0.0), 2.0)
        self.assertAlmostEqual(p.evaluate(1.0), 6.0)

    def test_roots(self):
        # P(s) = (s + 1)(s + 2)(s + 3) = s^3 + 6s^2 + 11s + 6
        p = Polynomial([1.0, 6.0, 11.0, 6.0])
        r = p.roots()
        self.assertEqual(len(r), 3)
        expected = [-1.0, -2.0, -3.0]
        # Verifica se as raízes encontradas estão próximas dos valores esperados
        for exp in expected:
            dists = [abs(val - exp) for val in r]
            self.assertLess(min(dists), 1e-5)

    def test_derivative(self):
        # P(s) = s^3 + 6s^2 + 11s + 6 => P'(s) = 3s^2 + 12s + 11
        p = Polynomial([1.0, 6.0, 11.0, 6.0])
        dp = p.derivative()
        self.assertEqual(dp.degree, 2)
        np.testing.assert_allclose(dp.coeffs, [3.0, 12.0, 11.0])

    def test_arithmetic(self):
        p1 = Polynomial([1.0, 2.0]) # s + 2
        p2 = Polynomial([1.0, 3.0]) # s + 3
        # Produto: (s+2)(s+3) = s^2 + 5s + 6
        p_prod = p1 * p2
        np.testing.assert_allclose(p_prod.coeffs, [1.0, 5.0, 6.0])
        
        # Soma: (s+2) + (s+3) = 2s + 5
        p_sum = p1 + p2
        np.testing.assert_allclose(p_sum.coeffs, [2.0, 5.0])

    def test_from_roots(self):
        roots = [-1.0, -2.0, -3.0]
        p = Polynomial.from_roots(roots)
        np.testing.assert_allclose(p.coeffs, [1.0, 6.0, 11.0, 6.0])

if __name__ == "__main__":
    unittest.main()
