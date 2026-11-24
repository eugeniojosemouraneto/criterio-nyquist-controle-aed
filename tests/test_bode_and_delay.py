"""
Testes unitários para bode.py, pade.py e simulation.py.
"""

import unittest
import numpy as np
from core.polynomial import Polynomial
from core.bode import BodeAnalyzer
from core.pade import pade_approximation, apply_delay_pade
from core.simulation import StepResponseSimulator

class TestBodeAndDelay(unittest.TestCase):
    def test_bode_margins(self):
        # G(s) = 20 / (s^3 + 6s^2 + 11s + 6)
        num = Polynomial([1.0])
        den = Polynomial([1.0, 6.0, 11.0, 6.0])
        bode = BodeAnalyzer(num, den, gain=20.0)
        
        self.assertIsNotNone(bode.w_gc)
        self.assertIsNotNone(bode.w_pc)
        self.assertGreater(bode.phase_margin, 0.0)
        self.assertGreater(bode.gain_margin_db, 0.0)

    def test_pade_first_order(self):
        tau = 0.4
        p_num, p_den = pade_approximation(tau, order=1)
        # Padé 1: (-0.2 s + 1) / (0.2 s + 1) => coeffs: [-0.2, 1.0] / [0.2, 1.0]
        np.testing.assert_allclose(p_num.coeffs, [-0.2, 1.0], rtol=1e-5)
        np.testing.assert_allclose(p_den.coeffs, [0.2, 1.0], rtol=1e-5)

    def test_pade_second_order(self):
        tau = 1.0
        p_num, p_den = pade_approximation(tau, order=2)
        # Padé 2: c_2 = 1/12, c_1 = -1/2, c_0 = 1
        np.testing.assert_allclose(p_num.coeffs, [1/12, -0.5, 1.0], rtol=1e-5)
        np.testing.assert_allclose(p_den.coeffs, [1/12, 0.5, 1.0], rtol=1e-5)

    def test_step_response_stable_first_order(self):
        # G(s) = 1 / (s + 1), malha fechada T(s) = 1 / (s + 2)
        # Resposta ao degrau: y(t) = 0.5 * (1 - e^(-2t)), valor de regime = 0.5
        num = Polynomial([1.0])
        den = Polynomial([1.0, 1.0])
        sim = StepResponseSimulator(num, den, gain=1.0, t_final=5.0, num_steps=500)
        
        self.assertIsNotNone(sim.steady_state)
        self.assertAlmostEqual(sim.steady_state, 0.5, places=2)
        self.assertAlmostEqual(sim.overshoot, 0.0, places=2) # Não tem overshoot

    def test_step_response_with_delay(self):
        num = Polynomial([1.0])
        den = Polynomial([1.0, 1.0])
        sim_delayed = StepResponseSimulator(num, den, gain=1.0, tau=0.5, t_final=5.0)
        # Nos primeiros tau segundos, a saída com atraso na malha fechada deve partir de zero
        self.assertAlmostEqual(sim_delayed.y[0], 0.0)

if __name__ == "__main__":
    unittest.main()
