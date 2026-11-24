"""
Testes unitários para o módulo core.nyquist.
"""

import unittest
import numpy as np
from core.polynomial import Polynomial
from core.nyquist import NyquistAnalyzer

class TestNyquist(unittest.TestCase):
    def test_benchmark_a_stable(self):
        # Sistema A: G(s) = 20 / (s^3 + 6s^2 + 11s + 6)
        num = Polynomial([1.0])
        den = Polynomial([1.0, 6.0, 11.0, 6.0])
        nyq = NyquistAnalyzer(num, den, gain=20.0)
        
        self.assertEqual(nyq.P, 0)
        self.assertEqual(nyq.N, 0)
        self.assertEqual(nyq.Z, 0)
        self.assertTrue(nyq.is_stable)
        self.assertIsNotNone(nyq.gain_margin)
        self.assertGreater(nyq.gain_margin, 1.0)
        self.assertGreater(nyq.phase_margin, 0.0)

    def test_benchmark_a_unstable(self):
        # Sistema A com K = 80 (> Kcrit = 60)
        num = Polynomial([1.0])
        den = Polynomial([1.0, 6.0, 11.0, 6.0])
        nyq = NyquistAnalyzer(num, den, gain=80.0)
        
        self.assertEqual(nyq.P, 0)
        # Deve ter envoltórios horários N > 0 => Z > 0
        self.assertGreater(nyq.Z, 0)
        self.assertFalse(nyq.is_stable)

    def test_benchmark_b_unstable_open_loop(self):
        # Sistema B: G(s) = K / ( (s - 1)(s + 2)(s + 5) )
        # den = s^3 + 6s^2 + 3s - 10
        # P = 1 (polo em +1)
        num = Polynomial([1.0])
        den = Polynomial([1.0, 6.0, 3.0, -10.0])
        
        # Para K = 18 (faixa estável 10 < K < 28)
        nyq_stable = NyquistAnalyzer(num, den, gain=18.0)
        self.assertEqual(nyq_stable.P, 1)
        self.assertEqual(nyq_stable.N, -1) # 1 envoltório anti-horário
        self.assertEqual(nyq_stable.Z, 0)
        self.assertTrue(nyq_stable.is_stable)

        # Para K = 5 (abaixo de 10)
        nyq_unstable = NyquistAnalyzer(num, den, gain=5.0)
        self.assertEqual(nyq_unstable.P, 1)
        self.assertNotEqual(nyq_unstable.Z, 0)
        self.assertFalse(nyq_unstable.is_stable)

    def test_exact_delay_frequency_response(self):
        # G(s) = 1 / (s + 1), tau = 0.5s
        num = Polynomial([1.0])
        den = Polynomial([1.0, 1.0])
        nyq_no_delay = NyquistAnalyzer(num, den, gain=1.0, tau=0.0)
        nyq_delay = NyquistAnalyzer(num, den, gain=1.0, tau=0.5)
        
        # O módulo não deve ser alterado pelo atraso puro
        mag_no_delay = np.abs(nyq_no_delay.response)
        mag_delay = np.abs(nyq_delay.response)
        np.testing.assert_allclose(mag_no_delay, mag_delay, rtol=1e-5)
        
        # A fase com atraso deve ser menor (mais defasada)
        phase_no_delay = np.unwrap(np.angle(nyq_no_delay.response))
        phase_delay = np.unwrap(np.angle(nyq_delay.response))
        self.assertTrue(np.all(phase_delay <= phase_no_delay + 1e-6))

if __name__ == "__main__":
    unittest.main()
