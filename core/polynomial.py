from typing import List, Union
import numpy as np

class Polynomial:
    def __init__(self, coeffs: Union[List[float], np.ndarray, float, int]):
        if isinstance(coeffs, (int, float, complex)):
            coeffs = [coeffs]
        coeffs = np.array(coeffs, dtype=np.complex128 if any(isinstance(c, complex) for c in coeffs) else np.float64)
        
        if len(coeffs) > 1:
            first_nonzero = np.flatnonzero(np.abs(coeffs) > 1e-15)
            coeffs = coeffs[first_nonzero[0]:] if len(first_nonzero) > 0 else np.array([0.0])
        
        self.coeffs = coeffs
        self.degree = len(coeffs) - 1

    def __len__(self):
        return len(self.coeffs)

    def __repr__(self):
        return f"Polynomial({self.coeffs.tolist()})"

    def to_string(self, var: str = "s") -> str:
        if len(self.coeffs) == 0 or (len(self.coeffs) == 1 and abs(self.coeffs[0]) < 1e-12):
            return "0"

        terms = []
        n = self.degree
        for i, c in enumerate(self.coeffs):
            power = n - i
            if abs(c) < 1e-12:
                continue

            if np.iscomplex(c):
                c_str = f"({c.real:+.4g}{c.imag:+.4g}j)"
            else:
                c_val = float(c)
                if power == n:
                    c_str = f"{c_val:.4g}" if c_val != 1 or power == 0 else ""
                    if c_val == -1 and power > 0:
                        c_str = "-"
                else:
                    sign = "+" if c_val >= 0 else "-"
                    abs_val = abs(c_val)
                    c_str = f" {sign} " + (f"{abs_val:.4g}" if abs_val != 1 or power == 0 else "")

            if power == 0:
                var_str = f"{abs(float(c)):.4g}" if (i > 0 and not np.iscomplex(c)) else (f"{c:.4g}" if not np.iscomplex(c) else c_str)
                terms.append(var_str if i == 0 else f"{c_str}")
            elif power == 1:
                terms.append(f"{c_str}{var}")
            else:
                terms.append(f"{c_str}{var}^{power}")

        res = "".join(terms).strip()
        return res if res else "0"

    def evaluate(self, s: Union[complex, float, np.ndarray]) -> Union[complex, float, np.ndarray]:
        # Algoritmo de Horner: P(s) = (...((c_n * s + c_{n-1}) * s + ...) + c_0
        if isinstance(s, (list, tuple)):
            s = np.array(s)
            
        result = np.zeros_like(s, dtype=np.complex128 if (np.iscomplexobj(s) or np.iscomplexobj(self.coeffs)) else np.float64)
        for c in self.coeffs:
            result = result * s + c
        return result

    def roots(self) -> np.ndarray:
        # Raízes via autovalores da matriz companheira de Frobenius de P(s) = 0
        if self.degree < 1:
            return np.array([], dtype=np.complex128)
        if self.degree == 1:
            # c1*s + c0 = 0 => s = -c0/c1
            return np.array([-self.coeffs[1] / self.coeffs[0]], dtype=np.complex128)
        
        lead = self.coeffs[0]
        if abs(lead) < 1e-15:
            return Polynomial(self.coeffs[1:]).roots()
            
        a = self.coeffs[1:] / lead
        n = self.degree
        
        # Matriz companheira C onde det(sI - C) = a_n s^n + ... + a_0
        companion = np.zeros((n, n), dtype=np.float64 if np.all(np.isreal(self.coeffs)) else np.complex128)
        companion[0, :] = -a
        for i in range(1, n):
            companion[i, i - 1] = 1.0
            
        eigenvalues = np.linalg.eigvals(companion)
        idx = np.lexsort((eigenvalues.imag, eigenvalues.real))[::-1]
        return eigenvalues[idx]

    def derivative(self) -> 'Polynomial':
        # d/ds (c_k * s^k) = k * c_k * s^(k-1)
        if self.degree == 0:
            return Polynomial([0.0])
        n = self.degree
        d_coeffs = [self.coeffs[i] * (n - i) for i in range(n)]
        return Polynomial(d_coeffs)

    def __add__(self, other: Union['Polynomial', float, int]) -> 'Polynomial':
        if isinstance(other, (int, float, complex)):
            other = Polynomial([other])
        l1, l2 = len(self.coeffs), len(other.coeffs)
        if l1 < l2:
            c1 = np.pad(self.coeffs, (l2 - l1, 0))
            c2 = other.coeffs
        else:
            c1 = self.coeffs
            c2 = np.pad(other.coeffs, (l1 - l2, 0))
        return Polynomial(c1 + c2)

    def __radd__(self, other):
        return self.__add__(other)

    def __sub__(self, other: Union['Polynomial', float, int]) -> 'Polynomial':
        if isinstance(other, (int, float, complex)):
            other = Polynomial([other])
        return self + (-other)

    def __neg__(self) -> 'Polynomial':
        return Polynomial(-self.coeffs)

    def __mul__(self, other: Union['Polynomial', float, int]) -> 'Polynomial':
        if isinstance(other, (int, float, complex)):
            return Polynomial(self.coeffs * other)
        return Polynomial(np.convolve(self.coeffs, other.coeffs))

    def __rmul__(self, other):
        return self.__mul__(other)

    @classmethod
    def from_roots(cls, roots: List[Union[complex, float]]) -> 'Polynomial':
        # P(s) = prod(s - r_i)
        p = Polynomial([1.0])
        for r in roots:
            p = p * Polynomial([1.0, -r])
        if np.all(np.isreal(p.coeffs) | (np.abs(p.coeffs.imag) < 1e-10)):
            p = Polynomial(p.coeffs.real)
        return p
