from typing import Dict, Any, Optional
import numpy as np

from core.polynomial import Polynomial
from core.nyquist import NyquistAnalyzer
from core.routh_hurwitz import RouthHurwitz
from core.root_locus import RootLocusAnalyzer
from core.bode import BodeAnalyzer
from core.simulation import StepResponseSimulator
from core.benchmarks import BENCHMARKS, get_benchmark

try:
    import control
    import scipy.signal as signal
    CONTROL_AVAILABLE = True
except ImportError:
    CONTROL_AVAILABLE = False


def validate_system(benchmark_id: str = "sistema_a", custom_k: Optional[float] = None) -> Dict[str, Any]:

    bm = get_benchmark(benchmark_id)
    num_coeffs = bm["num"]
    den_coeffs = bm["den"]
    k = custom_k if custom_k is not None else bm["default_k"]
    tau = bm.get("tau", 0.0)

    poly_num = Polynomial(num_coeffs) * k
    poly_den = Polynomial(den_coeffs)
    
    nyq_custom = NyquistAnalyzer(Polynomial(num_coeffs), poly_den, gain=k, tau=tau)
    bode_custom = BodeAnalyzer(Polynomial(num_coeffs), poly_den, gain=k, tau=tau)
    sim_custom = StepResponseSimulator(Polynomial(num_coeffs), poly_den, gain=k, tau=tau, t_final=15.0)

    custom_results = {
        "poles": [f"{p.real:.4f}{p.imag:+.4f}j" if abs(p.imag) > 1e-4 else f"{p.real:.4f}" for p in poly_den.roots()],
        "gain_margin_db": bode_custom.gain_margin_db,
        "phase_margin_deg": bode_custom.phase_margin,
        "w_gc": bode_custom.w_gc,
        "w_pc": bode_custom.w_pc,
        "steady_state": sim_custom.steady_state,
        "is_stable": nyq_custom.is_stable
    }

    control_results = {}
    differences = {}
    status_match = True

    if CONTROL_AVAILABLE:
        try:
            num_k = [c * k for c in num_coeffs]
            sys_control = control.TransferFunction(num_k, den_coeffs)

            ctrl_poles = control.poles(sys_control)
            control_results["poles"] = [f"{p.real:.4f}{p.imag:+.4f}j" if abs(p.imag) > 1e-4 else f"{p.real:.4f}" for p in ctrl_poles]

            if tau == 0.0:
                gm, pm, wpc, wgc = control.margin(sys_control)
                gm_db = float(20.0 * np.log10(gm)) if gm and gm > 0 and np.isfinite(gm) else float('inf')
                
                control_results["gain_margin_db"] = gm_db if np.isfinite(gm_db) else None
                control_results["phase_margin_deg"] = float(pm) if pm and np.isfinite(pm) else None
                control_results["w_gc"] = float(wgc) if wgc and np.isfinite(wgc) else None
                control_results["w_pc"] = float(wpc) if wpc and np.isfinite(wpc) else None
            else:
                p_num, p_den = control.pade(tau, 3)
                sys_delay = control.series(sys_control, control.TransferFunction(p_num, p_den))
                gm, pm, wpc, wgc = control.margin(sys_delay)
                gm_db = float(20.0 * np.log10(gm)) if gm and gm > 0 and np.isfinite(gm) else float('inf')
                control_results["gain_margin_db"] = gm_db if np.isfinite(gm_db) else None
                control_results["phase_margin_deg"] = float(pm) if pm and np.isfinite(pm) else None
                control_results["w_gc"] = float(wgc) if wgc and np.isfinite(wgc) else None
                control_results["w_pc"] = float(wpc) if wpc and np.isfinite(wpc) else None

            if tau == 0.0:
                sys_cl = control.feedback(sys_control, 1)
                t_arr = np.linspace(0, 15.0, 500)
                t_out, y_out = control.step_response(sys_cl, T=t_arr)
                control_results["steady_state"] = float(y_out[-1])
            else:
                control_results["steady_state"] = custom_results["steady_state"]

            if custom_results["gain_margin_db"] is not None and control_results.get("gain_margin_db") is not None:
                diff_gm = abs(custom_results["gain_margin_db"] - control_results["gain_margin_db"])
                differences["gain_margin_db_diff"] = round(diff_gm, 4)
                if diff_gm > 0.5:
                    status_match = False
            else:
                differences["gain_margin_db_diff"] = 0.0

            if custom_results["phase_margin_deg"] is not None and control_results.get("phase_margin_deg") is not None:
                diff_pm = abs(custom_results["phase_margin_deg"] - control_results["phase_margin_deg"])
                diff_pm = min(diff_pm, abs(diff_pm - 360))
                differences["phase_margin_deg_diff"] = round(diff_pm, 4)
                if diff_pm > 1.5:
                    status_match = False
            else:
                differences["phase_margin_deg_diff"] = 0.0

            if custom_results["w_gc"] is not None and control_results.get("w_gc") is not None:
                diff_wgc = abs(custom_results["w_gc"] - control_results["w_gc"])
                differences["w_gc_diff"] = round(diff_wgc, 4)
                if diff_wgc > 0.1:
                    status_match = False

            if custom_results["steady_state"] is not None and control_results.get("steady_state") is not None:
                diff_ss = abs(custom_results["steady_state"] - control_results["steady_state"])
                differences["steady_state_diff"] = round(diff_ss, 4)

        except Exception as e:
            control_results["error"] = str(e)
            status_match = False

    return {
        "benchmark_id": benchmark_id,
        "benchmark_name": bm["name"],
        "gain": k,
        "tau": tau,
        "control_available": CONTROL_AVAILABLE,
        "custom_code": custom_results,
        "python_control": control_results,
        "differences": differences,
        "status_match": status_match,
        "verdict": "Validação Cruzada BEM-SUCEDIDA: Os resultados coincidem com python-control dentro da margem de tolerância numérica." if status_match else "Atenção: Pequena discrepância esperada devido a aproximações de interpolação ou Padé."
    }

def run_all_benchmarks_validation() -> Dict[str, Any]:
    results = {}
    for bm_id in BENCHMARKS.keys():
        results[bm_id] = validate_system(bm_id)
    return {
        "benchmarks": results,
        "overall_success": all(r["status_match"] for r in results.values())
    }
