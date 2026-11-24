"""
Testes unitários para o módulo core.routh_hurwitz.
"""

import unittest
from core.polynomial import Polynomial
from core.routh_hurwitz import RouthHurwitz

class TestRouthHurwitz(unittest.TestCase):
    def test_stable_system(self):
        # q(s) = s^3 + 6s^2 + 11s + 6 = 0 (polos em -1, -2, -3)
        p = Polynomial([1.0, 6.0, 11.0, 6.0])
        rh = RouthHurwitz(p)
        self.assertTrue(rh.is_stable)
        self.assertEqual(rh.sign_changes, 0)
        self.assertEqual(rh.num_rhp_poles, 0)

    def test_unstable_system_one_rhp_pole(self):
        # q(s) = (s - 2)(s + 1)(s + 2) = (s - 2)(s^2 + 3s + 2) = s^3 + s^2 - 4s - 4
        p = Polynomial([1.0, 1.0, -4.0, -4.0])
        rh = RouthHurwitz(p)
        self.assertFalse(rh.is_stable)
        self.assertEqual(rh.sign_changes, 1)
        self.assertEqual(rh.num_rhp_poles, 1)

    def test_unstable_system_two_rhp_poles(self):
        # q(s) = (s - 1)(s - 2)(s + 3) = s^3 - 7s + 6
        # Coeficientes: 1, 0, -7, 6
        p = Polynomial([1.0, 0.0, -7.0, 6.0])
        rh = RouthHurwitz(p)
        self.assertFalse(rh.is_stable)
        self.assertGreater(rh.sign_changes, 0)

    def test_special_case_zero_in_first_column(self):
        # q(s) = s^3 + 2s^2 + s + 2 = 0
        # Linha s^3: 1, 1
        # Linha s^2: 2, 2
        # Linha s^1: (2*1 - 1*2)/2 = 0 (linha inteira de zeros ou primeiro termo zero!)
        p = Polynomial([1.0, 2.0, 1.0, 2.0])
        rh = RouthHurwitz(p)
        # Deve ter detectado caso especial
        self.assertGreater(len(rh.special_cases), 0)

    def test_benchmark_a_gain_margin(self):
        # G(s) = K / (s^3 + 6s^2 + 11s + 6)
        # Malha fechada: s^3 + 6s^2 + 11s + (6 + K) = 0
        # Estável para K < 60, instável para K > 60
        # Teste K = 20: 6 + 20 = 26
        p_stable = Polynomial([1.0, 6.0, 11.0, 26.0])
        rh_stable = RouthHurwitz(p_stable)
        self.assertTrue(rh_stable.is_stable)
        
        # Teste K = 70: 6 + 70 = 76
        p_unstable = Polynomial([1.0, 6.0, 11.0, 76.0])
        rh_unstable = RouthHurwitz(p_unstable)
        self.assertFalse(rh_unstable.is_stable)
        self.assertEqual(rh_unstable.sign_changes, 2)

if __name__ == "__main__":
    unittest.main()
