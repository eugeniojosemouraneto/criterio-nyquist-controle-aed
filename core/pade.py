import math
from typing import Tuple
import numpy as np
from core.polynomial import Polynomial

def pade_approximation(tau: float, order: int = 1) -> Tuple[Polynomial, Polynomial]:
    if tau <= 0 or order < 1:
        return Polynomial([1.0]), Polynomial([1.0])
        
    num_coeffs = np.zeros(order + 1, dtype=np.float64)
    den_coeffs = np.zeros(order + 1, dtype=np.float64)
    
    fact_2n = math.factorial(2 * order)
    fact_n = math.factorial(order)
    
    # c_k = (2N - k)! * N! / ((2N)! * k! * (N - k)!)
    for k in range(order + 1):
        c_k = (math.factorial(2 * order - k) * fact_n) / (fact_2n * math.factorial(k) * math.factorial(order - k))
        power_index = order - k
        num_coeffs[power_index] = c_k * ((-tau) ** k)
        den_coeffs[power_index] = c_k * ((tau) ** k)
        
    return Polynomial(num_coeffs), Polynomial(den_coeffs)

def apply_delay_pade(num: Polynomial, den: Polynomial, tau: float, order: int = 1) -> Tuple[Polynomial, Polynomial]:
    if tau <= 0:
        return num, den
    p_num, p_den = pade_approximation(tau, order)
    return num * p_num, den * p_den
