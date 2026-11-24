"""
Script facilitador para execução e testes do projeto Controle_AED.
"""

import sys
import os
import unittest

def run_tests():
    """Executa a suíte de testes unitários."""
    print("  Executando Suíte de Testes Unitários ")
    print("==================================================")
    loader = unittest.TestLoader()
    start_dir = os.path.join(os.path.dirname(__file__), "tests")
    suite = loader.discover(start_dir)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    sys.exit(not result.wasSuccessful())

def run_server(port=5000):
    """Inicia o servidor web Flask."""
    from app import app
    print("  Controle Dinâmico Iniciado")
    print(f"  Acesse em: http://127.0.0.1:{port}")
    print("  Pressione Ctrl+C para encerrar")
    print("==================================================")
    app.run(debug=True, host="0.0.0.0", port=port)

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] in ["test", "tests"]:
        run_tests()
    else:
        run_server()
