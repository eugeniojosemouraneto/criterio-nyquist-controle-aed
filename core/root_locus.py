from typing import List, Dict, Any, Tuple, Optional
import numpy as np
from core.polynomial import Polynomial

class RootLocusAnalyzer:
    def __init__(self, num: Polynomial, den: Polynomial, current_k: float = 1.0, k_max: float = 100.0, num_points: int = 400):
        self.num = num
        self.den = den
        self.current_k = float(current_k)
        self.k_max = float(k_max)
        self.num_points = num_points
        
        self.open_poles = self.den.roots()
        self.open_zeros = self.num.roots()
        self.n = len(self.open_poles)
        self.m = len(self.open_zeros)
        
        self.num_asymptotes = max(0, self.n - self.m)
        self.centroid = 0.0
        self.asymptote_angles: List[float] = []
        self.breakaway_points: List[float] = []
        self.imaginary_crossings: List[Dict[str, float]] = []
        
        self.k_values = np.array([])
        self.branches: List[List[complex]] = []
        self.current_closed_loop_poles: List[complex] = []
        
        self._analyze()

    def _calculate_asymptotes(self):
        if self.num_asymptotes <= 0:
            return
            
        # sigma_a = (sum(polos) - sum(zeros)) / (n - m)
        sum_poles = np.sum(self.open_poles).real
        sum_zeros = np.sum(self.open_zeros).real if self.m > 0 else 0.0
        self.centroid = float((sum_poles - sum_zeros) / self.num_asymptotes)
        
        # phi_a = (2k + 1) * 180° / (n - m)
        angles = []
        for k in range(self.num_asymptotes):
            ang = ((2 * k + 1) * 180.0) / self.num_asymptotes
            ang_norm = (ang + 180.0) % 360.0 - 180.0
            if abs(ang_norm - (-180.0)) < 1e-5:
                ang_norm = 180.0
            angles.append(float(ang_norm))
        self.asymptote_angles = sorted(angles)

    def _calculate_breakaway_points(self):
        d_den = self.den.derivative()
        d_num = self.num.derivative()
        
        # dK/ds = 0 => Num(s)*Den'(s) - Den(s)*Num'(s) = 0
        poly_break = (self.num * d_den) - (self.den * d_num)
        candidate_roots = poly_break.roots()
        
        breakaways = []
        for r in candidate_roots:
            if abs(r.imag) < 1e-5:
                sigma = float(r.real)
                # K = -Den(sigma) / Num(sigma) >= 0
                den_val = self.den.evaluate(sigma).real
                num_val = self.num.evaluate(sigma).real
                if abs(num_val) > 1e-12:
                    k_val = -den_val / num_val
                    if k_val >= -1e-6:
                        breakaways.append(sigma)
                        
        self.breakaway_points = sorted(list(set([round(x, 4) for x in breakaways])))

    def _trace_branches(self):
        if self.n == 0:
            return
            
        k_linear = np.linspace(0, self.k_max, self.num_points)
        k_log = np.logspace(-3, np.log10(max(1.0, self.k_max)), self.num_points // 2)
        k_merged = np.unique(np.sort(np.concatenate(([0.0], k_log, k_linear))))
        self.k_values = k_merged
        
        num_branches = self.n
        branches = [[] for _ in range(num_branches)]
        prev_roots = np.copy(self.open_poles)
        
        for idx_b in range(num_branches):
            branches[idx_b].append(prev_roots[idx_b])
            
        for k in self.k_values[1:]:
            # Equação característica: Den(s) + K*Num(s) = 0
            char_poly = self.den + (self.num * k)
            current_roots = char_poly.roots()
            
            if len(current_roots) < num_branches:
                diff = num_branches - len(current_roots)
                current_roots = np.concatenate((current_roots, prev_roots[-diff:]))
                
            matched_indices = []
            available = list(range(len(current_roots)))
            ordered_roots = [None] * num_branches
            
            for b in range(num_branches):
                p_prev = prev_roots[b]
                best_idx = None
                best_dist = float('inf')
                for cand_idx in available:
                    dist = abs(current_roots[cand_idx] - p_prev)
                    if dist < best_dist:
                        best_dist = dist
                        best_idx = cand_idx
                if best_idx is not None:
                    ordered_roots[b] = current_roots[best_idx]
                    available.remove(best_idx)
                else:
                    ordered_roots[b] = p_prev
                    
            for b in range(num_branches):
                branches[b].append(ordered_roots[b])
            prev_roots = ordered_roots

        self.branches = branches

        # Raízes em K atual
        curr_poly = self.den + (self.num * self.current_k)
        self.current_closed_loop_poles = curr_poly.roots().tolist()

    def _analyze(self):
        self._calculate_asymptotes()
        self._calculate_breakaway_points()
        self._trace_branches()

    def get_plot_data(self) -> Dict[str, Any]:
        branch_data = []
        for b_idx, b_pts in enumerate(self.branches):
            pts_real = [float(p.real) for p in b_pts]
            pts_imag = [float(p.imag) for p in b_pts]
            branch_data.append({
                "id": b_idx,
                "real": pts_real,
                "imag": pts_imag
            })
            
        return {
            "open_poles": [{"real": float(p.real), "imag": float(p.imag)} for p in self.open_poles],
            "open_zeros": [{"real": float(z.real), "imag": float(z.imag)} for z in self.open_zeros],
            "closed_poles": [{"real": float(cp.real), "imag": float(cp.imag)} for cp in self.current_closed_loop_poles],
            "current_k": self.current_k,
            "branches": branch_data,
            "centroid": self.centroid,
            "asymptote_angles": self.asymptote_angles,
            "num_asymptotes": self.num_asymptotes,
            "breakaway_points": self.breakaway_points
        }
