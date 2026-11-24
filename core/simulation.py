from typing import Dict, Any, Tuple, Optional
import numpy as np
from core.polynomial import Polynomial

class StepResponseSimulator:
    def __init__(self, 
                 num: Polynomial, 
                 den: Polynomial, 
                 gain: float = 1.0, 
                 tau: float = 0.0, 
                 t_final: float = 10.0, 
                 num_steps: int = 1000):
        self.num = num * gain
        self.den = den
        self.gain = float(gain)
        self.tau = max(0.0, float(tau))
        self.t_final = float(t_final)
        self.num_steps = num_steps
        
        self.t = np.linspace(0, self.t_final, self.num_steps)
        self.y = np.zeros(self.num_steps)
        
        self.rise_time: Optional[float] = None
        self.peak_time: Optional[float] = None
        self.peak_value: Optional[float] = None
        self.overshoot: Optional[float] = None
        self.settling_time: Optional[float] = None
        self.steady_state: Optional[float] = None
        
        self._simulate()
        self._compute_metrics()

    def _simulate(self):
        d_coeffs = np.real(self.den.coeffs)
        n = len(d_coeffs) - 1
        
        if n <= 0:
            self.y = np.ones(self.num_steps)
            return
            
        a0 = d_coeffs[0]
        a_norm = d_coeffs / a0
        
        n_coeffs = np.real(self.num.coeffs)
        if len(n_coeffs) < n + 1:
            n_pad = np.pad(n_coeffs, (n + 1 - len(n_coeffs), 0))
        else:
            n_pad = n_coeffs[-(n + 1):]
        b_norm = n_pad / a0
        
        d0 = b_norm[0]
        b_prime = b_norm[1:] - d0 * a_norm[1:]
        
        # Forma Canônica Controlável: dx/dt = A*x + B*u, y = C*x + D*u
        A = np.zeros((n, n), dtype=np.float64)
        for i in range(n - 1):
            A[i, i + 1] = 1.0
        A[n - 1, :] = -a_norm[1:][::-1]
        
        B = np.zeros((n, 1), dtype=np.float64)
        B[n - 1, 0] = 1.0
        
        C = b_prime[::-1].reshape(1, n)
        
        dt = self.t_final / (self.num_steps - 1)
        delay_steps = int(round(self.tau / dt)) if self.tau > 0 else 0
        
        x = np.zeros((n, 1), dtype=np.float64)
        delay_buffer = np.zeros(max(1, delay_steps + 1))
        
        def f_dot(state, u_val):
            return A @ state + B * u_val

        for i in range(self.num_steps):
            cx_val = float(np.squeeze(C @ x))
            if delay_steps == 0:
                # u = r - y = (1 - C*x) / (1 + d0)
                denom_feed = 1.0 + d0
                u = (1.0 - cx_val) / denom_feed if abs(denom_feed) > 1e-9 else 0.0
                y_curr = cx_val + d0 * u
            else:
                y_delayed = delay_buffer[-delay_steps]
                u = 1.0 - y_delayed
                y_curr = cx_val + d0 * u
                
            self.y[i] = y_curr
            
            if delay_steps > 0:
                delay_buffer = np.roll(delay_buffer, -1)
                delay_buffer[-1] = y_curr
                
            # RK4: x_{k+1} = x_k + (dt/6) * (k1 + 2*k2 + 2*k3 + k4)
            if i < self.num_steps - 1:
                k1 = f_dot(x, u)
                k2 = f_dot(x + 0.5 * dt * k1, u)
                k3 = f_dot(x + 0.5 * dt * k2, u)
                k4 = f_dot(x + dt * k3, u)
                x = x + (dt / 6.0) * (k1 + 2.0 * k2 + 2.0 * k3 + k4)
                
                if np.any(np.abs(x) > 1e6):
                    self.y[i+1:] = np.sign(y_curr) * 1e6
                    break

    def _compute_metrics(self):
        if np.any(np.isnan(self.y)) or np.any(np.abs(self.y) >= 1e5):
            self.steady_state = None
            self.overshoot = None
            return

        last_samples = max(5, int(0.05 * self.num_steps))
        y_ss = float(np.mean(self.y[-last_samples:]))
        self.steady_state = y_ss
        
        if abs(y_ss) < 1e-4:
            return
            
        idx_peak = int(np.argmax(self.y))
        y_peak = float(self.y[idx_peak])
        self.peak_value = y_peak
        self.peak_time = float(self.t[idx_peak])
        
        # %OS = ((y_peak - y_ss) / y_ss) * 100
        if y_peak > y_ss:
            self.overshoot = float(((y_peak - y_ss) / y_ss) * 100.0)
        else:
            self.overshoot = 0.0

        # tr: 10% a 90% de y_ss
        val_10 = 0.1 * y_ss
        val_90 = 0.9 * y_ss
        idx_10 = np.where(self.y >= val_10)[0]
        idx_90 = np.where(self.y >= val_90)[0]
        
        if len(idx_10) > 0 and len(idx_90) > 0 and idx_90[0] > idx_10[0]:
            self.rise_time = float(self.t[idx_90[0]] - self.t[idx_10[0]])

        # ts (faixa de 2% de y_ss)
        band = 0.02 * abs(y_ss)
        outside = np.where(np.abs(self.y - y_ss) > band)[0]
        if len(outside) > 0 and outside[-1] < self.num_steps - 1:
            self.settling_time = float(self.t[outside[-1]])
        elif len(outside) == 0:
            self.settling_time = 0.0
        else:
            self.settling_time = None

    def get_plot_data(self) -> Dict[str, Any]:
        return {
            "time": [float(val) for val in self.t],
            "response": [float(val) for val in self.y],
            "rise_time": self.rise_time,
            "peak_time": self.peak_time,
            "peak_value": self.peak_value,
            "overshoot": self.overshoot,
            "settling_time": self.settling_time,
            "steady_state": self.steady_state
        }
