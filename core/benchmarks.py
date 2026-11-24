from typing import Dict, Any
from core.polynomial import Polynomial

BENCHMARKS: Dict[str, Dict[str, Any]] = {
    "sistema_a": {
        "id": "sistema_a",
        "name": "Sistema A (Padrão - 3ª Ordem Estável)",
        "category": "Estável em Malha Aberta",
        "description": "Sistema clássico estável de terceira ordem com polos em s = -1, -2, -3. "
                       "Ilustra o comportamento canônico de estabilidade absoluta e relativa com margens de ganho e fase finitas.",
        "num": [1.0],
        "den": [1.0, 6.0, 11.0, 6.0], # (s+1)(s+2)(s+3) = s^3 + 6s^2 + 11s + 6
        "default_k": 20.0,
        "tau": 0.0,
        "k_crit": 60.0,
        "open_poles": [-1.0, -2.0, -3.0],
        "open_zeros": [],
        "context": "Ogata (2010, Exemplo 5-18) e Nise (2017, Exemplo 6.3). "
                   "O sistema é estável em malha fechada para 0 < K < 60."
    },
    "sistema_b": {
        "id": "sistema_b",
        "name": "Sistema B (Instável em Malha Aberta)",
        "category": "Planta Instável (P = 1)",
        "description": "Modela sistemas naturalmente instáveis como o pêndulo invertido ou levitação magnética. "
                       "Possui um polo instável em s = +1 (P = 1). Exige envoltório anti-horário (N = -1) em torno de (-1, 0) para estabilidade.",
        "num": [1.0],
        "den": [1.0, 6.0, 3.0, -10.0], # (s - 1)(s + 2)(s + 5) = s^3 + 6s^2 + 3s - 10
        "default_k": 18.0,
        "tau": 0.0,
        "k_crit_low": 10.0,
        "k_crit_high": 28.0,
        "open_poles": [1.0, -2.0, -5.0],
        "open_zeros": [],
        "context": "Nise (2017, Cap. 10) e Ogata (2010, Cap. 7). "
                   "Estável em malha fechada exclusivamente na faixa 10 < K < 28."
    },
    "sistema_c": {
        "id": "sistema_c",
        "name": "Sistema C (Fase Não-Mínima)",
        "category": "Zero no Semiplano Direito",
        "description": "Sistema com zero no semiplano direito (s = +2). Apresenta atraso de fase adicional severo "
                       "e resposta ao degrau com undershoot (resposta inicial na direção contrária ao degrau).",
        "num": [1.0, -2.0], # s - 2
        "den": [1.0, 9.0, 23.0, 15.0], # (s+1)(s+3)(s+5) = s^3 + 9s^2 + 23s + 15
        "default_k": 3.0,
        "tau": 0.0,
        "k_crit": 7.5,
        "open_poles": [-1.0, -3.0, -5.0],
        "open_zeros": [2.0],
        "context": "Åström & Murray (2008, Seção 9.2) e Nise (2017, Cap. 13). "
                   "Zeros de fase não-mínima impõem limites fundamentais de desempenho no controle por realimentação."
    },
    "sistema_d": {
        "id": "sistema_d",
        "name": "Sistema D (Atraso Puro de Transporte)",
        "category": "Sistemas Controlados via Rede (NCS)",
        "description": "Sistema com atraso puro e^(-tau * s) com tau = 0.5s. O atraso introduz defasagem infinita "
                       "conforme w -> inf, sem alterar o módulo. Demonstra a superioridade do critério exato de Nyquist sobre a aproximação de Padé.",
        "num": [1.0],
        "den": [1.0, 3.0, 2.0], # (s+1)(s+2) = s^2 + 3s + 2
        "default_k": 2.5,
        "tau": 0.5,
        "open_poles": [-1.0, -2.0],
        "open_zeros": [],
        "context": "Åström & Murray (2008, Cap. 9) e Ogata (2010, Seção 7-10). "
                   "Em sistemas em rede (NCS), o atraso de latência degrada drasticamente a margem de fase."
    }
}

def get_benchmark(benchmark_id: str) -> Dict[str, Any]:
    return BENCHMARKS.get(benchmark_id, BENCHMARKS["sistema_a"])
