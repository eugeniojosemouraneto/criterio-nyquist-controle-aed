"""
Módulo de Algoritmos de Controle Clássico e Análise de Estabilidade. Sem uso de bibliotecas de controle.
"""

from core.polynomial import Polynomial
from core.pade import pade_approximation, apply_delay_pade
from core.routh_hurwitz import RouthHurwitz
from core.nyquist import NyquistAnalyzer
from core.root_locus import RootLocusAnalyzer
from core.bode import BodeAnalyzer
from core.simulation import StepResponseSimulator
from core.benchmarks import BENCHMARKS, get_benchmark
from core.scalability import benchmark_order, run_scalability_suite

__all__ = [
    "Polynomial",
    "pade_approximation",
    "apply_delay_pade",
    "RouthHurwitz",
    "NyquistAnalyzer",
    "RootLocusAnalyzer",
    "BodeAnalyzer",
    "StepResponseSimulator",
    "BENCHMARKS",
    "get_benchmark",
    "benchmark_order",
    "run_scalability_suite",
]
