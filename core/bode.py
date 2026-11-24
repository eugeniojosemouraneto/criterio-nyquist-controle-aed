
from typing import Dict, Any, Tuple, Optional
import numpy as np
from core.polynomial import Polynomial

class BodeAnalyzer:

    def __init__(self, 
                 num: Polynomial, 
                 den: Polynomial, 
                 gain: float = 1.0, 
                 tau: float = 0.0,
                 w_min: float = 1e-2, 
                 w_max: float = 1e3, 
                 num_points: int = 400):
        self.num = num * gain
        self.den = den
        self.gain = float(gain)
        self.tau = max(0.0, float(tau))
        self.w_min = w_min
        self.w_max = w_max
        self.num_points = num_points
        
        self.omega = np.logspace(np.log10(self.w_min), np.log10(self.w_max), self.num_points)
        self.magnitude_db = np.array([])
        self.phase_deg = np.array([])
        
        self.w_gc: Optional[float] = None
        self.phase_margin: Optional[float] = None
        self.w_pc: Optional[float] = None
        self.gain_margin_db: Optional[float] = None
        
        self._compute()

    def _compute(self):
        s = 1j * self.omega
        n_vals = self.num.evaluate(s)
        d_vals = self.den.evaluate(s)
        
        mask_zero = np.abs(d_vals) < 1e-15
        if np.any(mask_zero):
            d_vals = d_vals.copy()
            d_vals[mask_zero] = 1e-15
            
        gh = n_vals / d_vals
        
        # |G(j*w)|_dB = 20 * log10(|G(j*w)|)
        mag_linear = np.abs(gh)
        self.magnitude_db = 20.0 * np.log10(np.maximum(mag_linear, 1e-12))
        
        phase_rad = np.unwrap(np.angle(gh))
        
        # arg(G(j*w)*e^(-j*w*tau)) = arg(G(j*w)) - w*tau
        if self.tau > 0:
            delay_phase = -self.omega * self.tau
            phase_rad = phase_rad + delay_phase
            
        self.phase_deg = np.rad2deg(phase_rad)
        
        # MF = 180° + arg(G(j*w_gc)) onde |G(j*w_gc)|_dB = 0
        diff_mag = self.magnitude_db
        sign_cross = np.where(np.diff(np.sign(diff_mag)))[0]
        if len(sign_cross) > 0:
            idx = sign_cross[0]
            w1, w2 = self.omega[idx], self.omega[idx + 1]
            m1, m2 = self.magnitude_db[idx], self.magnitude_db[idx + 1]
            p1, p2 = self.phase_deg[idx], self.phase_deg[idx + 1]
            
            frac = (-m1) / (m2 - m1) if abs(m2 - m1) > 1e-12 else 0.0
            self.w_gc = float(w1 + frac * (w2 - w1))
            phi_at_wgc = float(p1 + frac * (p2 - p1))
            
            pm = (phi_at_wgc + 180.0) % 360.0 - 180.0 + 180.0
            if pm > 180:
                pm -= 360
            self.phase_margin = float(pm)
            
        # MG_dB = -20*log10(|G(j*w_pc)|) onde Im(G(j*w_pc)) = 0 e Re(G(j*w_pc)) < 0
        phase_crossings = []
        try:
            d0_val = self.den.evaluate(0.0)
            if abs(d0_val) > 1e-12:
                g0_real = float((self.num.evaluate(0.0) / d0_val).real)
                if g0_real < -1e-9:
                    phase_crossings.append({
                        "w": 0.0,
                        "mag_db": float(20.0 * np.log10(abs(g0_real)))
                    })
        except Exception:
            pass

        im_vals = gh.imag
        re_vals = gh.real
        sign_cross_im = np.where(np.diff(np.sign(im_vals)))[0]
        
        for idx in sign_cross_im:
            w1, w2 = self.omega[idx], self.omega[idx + 1]
            im1, im2 = im_vals[idx], im_vals[idx + 1]
            re1, re2 = re_vals[idx], re_vals[idx + 1]
            
            frac = (-im1) / (im2 - im1) if abs(im2 - im1) > 1e-15 else 0.0
            re_cross = float(re1 + frac * (re2 - re1))
            
            if re_cross < -1e-9:
                w_cross = float(w1 + frac * (w2 - w1))
                mag_cross = abs(re_cross)
                phase_crossings.append({
                    "w": w_cross,
                    "mag_db": float(20.0 * np.log10(mag_cross))
                })

        pos_crossings = [c for c in phase_crossings if c["w"] > 0]
        if pos_crossings:
            best_pc = min(pos_crossings, key=lambda c: abs(c["mag_db"]))
            self.w_pc = best_pc["w"]
            self.gain_margin_db = float(-best_pc["mag_db"])
        elif phase_crossings:
            best_pc = phase_crossings[0]
            self.w_pc = best_pc["w"]
            self.gain_margin_db = float(-best_pc["mag_db"])
        else:
            self.w_pc = None
            self.gain_margin_db = None

    def get_plot_data(self) -> Dict[str, Any]:
        return {
            "omega": [float(w) for w in self.omega],
            "magnitude_db": [float(m) for m in self.magnitude_db],
            "phase_deg": [float(p) for p in self.phase_deg],
            "w_gc": self.w_gc,
            "phase_margin": self.phase_margin,
            "w_pc": self.w_pc,
            "gain_margin_db": self.gain_margin_db
        }
