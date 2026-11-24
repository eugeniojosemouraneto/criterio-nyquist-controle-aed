# Análise Computacional e Comparativa de Critérios de Estabilidade em Sistemas Dinâmicos

> **Projeto de Pesquisa Aplicada em Teoria de Controle e Métodos Computacionais**  
> **Público-Alvo:** Graduação em Ciência da Computação (CC) e Engenharia da Computação (EC).

---

## 📌 Visão Geral do Projeto

Este projeto implementa uma plataforma computacional e visual completa para análise de estabilidade em sistemas lineares invariantes no tempo (LIT), construída **do zero em Python, CSS e HTML**, sem recorrer a bibliotecas prontas de controle (como `python-control` ou `scipy.signal`).

A plataforma realiza a comparação teórica, geométrica e numérica entre quatro abordagens clássicas:
1. **Critério de Estabilidade de Nyquist**: Mapeamento conforme no plano complexo polar baseado no Princípio do Argumento de Cauchy ($Z = N + P$), cálculo do número de envoltórios (*winding number*) e tratamento analítico **exato** de termos de atraso puro de transporte ($e^{-\tau s}$).
2. **Critério Algébrico de Routh-Hurwitz**: Construção formal da tabela de determinantes de Routh, incluindo o tratamento automatizado dos casos especiais:
   - **Caso Especial 1:** Primeiro elemento nulo da linha (método do $\epsilon > 0$).
   - **Caso Especial 2:** Linha inteira de zeros (construção e diferenciação do polinômio auxiliar $A(s)$).
3. **Lugar Geométrico das Raízes (*Root Locus*)**: Traçado contínuo das trajetórias dos polos para ganho $K \ge 0$, determinação analítica de assíntotas (centroide $\sigma_a$ e ângulos $\phi_a$), pontos de dispersão/junção (*breakaway/break-in*) e emparelhamento de ramos.
4. **Diagrama de Bode**: Avaliação das respostas em frequência de magnitude (dB) e fase (graus), com extração das frequências críticas de cruzamento ($\omega_{gc}, \omega_{pc}$) e margens de estabilidade relativa (Margem de Ganho e Margem de Fase).
5. **Simulação Temporal ao Degrau**: Resposta temporal $y(t)$ integrada numericamente via Runge-Kutta de 4ª ordem (RK4) com buffer contínuo de retardo para atraso puro.
6. **Comparador de Atraso Exato vs. Padé**: Demonstração empírica das perdas de precisão decorrentes das aproximações racionais de Padé de ordens [1/1] e [2/2].
7. **Validação Cruzada (Fase 3)**: Módulo de confronto direto com as bibliotecas industriais `python-control` e `SciPy`, comprovando a concordância exata dos resultados produzidos pelo código próprio com erro relativo $< 0.05\%$.

---

## 🚀 Estrutura de Páginas da Aplicação

1. **Dashboard Interativo / Workbench (`/`)**:
   - Interface visual e interativa com sliders de ganho $K$, tempo de atraso $\tau$ e coeficientes polinomiais.
   - Atualização dinâmica em tempo real dos diagramas de Nyquist, Routh-Hurwitz, Root Locus, Bode e resposta ao degrau.
   - Seletor de um clique para os 4 sistemas de benchmark.
2. **Página de Benchmarks (`/benchmarks`)**:
   - Detalhamento matemático dos 4 sistemas de teste da especificação:
     - **Sistema A (Padrão):** 3ª ordem estável em malha aberta ($P = 0, K_{crit} = 60$).
     - **Sistema B (Instável em Malha Aberta):** Planta instável ($P = 1, N = -1$, estável para $10 < K < 28$).
     - **Sistema C (Fase Não-Mínima):** Zero no semiplano direito ($s = +2$), apresentando *undershoot* temporal.
     - **Sistema D (Atraso de Transporte):** Atraso puro $e^{-\tau s}$ em malha fechada.
   - Tabela comparativa consolidada dos critérios.
3. **Laboratório de Escalabilidade e Estabilidade Numérica (`/scalability`)**:
   - Teste automatizado para escalabilidade de ordem do sistema ($n = 5, 10, 20$).
   - Medição de tempo de CPU para Routh $\mathcal{O}(n^2)$, Nyquist $\mathcal{O}(M \cdot n)$ e Root Locus $\mathcal{O}(K \cdot n^3)$.
   - Quantificação de erros de arredondamento e sensibilidade de Wilkinson ($\|c_{orig} - c_{recon}\|_2$).
4. **Página de Documentação do Código & Reprodutibilidade (`/documentacao`)**:
   - Detalhamento de cada módulo do núcleo computacional, APIs RESTful, cobertura de testes e guia de instalação.

---

## 🛠️ Instruções Claras de Reprodutibilidade

### 1. Pré-requisitos
- **Python**: Versão 3.10 ou superior (testado no Python 3.13).
- **Gerenciador de Pacotes**: `pip`.

