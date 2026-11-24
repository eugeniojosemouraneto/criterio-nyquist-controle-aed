import os
from flask import Flask, render_template, request, jsonify, send_from_directory
import numpy as np

from core.polynomial import Polynomial
from core.routh_hurwitz import RouthHurwitz
from core.nyquist import NyquistAnalyzer
from core.root_locus import RootLocusAnalyzer
from core.bode import BodeAnalyzer
from core.simulation import StepResponseSimulator
from core.pade import pade_approximation, apply_delay_pade
from core.benchmarks import BENCHMARKS, get_benchmark
from core.scalability import run_scalability_suite, benchmark_order
from core.cross_validation import validate_system, run_all_benchmarks_validation, CONTROL_AVAILABLE

app = Flask(__name__)

def parse_polynomial_input(val) -> Polynomial:
    if isinstance(val, (list, tuple)):
        return Polynomial([float(x) for x in val])
    if isinstance(val, (int, float)):
        return Polynomial([float(val)])
    if isinstance(val, str):
        cleaned = val.replace(",", " ").replace(";", " ")
        tokens = [t.strip() for t in cleaned.split() if t.strip()]
        return Polynomial([float(t) for t in tokens])
    return Polynomial([1.0])

@app.route("/")
def index():
    return render_template("index.html", benchmarks=BENCHMARKS)

@app.route("/benchmarks")
def benchmarks_page():
    return render_template("benchmarks.html", benchmarks=BENCHMARKS)

@app.route("/scalability")
def scalability_page():
    return render_template("scalability.html")

@app.route("/documentacao")
def documentation_page():
    return render_template("documentation.html")

@app.route("/favicon.ico")
def favicon():
    return send_from_directory(os.path.join(app.root_path, "static"), "favicon.svg", mimetype="image/svg+xml")

@app.route("/api/analyze", methods=["POST"])
def api_analyze():
    try:
        data = request.get_json(force=True) or {}
        
        benchmark_id = data.get("benchmark_id")
        if benchmark_id and benchmark_id in BENCHMARKS:
            bm = BENCHMARKS[benchmark_id]
            num = Polynomial(bm["num"])
            den = Polynomial(bm["den"])
            default_k = float(data.get("gain", bm.get("default_k", 1.0)))
            tau = float(data.get("tau", bm.get("tau", 0.0)))
        else:
            num = parse_polynomial_input(data.get("num", [1.0]))
            den = parse_polynomial_input(data.get("den", [1.0, 3.0, 2.0]))
            default_k = float(data.get("gain", 1.0))
            tau = max(0.0, float(data.get("tau", 0.0)))
            
        gain = default_k

        # 1. Routh-Hurwitz: D(s) + K*N(s) = 0
        if tau > 0:
            p_num, p_den = apply_delay_pade(num * gain, den, tau, order=1)
            char_poly = p_den + p_num
            routh = RouthHurwitz(char_poly)
            routh_note = f"Com atraso tau = {tau}s, Routh-Hurwitz foi avaliado utilizando aproximação de Padé [1/1]."
        else:
            char_poly = den + (num * gain)
            routh = RouthHurwitz(char_poly)
            routh_note = "Sem atraso puro: equação característica exata 1 + K*G(s) = 0."

        routh_data = routh.to_dict()
        routh_data["note"] = routh_note

        # 2. Nyquist: Z = N + P
        nyquist = NyquistAnalyzer(num, den, gain=gain, tau=tau)
        nyquist_data = nyquist.get_plot_data()

        # 3. Root Locus: 1 + K*G(s) = 0
        if tau > 0:
            rl_num, rl_den = apply_delay_pade(num, den, tau, order=1)
            rl = RootLocusAnalyzer(rl_num, rl_den, current_k=gain, k_max=max(50.0, gain * 2.5))
            rl_data = rl.get_plot_data()
            rl_data["note"] = f"Lugar das Raízes traçado com aproximação de Padé [1/1] para o atraso tau = {tau}s."
        else:
            rl = RootLocusAnalyzer(num, den, current_k=gain, k_max=max(50.0, gain * 2.5))
            rl_data = rl.get_plot_data()
            rl_data["note"] = "Lugar das Raízes exato da função de malha aberta."

        # 4. Bode: 20*log10(|G|) e fase
        bode = BodeAnalyzer(num, den, gain=gain, tau=tau)
        bode_data = bode.get_plot_data()

        # 5. Resposta ao Degrau (RK4)
        poles = den.roots()
        real_parts = [abs(p.real) for p in poles if abs(p.real) > 1e-3]
        min_real = min(real_parts) if real_parts else 1.0
        t_final = min(40.0, max(5.0, 5.0 / min_real + 2.0 * tau))
        
        sim = StepResponseSimulator(num, den, gain=gain, tau=tau, t_final=t_final)
        sim_data = sim.get_plot_data()

        # 6. Padé vs Exato (tau > 0)
        pade_comparison = None
        if tau > 0:
            pade_comparison = {}
            for order in [1, 2]:
                p_n, p_d = apply_delay_pade(num, den, tau, order=order)
                sim_p = StepResponseSimulator(p_n, p_d, gain=gain, tau=0.0, t_final=t_final)
                nyq_p = NyquistAnalyzer(p_n, p_d, gain=gain, tau=0.0)
                pade_comparison[f"pade_{order}"] = {
                    "order": order,
                    "step_time": sim_p.get_plot_data()["time"],
                    "step_response": sim_p.get_plot_data()["response"],
                    "nyquist_real": [float(r.real) for r in nyq_p.response[::5]],
                    "nyquist_imag": [float(r.imag) for r in nyq_p.response[::5]]
                }

        return jsonify({
            "success": True,
            "gain": gain,
            "tau": tau,
            "num_str": num.to_string(),
            "den_str": den.to_string(),
            "char_poly_str": char_poly.to_string(),
            "routh": routh_data,
            "nyquist": nyquist_data,
            "root_locus": rl_data,
            "bode": bode_data,
            "step_response": sim_data,
            "pade_comparison": pade_comparison
        })

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400

@app.route("/api/scalability", methods=["POST"])
def api_scalability():
    try:
        data = request.get_json(force=True) or {}
        orders = data.get("orders", [3, 5, 8, 10, 15, 20])
        orders = [int(o) for o in orders if 2 <= int(o) <= 30]
        results = run_scalability_suite(orders)
        return jsonify({"success": True, "data": results})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400

@app.route("/api/benchmark/<benchmark_id>", methods=["GET"])
def api_get_benchmark(benchmark_id):
    if benchmark_id not in BENCHMARKS:
        return jsonify({"success": False, "error": "Benchmark não encontrado"}), 404
    return jsonify({"success": True, "benchmark": BENCHMARKS[benchmark_id]})

@app.route("/api/cross-validation", methods=["GET"])
def api_cross_validation_all():
    results = run_all_benchmarks_validation()
    return jsonify({"success": True, "data": results})

@app.route("/api/cross-validation/<benchmark_id>", methods=["GET"])
def api_cross_validation_single(benchmark_id):
    if benchmark_id not in BENCHMARKS:
        return jsonify({"success": False, "error": "Benchmark não encontrado"}), 404
    k = request.args.get("gain", type=float)
    result = validate_system(benchmark_id, custom_k=k)
    return jsonify({"success": True, "data": result})

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
