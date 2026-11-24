from typing import List, Dict, Any
import numpy as np
from core.polynomial import Polynomial

class RouthHurwitz:
    def __init__(self, polynomial: Polynomial, epsilon: float = 1e-8):
        coeffs = np.real(polynomial.coeffs)
        if len(coeffs) > 1 and coeffs[0] < 0:
            coeffs = -coeffs
            
        self.poly = Polynomial(coeffs)
        self.degree = self.poly.degree
        self.epsilon = epsilon
        
        self.table: List[List[float]] = []
        self.row_labels: List[str] = []
        self.special_cases: List[str] = []
        self.auxiliary_polynomials: List[Dict[str, Any]] = []
        self.first_column: List[float] = []
        self.sign_changes = 0
        self.num_rhp_poles = 0
        self.is_stable = False
        self.is_marginally_stable = False
        self.verdict = ""
        
        self._compute_table()

    def _compute_table(self):
        n = self.degree
        if n < 1:
            self.verdict = "Polinômio de grau zero."
            return

        coeffs = self.poly.coeffs
        num_cols = (n + 2) // 2
        table = [[0.0 for _ in range(num_cols)] for _ in range(n + 1)]
        row_labels = [f"s^{n - i}" for i in range(n + 1)]

        # Linha s^n: a_n, a_{n-2}, a_{n-4}, ...
        c_idx = 0
        for j in range(0, n + 1, 2):
            table[0][c_idx] = float(coeffs[j])
            c_idx += 1
            
        # Linha s^(n-1): a_{n-1}, a_{n-3}, a_{n-5}, ...
        c_idx = 0
        for j in range(1, n + 1, 2):
            table[1][c_idx] = float(coeffs[j])
            c_idx += 1

        for i in range(2, n + 1):
            power = n - i
            prev1 = table[i - 1]
            prev2 = table[i - 2]
            pivot = prev1[0]

            if abs(pivot) < 1e-12:
                is_row_all_zero = all(abs(val) < 1e-12 for val in prev1)
                
                if is_row_all_zero:
                    # Caso Especial 2: Linha nula -> derivada do polinomio auxiliar dA(s)/ds
                    aux_power = power + 1
                    self.special_cases.append(f"Linha inteira nula em s^{power + 1}: uso do polinomio auxiliar A(s)")

                    aux_coeffs = []
                    curr_pow = aux_power + 1
                    for c_val in prev2:
                        if curr_pow >= 0:
                            aux_coeffs.append(c_val)
                            if curr_pow > 0:
                                aux_coeffs.append(0.0)
                            curr_pow -= 2
                    
                    aux_poly = Polynomial(aux_coeffs)
                    d_aux = aux_poly.derivative()
                    self.auxiliary_polynomials.append({
                        "power": aux_power + 1,
                        "polynomial": aux_poly.to_string(),
                        "derivative": d_aux.to_string()
                    })

                    d_coeffs = d_aux.coeffs
                    new_prev1 = [float(d_coeffs[idx_d]) for idx_d in range(0, len(d_coeffs), 2)]
                    while len(new_prev1) < num_cols:
                        new_prev1.append(0.0)
                        
                    table[i - 1] = new_prev1[:num_cols]
                    prev1 = table[i - 1]
                    pivot = prev1[0]
                else:
                    # Caso Especial 1: Primeiro elemento zero -> substituicao por epsilon > 0
                    self.special_cases.append(f"Pivo nulo em s^{power + 1}: substituicao por epsilon = {self.epsilon:g}")
                    prev1[0] = self.epsilon
                    pivot = self.epsilon

            # b_k = (pivot * prev2[k+1] - prev2[0] * prev1[k+1]) / pivot
            for j in range(num_cols - 1):
                numerator = prev1[0] * prev2[j + 1] - prev2[0] * prev1[j + 1]
                table[i][j] = float(numerator / pivot)

        self.table = table
        self.row_labels = row_labels
        self.first_column = [row[0] for row in table]
        
        # Contagem de variacoes de sinal na 1a coluna (numero de polos no semiplano direito)
        signs = [1 if val >= 0 else -1 for val in self.first_column]
        self.sign_changes = sum(1 for k in range(len(signs) - 1) if signs[k] * signs[k + 1] < 0)
        self.num_rhp_poles = self.sign_changes

        if len(self.auxiliary_polynomials) > 0:
            if self.sign_changes == 0:
                self.is_marginally_stable = True
                self.is_stable = False
                self.verdict = "Sistema Marginalmente Estavel: raizes puramente imaginarias identificadas via A(s)."
            else:
                self.is_stable = False
                self.verdict = f"Sistema Instavel: {self.sign_changes} polo(s) no semiplano direito."
        else:
            if self.sign_changes == 0:
                self.is_stable = True
                self.verdict = f"Sistema Estavel: todos os {n} polos no semiplano esquerdo."
            else:
                self.is_stable = False
                self.verdict = f"Sistema Instavel: {self.sign_changes} polo(s) no semiplano direito."

    def to_dict(self) -> Dict[str, Any]:
        formatted_table = []
        for label, row in zip(self.row_labels, self.table):
            formatted_row = []
            for val in row:
                if abs(val) < 1e-9:
                    formatted_row.append("0.0000")
                elif abs(val - self.epsilon) < 1e-11:
                    formatted_row.append(f"ε ({self.epsilon:g})")
                else:
                    formatted_row.append(f"{val:.4f}")
            formatted_table.append({
                "label": label,
                "values": formatted_row,
                "first_col_sign": "+" if row[0] >= 0 else "-"
            })

        return {
            "polynomial": self.poly.to_string(),
            "degree": self.degree,
            "table": formatted_table,
            "first_column": [f"{v:.4f}" for v in self.first_column],
            "sign_changes": self.sign_changes,
            "num_rhp_poles": self.num_rhp_poles,
            "is_stable": self.is_stable,
            "is_marginally_stable": self.is_marginally_stable,
            "special_cases": self.special_cases,
            "auxiliary_polynomials": self.auxiliary_polynomials,
            "verdict": self.verdict
        }
