from typing import List, Dict, Any, Tuple, Optional, Union
import numpy as np
from core.polynomial import Polynomial

class NyquistAnalyzer:

    def __init__(self, 
                 num: Polynomial, 
                 den: Polynomial, 
                 gain: float = 1.0, 
                 tau: float = 0.0,
                 w_points: int = 1500,
                 w_min: float = 1e-3,
                 w_max: float = 1e3):
        self.num = num * gain
        self.den = den
        self.gain = gain
        self.tau = max(0.0, float(tau))
        self.w_points = w_points
        self.w_min = w_min
        self.w_max = w_max
        
        self.open_loop_poles = self.den.roots()
        self.open_loop_zeros = self.num.roots()
        
        # P: polos de malha aberta no semiplano direito (Re > 0)
        self.P = int(np.sum(self.open_loop_poles.real > 1e-7))
        self.poles_on_imag = [p for p in self.open_loop_poles if abs(p.real) < 1e-6]
        
        self.omega = np.array([])
        self.response = np.array([], dtype=np.complex128)
        self.full_contour_response = np.array([], dtype=np.complex128)
        
        self.N = 0                  
        self.Z = 0                 
        self.is_stable = False
        self.gain_margin = None     
        self.gain_margin_db = None  
        self.phase_margin = None    
        self.w_pc = None            
        self.w_gc = None            
        self.stability_summary = ""
        
        self._analyze()

    def evaluate_gh(self, s: Union[complex, np.ndarray]) -> Union[complex, np.ndarray]:
        n_val = self.num.evaluate(s)
        d_val = self.den.evaluate(s)
        
        mask_zero = np.abs(d_val) < 1e-15
        if np.any(mask_zero):
            if isinstance(d_val, np.ndarray):
                d_val = d_val.copy()
                d_val[mask_zero] = 1e-15
            else:
                d_val = 1e-15
                
        gh = n_val / d_val
        
        # Atraso de transporte puro: e^(-tau * s)
        if self.tau > 0:
            delay_factor = np.exp(-self.tau * s)
            gh = gh * delay_factor
            
        return gh

    def _generate_contour(self):
        w_pos = np.logspace(np.log10(self.w_min), np.log10(self.w_max), self.w_points)
        
        has_pole_at_origin = any(abs(p) < 1e-5 for p in self.open_loop_poles)
        indentation_points = []
        if has_pole_at_origin:
            eps = 1e-4
            thetas = np.linspace(-np.pi / 2, np.pi / 2, 80)
            s_indent = eps * np.exp(1j * thetas)
            indentation_points = [self.evaluate_gh(s) for s in s_indent]
            
        s_pos = 1j * w_pos
        gh_pos = self.evaluate_gh(s_pos)
        
        self.omega = w_pos
        self.response = gh_pos

        gh_neg = np.conj(gh_pos[::-1]) 
        
        contour = []
        contour.extend(gh_neg)
        if indentation_points:
            contour.extend(indentation_points)
        contour.extend(gh_pos)
        
        self.full_contour_response = np.array(contour, dtype=np.complex128)

    def _compute_winding_number(self) -> int:
        z0 = -1.0 + 0.0j
        pts = self.full_contour_response - z0
        
        angles = np.angle(pts)
        diffs = np.diff(angles)
        diffs = (diffs + np.pi) % (2 * np.pi) - np.pi
        
        # W = sum(diffs) / (2*pi) e N = -W (horário em torno de -1)
        total_angle = np.sum(diffs)
        winding_counter_clockwise = total_angle / (2 * np.pi)
        N_clockwise = int(np.round(-winding_counter_clockwise))
        
        ray_crossings = 0
        real_pts = self.full_contour_response.real
        imag_pts = self.full_contour_response.imag
        n_pts = len(pts)
        for i in range(n_pts - 1):
            y1, y2 = imag_pts[i], imag_pts[i+1]
            x1, x2 = real_pts[i], real_pts[i+1]
            if (y1 <= 0 < y2) or (y2 <= 0 < y1):
                t = -y1 / (y2 - y1)
                x_cross = x1 + t * (x2 - x1)
                if x_cross < -1.0:
                    if y1 < y2:
                        ray_crossings -= 1
                    else:
                        ray_crossings += 1
                        
        return N_clockwise

    def _extract_margins(self):
        mag = np.abs(self.response)
        phase_rad = np.unwrap(np.angle(self.response))
        phase_deg = np.rad2deg(phase_rad)
        
        # |G(j*w_gc)| = 1, MF = 180° + arg(G(j*w_gc))
        diff_mag = mag - 1.0
        sign_changes_mag = np.where(np.diff(np.sign(diff_mag)))[0]
        
        if len(sign_changes_mag) > 0:
            idx = sign_changes_mag[0]
            w1, w2 = self.omega[idx], self.omega[idx + 1]
            m1, m2 = mag[idx], mag[idx + 1]
            p1, p2 = phase_deg[idx], phase_deg[idx + 1]
            
            frac = (1.0 - m1) / (m2 - m1) if abs(m2 - m1) > 1e-12 else 0.0
            self.w_gc = float(w1 + frac * (w2 - w1))
            phi_at_wgc = float(p1 + frac * (p2 - p1))
            
            norm_phi = (phi_at_wgc + 180.0) % 360.0 - 180.0
            self.phase_margin = float(norm_phi + 180.0)
            if self.phase_margin > 180:
                self.phase_margin -= 360
        else:
            self.w_gc = None
            self.phase_margin = None

        # arg(G(j*w_pc)) = -180°, MG = 1 / |G(j*w_pc)|
        candidates_pc = []
        try:
            d0_val = self.den.evaluate(0.0)
            if abs(d0_val) > 1e-12:
                g0_real = float((self.num.evaluate(0.0) / d0_val).real)
                if g0_real < -1e-9:
                    candidates_pc.append({
                        "w": 0.0,
                        "mag": abs(g0_real)
                    })
        except Exception:
            pass

        im_vals = self.response.imag
        re_vals = self.response.real
        sign_cross_im = np.where(np.diff(np.sign(im_vals)))[0]
        
        for idx in sign_cross_im:
            w1, w2 = self.omega[idx], self.omega[idx + 1]
            im1, im2 = im_vals[idx], im_vals[idx + 1]
            re1, re2 = re_vals[idx], re_vals[idx + 1]
            
            frac = (-im1) / (im2 - im1) if abs(im2 - im1) > 1e-15 else 0.0
            re_cross = float(re1 + frac * (re2 - re1))
            
            if re_cross < -1e-9:
                w_cross = float(w1 + frac * (w2 - w1))
                candidates_pc.append({
                    "w": w_cross,
                    "mag": abs(re_cross)
                })

        pos_candidates = [c for c in candidates_pc if c["w"] > 0]
        if pos_candidates:
            best_pc = min(pos_candidates, key=lambda c: abs(np.log(c["mag"] + 1e-15)))
        elif candidates_pc:
            best_pc = candidates_pc[0]
        else:
            best_pc = None

        if best_pc is not None:
            self.w_pc = best_pc["w"]
            mag_at_wpc = best_pc["mag"]
            if mag_at_wpc > 1e-12:
                # MG = 1 / |G(j*w_pc)|, MG_dB = -20*log10(|G(j*w_pc)|)
                self.gain_margin = float(1.0 / mag_at_wpc)
                self.gain_margin_db = float(-20.0 * np.log10(mag_at_wpc))
            else:
                self.gain_margin = float('inf')
                self.gain_margin_db = float('inf')
        else:
            self.w_pc = None
            self.gain_margin = None
            self.gain_margin_db = None

    def _analyze(self):
        self._generate_contour()
        self.N = self._compute_winding_number()
        # Teorema de Nyquist: Z = N + P
        self.Z = self.N + self.P
        self.is_stable = (self.Z == 0)
        
        self._extract_margins()
        
        self._extract_margins()
        
        if self.is_stable:
            mg_str = f"{self.gain_margin_db:.2f} dB" if self.gain_margin_db is not None else "Infinito"
            mf_str = f"{self.phase_margin:.2f}°" if self.phase_margin is not None else "Infinita"
            self.stability_summary = (
                f"Sistema em Malha Fechada ESTÁVEL: Z = N + P = {self.N} + {self.P} = {self.Z}. "
                f"MG = {mg_str}, MF = {mf_str}."
            )
        else:
            self.stability_summary = (
                f"Sistema em Malha Fechada INSTÁVEL: Z = N + P = {self.N} + {self.P} = {self.Z} "
                f"polo(s) instável(is) no semiplano direito (RHP)."
            )

    def get_plot_data(self, max_points: int = 500) -> Dict[str, Any]:
        step = max(1, len(self.response) // max_points)
        pos_sampled = self.response[::step]
        neg_sampled = np.conj(pos_sampled)
        
        return {
            "real_pos": [float(r.real) for r in pos_sampled],
            "imag_pos": [float(r.imag) for r in pos_sampled],
            "real_neg": [float(r.real) for r in neg_sampled],
            "imag_neg": [float(r.imag) for r in neg_sampled],
            "critical_point": [-1.0, 0.0],
            "P": self.P,
            "N": self.N,
            "Z": self.Z,
            "is_stable": self.is_stable,
            "gain_margin": self.gain_margin,
            "gain_margin_db": self.gain_margin_db,
            "phase_margin": self.phase_margin,
            "w_pc": self.w_pc,
            "w_gc": self.w_gc,
            "stability_summary": self.stability_summary
        }