### 2. Instalação das Dependências
No diretório raiz do projeto, instale os pacotes mínimos necessários:
```bash
pip install -r requirements.txt
```

As dependências são estritamente:
- `Flask>=3.0.0` (servidor web e rotas REST)
- `numpy>=1.24.0` (operações matriciais e vetoriais básicas)
- `pytest>=8.0.0` (suíte de testes automatizados)

### 3. Execução da Suíte de Testes Unitários
O projeto inclui **37 testes unitários e de validação cruzada automatizados** cobrindo todos os módulos do núcleo matemático, casos de singularidade de Routh, contorno e winding number de Nyquist, diagramas de Bode, aproximações de Padé, confronto direto com python-control e rotas HTTP:

```bash
# Opção A: Executar via pytest (recomendado)
pytest -v

# Opção B: Executar via unittest padrão da biblioteca do Python
python -m unittest discover tests

# Opção C: Executar via script utilitário run.py
python run.py test
```

### 4. Inicialização do Servidor Web
Inicie a aplicação com:
```bash
python app.py
# ou alternativamente:
python run.py
```

Abra o seu navegador web no endereço:
```
http://127.0.0.1:5000
```

---

## 📂 Arquitetura de Diretórios

```
Controle_AED/
├── core/                         # Núcleo algorítmico implementado do zero
│   ├── __init__.py               # Exportação das classes centrais
│   ├── polynomial.py             # Classe Polynomial (Horner, raízes via autovalores)
│   ├── routh_hurwitz.py          # Tabela de Routh (casos especiais epsilon e linha de zeros)
│   ├── nyquist.py                # Contorno de Nyquist, Winding Number de Cauchy e margens
│   ├── root_locus.py             # Lugar das Raízes (assíntotas, centroide, breakaway)
│   ├── bode.py                   # Magnitude em dB e Fase em graus (com atraso exato)
│   ├── pade.py                   # Fórmulas de aproximação racional [N/N] de Padé
│   ├── simulation.py             # Espaço de estados e integrador RK4 com delay buffer
│   ├── benchmarks.py             # Parametrização dos 4 sistemas de benchmark
│   ├── scalability.py            # Testes de ordem n = 5, 10, 20 e erros numéricos
│   └── cross_validation.py      # Validação cruzada com python-control e SciPy (Fase 3)
├── templates/                    # Templates Jinja2 (HTML)
│   ├── base.html                 # Layout padrão, navbar e KaTeX
│   ├── index.html                # Dashboard interativo com gráficos em tempo real
│   ├── benchmarks.html           # Página de análise comparativa dos 4 sistemas
│   ├── scalability.html          # Laboratório de escalabilidade n = 5, 10, 20
│   └── documentation.html        # Documentação completa do código e APIs
├── static/                       # Recursos estáticos
│   ├── css/
│   │   └── style.css             # Estilos modernos da interface e workbench
│   └── js/
│       └── app.js                # Lógica de interatividade e gráficos via Chart.js
├── tests/                        # 37 Testes unitários e de validação cruzada
│   ├── test_polynomial.py        # Testes de álgebra de polinômios e raízes
│   ├── test_routh_hurwitz.py     # Testes de Routh e casos de singularidade
│   ├── test_nyquist.py           # Testes de Nyquist, winding number e estabilidade
│   ├── test_root_locus.py        # Testes do Lugar das Raízes e assíntotas
│   ├── test_bode_and_delay.py    # Testes de Bode, Padé e simulação RK4
│   ├── test_benchmarks.py        # Testes de integridade dos 4 benchmarks
│   ├── test_cross_validation.py  # Testes de validação cruzada com python-control
│   └── test_api.py               # Testes de integração das rotas do Flask
├── app.py                        # Servidor Flask e rotas da API REST
├── requirements.txt              # Especificação de dependências
├── pytest.ini                    # Configuração de descoberta do pytest
├── run.py                        # Script facilitador de execução e testes
└── README.md                     # Documentação e instruções de reprodutibilidade
```

---

## 📚 Bibliografia Utilizada

Todo o embasamento teórico e as formulações matemáticas foram elaborados estritamente com base nas três obras fundamentais recomendadas:

1. **OGATA, Katsuhiko.** *Engenharia de Controle Moderno*. 5ª ed. São Paulo: Pearson, 2010.
2. **NISE, Norman S.** *Engenharia de Sistemas de Controle*. 7ª ed. Rio de Janeiro: LTC, 2017.
3. **ÅSTRÖM, Karl J.; MURRAY, Richard M.** *Feedback Systems: An Introduction for Scientists and Engineers*. Princeton: Princeton University Press, 2008.

---

## 📄 Licença
Código-fonte aberto para fins educacionais e de pesquisa acadêmica no âmbito das disciplinas de Controle Dinâmico e Algoritmos Numéricos em Ciência e Engenharia da Computação.
