#!/usr/bin/env python3
"""
Teste de ambiente de produção - Moni Personal
Valida todos os endpoints críticos antes do deploy
"""

import requests
import time
import sys
import json
from datetime import datetime


class ProductionTest:
    def __init__(self, base_url="http://127.0.0.1:8000"):
        self.base_url = base_url
        self.passed = 0
        self.failed = 0

    def log(self, message, status="INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        colors = {
            "INFO": "\033[36m",  # Cyan
            "PASS": "\033[32m",  # Green
            "FAIL": "\033[31m",  # Red
            "WARN": "\033[33m",  # Yellow
        }
        reset = "\033[0m"
        print(f"{colors.get(status, '')}{timestamp} [{status}] {message}{reset}")

    def test_endpoint(self, name, endpoint, expected_status=200, expected_content=None, allow_redirects=True):
        """Testa um endpoint específico"""
        try:
            self.log(f"Testing {name}: {endpoint}")
            response = requests.get(f"{self.base_url}{endpoint}", timeout=10, allow_redirects=allow_redirects)

            # Se esperamos um redirect, aceita múltiplos códigos de redirect
            if expected_status in [302, 303, 307] and response.status_code in [302, 303, 307]:
                expected_status = response.status_code  # Aceita qualquer redirect válido

            # Verifica status code
            if response.status_code != expected_status:
                self.log(f"❌ {name} - Status code: {response.status_code} (expected {expected_status})", "FAIL")
                self.failed += 1
                return False

            # Verifica conteúdo se fornecido
            if expected_content:
                if expected_content not in response.text:
                    self.log(f"❌ {name} - Content check failed", "FAIL")
                    self.failed += 1
                    return False

            # Se chegou até aqui, passou no teste
            self.log(f"✅ {name} - OK", "PASS")
            self.passed += 1
            return True

        except requests.exceptions.ConnectionError:
            self.log(f"❌ {name} - Connection error (server not running?)", "FAIL")
            self.failed += 1
            return False
        except requests.exceptions.Timeout:
            self.log(f"❌ {name} - Timeout", "FAIL")
            self.failed += 1
            return False
        except Exception as e:
            self.log(f"❌ {name} - Unexpected error: {str(e)}", "FAIL")
            self.failed += 1
            return False

    def test_json_endpoint(self, name, endpoint, required_fields=None):
        """Testa endpoint JSON e verifica campos obrigatórios"""
        try:
            self.log(f"Testing JSON {name}: {endpoint}")
            response = requests.get(f"{self.base_url}{endpoint}", timeout=10)

            if response.status_code != 200:
                self.log(f"❌ {name} - Status code: {response.status_code}", "FAIL")
                self.failed += 1
                return False

            # Verifica se é JSON válido
            try:
                data = response.json()
            except json.JSONDecodeError:
                self.log(f"❌ {name} - Invalid JSON response", "FAIL")
                self.failed += 1
                return False

            # Verifica campos obrigatórios
            if required_fields:
                for field in required_fields:
                    if field not in data:
                        self.log(f"❌ {name} - Missing field: {field}", "FAIL")
                        self.failed += 1
                        return False

            self.log(f"✅ {name} - JSON OK", "PASS")
            self.passed += 1
            return True

        except Exception as e:
            self.log(f"❌ {name} - Error: {str(e)}", "FAIL")
            self.failed += 1
            return False

    def run_all_tests(self):
        """Executa todos os testes de produção"""
        self.log("=== INICIANDO TESTES DE PRODUÇÃO ===")
        self.log(f"Target: {self.base_url}")

        # Health Checks (críticos para DigitalOcean)
        self.log("\n--- HEALTH CHECKS ---")
        self.test_json_endpoint("Health Check", "/health", ["status", "timestamp", "service"])
        self.test_json_endpoint("Ping", "/ping", ["status", "message"])
        self.test_json_endpoint("Readiness Check", "/readiness", ["status", "database"])

        # Endpoints principais
        self.log("\n--- ENDPOINTS PRINCIPAIS ---")
        self.test_endpoint("Root Redirect", "/", 302, allow_redirects=False)  # Should redirect
        self.test_endpoint("Login Page", "/login", 200, "MoniPersonal")

        # Teste de endpoint protegido (deve redirecionar para login)
        self.test_endpoint("Protected Admin", "/admin/alunos", 302, allow_redirects=False)  # Should redirect to login

        # Arquivos estáticos
        self.log("\n--- ASSETS ESTÁTICOS ---")
        self.test_endpoint("Favicon", "/static/favicon.png", 200)
        self.test_endpoint("Logo", "/static/img/logo-monipersonal.png", 200)

        # Relatório final
        self.log("\n=== RELATÓRIO FINAL ===")
        total_tests = self.passed + self.failed
        success_rate = (self.passed / total_tests * 100) if total_tests > 0 else 0

        self.log(f"Total de testes: {total_tests}")
        self.log(f"Passou: {self.passed}", "PASS")
        self.log(f"Falhou: {self.failed}", "FAIL" if self.failed > 0 else "INFO")
        self.log(f"Taxa de sucesso: {success_rate:.1f}%")

        if self.failed == 0:
            self.log("🎉 TODOS OS TESTES PASSARAM - PRONTO PARA DEPLOY!", "PASS")
            return True
        else:
            self.log("❌ ALGUNS TESTES FALHARAM - REVISAR ANTES DO DEPLOY", "FAIL")
            return False


def wait_for_server(base_url="http://127.0.0.1:8000", timeout=30):
    """Aguarda o servidor estar disponível"""
    print(f"⏳ Aguardando servidor em {base_url}...")
    start_time = time.time()

    while time.time() - start_time < timeout:
        try:
            response = requests.get(f"{base_url}/health", timeout=5)
            if response.status_code == 200:
                print("✅ Servidor está respondendo!")
                return True
        except:
            pass

        time.sleep(2)

    print(f"❌ Servidor não respondeu em {timeout}s")
    return False


if __name__ == "__main__":
    print("🚀 TESTE DE AMBIENTE DE PRODUÇÃO - MONI PERSONAL")
    print("=" * 60)

    # Aguarda servidor estar disponível
    if not wait_for_server():
        print("❌ Servidor não está respondendo. Inicie a aplicação primeiro:")
        print("   export DATABASE_URL='sqlite:///./monipersonal_test.db'")
        print("   source venv_production_test/bin/activate")
        print("   uvicorn main:app --host 127.0.0.1 --port 8000")
        sys.exit(1)

    # Executa testes
    tester = ProductionTest()
    success = tester.run_all_tests()

    # Exit code para scripts automatizados
    sys.exit(0 if success else 1)