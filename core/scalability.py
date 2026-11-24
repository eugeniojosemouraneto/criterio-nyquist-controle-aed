import time
from typing import Dict, Any, List, Tuple
import numpy as np
from core.polynomial import Polynomial
from core.routh_hurwitz import RouthHurwitz
from core.nyquist import NyquistAnalyzer
from core.root_locus import RootLocusAnalyzer

def generate_stable_system(order: int) -> Tuple[Polynomial, Polynomial]:
    poles = [-float(k + 1) for k in range(order)]
    den = Polynomial.from_roots(poles)
    num = Polynomial([1.0])
    return num, den

def benchmark_order(order: int, num_runs: int = 5) -> Dict[str, Any]:
    num, den = generate_stable_system(order)
    
    # 1. Routh-Hurwitz O(n^2)
    routh_times = []
    for _ in range(num_runs):
        t0 = time.perf_counter()
        rh = RouthHurwitz(den)
        routh_times.append(time.perf_counter() - t0)
    avg_routh_time_ms = float(np.mean(routh_times) * 1000.0)
    
    # 2. Nyquist O(M*n)
    nyquist_times = []
    for _ in range(num_runs):
        t0 = time.perf_counter()
        nyq = NyquistAnalyzer(num, den, gain=1.0, w_points=800)
        nyquist_times.append(time.perf_counter() - t0)
    avg_nyquist_time_ms = float(np.mean(nyquist_times) * 1000.0)
    
    # 3. Root Locus O(K_points * n^3)
    rl_times = []
    for _ in range(num_runs):
        t0 = time.perf_counter()
        rl = RootLocusAnalyzer(num, den, current_k=1.0, k_max=50.0, num_points=150)
        rl_times.append(time.perf_counter() - t0)
    avg_rl_time_ms = float(np.mean(rl_times) * 1000.0)
    
    computed_roots = den.roots()
    poles = [-float(k + 1) for k in range(order)]
    sorted_orig = np.sort(poles)
    sorted_calc = np.sort(computed_roots.real)
    max_root_err = float(np.max(np.abs(sorted_orig - sorted_calc)))
    
    # erro_rel = max |s_orig - s_calc| / max |s_orig|
    rel_error = float(max_root_err / max(1.0, float(order)))
    
    c = den.coeffs
    coef_dynamic_range = float(np.max(c) / np.min(c[c > 0])) if np.any(c > 0) else 1.0

    return {
        "order": order,
        "routh_time_ms": round(avg_routh_time_ms, 4),
        "nyquist_time_ms": round(avg_nyquist_time_ms, 4),
        "root_locus_time_ms": round(avg_rl_time_ms, 4),
        "total_time_ms": round(avg_routh_time_ms + avg_nyquist_time_ms + avg_rl_time_ms, 4),
        "relative_error": rel_error,
        "root_error": max_root_err,
        "coef_dynamic_range": coef_dynamic_range,
        "routh_stable": rh.is_stable,
        "nyquist_stable": nyq.is_stable,
        "winding_number": nyq.N
    }

def run_scalability_suite(orders: List[int] = [3, 5, 8, 10, 15, 20]) -> Dict[str, Any]:
    results = []
    for n in orders:
        res = benchmark_order(n)
        results.append(res)
        
    return {
        "benchmark_results": results,
        "summary": "O tempo de computação de Routh escala em O(n^2), Nyquist em O(M*n) e Root Locus em O(K*n^3). "
                   "O erro relativo cresce exponencialmente com n devido ao condicionamento do polinômio (Fenômeno de Wilkinson)."
    }
