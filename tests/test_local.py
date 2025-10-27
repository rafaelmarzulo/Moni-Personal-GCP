#!/usr/bin/env python3
"""
Script para testar a aplicação localmente
"""
import os
import sys

def setup_environment():
    """Configura o ambiente para teste local"""
    # Usar configuração local
    os.environ['DATABASE_URL'] = 'sqlite:///./monipersonal_test.db'
    os.environ['DEBUG'] = 'true'
    os.environ['ENVIRONMENT'] = 'development'

    print("🔧 Ambiente configurado para teste local")
    print(f"📁 Diretório: {os.getcwd()}")
    print(f"🗃️ Banco: SQLite (monipersonal_test.db)")

def create_tables():
    """Cria as tabelas do banco de dados"""
    try:
        from database import Base, engine
        from models import Aluno, Avaliacao  # Importar todos os modelos

        print("📋 Criando tabelas...")
        Base.metadata.create_all(bind=engine)
        print("✅ Tabelas criadas com sucesso!")
        return True
    except Exception as e:
        print(f"❌ Erro ao criar tabelas: {e}")
        return False

def create_test_data():
    """Cria dados de teste"""
    try:
        from database import SessionLocal
        from models import Aluno, Avaliacao
        from datetime import datetime, date

        db = SessionLocal()

        # Verificar se já existem dados
        if db.query(Aluno).count() > 0:
            print("📊 Dados de teste já existem")
            db.close()
            return True

        # Criar aluno de teste
        aluno_teste = Aluno(
            nome="João Silva",
            email="joao@teste.com",
            senha="$2b$12$KQQhJ2dPZhIhEhYlKQkMX.X1..XXX",  # senha: teste123
            ativo=True
        )

        db.add(aluno_teste)
        db.commit()

        # Criar algumas avaliações de teste
        avaliacoes = [
            Avaliacao(
                nome="João Silva",
                peso="75.5",
                altura="175",
                peito="95.0",
                cintura="80.0",
                quadril="85.0",
                braco_direito="30.0",
                braco_esquerdo="30.0",
                coxa_direita="55.0",
                coxa_esquerda="55.0",
                alimentacao="Boa alimentação",
                melhorias="exercicios,dieta",
                pedido_especial="Foco em força",
                rotina_treino="3x por semana",
                sugestao_geral="Continue assim!",
                data=datetime(2024, 9, 1),
                peso_numerico=75.5,
                imc=24.7
            ),
            Avaliacao(
                nome="João Silva",
                peso="77.0",
                altura="175",
                peito="96.0",
                cintura="79.0",
                quadril="86.0",
                braco_direito="31.0",
                braco_esquerdo="31.0",
                coxa_direita="56.0",
                coxa_esquerda="56.0",
                alimentacao="Melhorou muito",
                melhorias="exercicios,resistencia",
                pedido_especial="Manter foco",
                rotina_treino="4x por semana",
                sugestao_geral="Excelente progresso!",
                data=datetime(2024, 9, 24),
                peso_numerico=77.0,
                imc=25.1
            )
        ]

        for avaliacao in avaliacoes:
            db.add(avaliacao)

        db.commit()
        db.close()

        print("🎯 Dados de teste criados:")
        print("   - Aluno: João Silva (joao@teste.com)")
        print("   - 2 avaliações com progresso")
        print("   - Login: joao@teste.com / teste123")

        return True

    except Exception as e:
        print(f"❌ Erro ao criar dados de teste: {e}")
        return False

def start_server():
    """Inicia o servidor de desenvolvimento"""
    try:
        import uvicorn
        print("\n🚀 Iniciando servidor de desenvolvimento...")
        print("📱 URLs disponíveis:")
        print("   - Aplicação: http://localhost:8000")
        print("   - Documentação API: http://localhost:8000/docs")
        print("\n👤 Login de teste:")
        print("   - Email: joao@teste.com")
        print("   - Senha: teste123")
        print("\n🛑 Para parar o servidor: Ctrl+C")
        print("\n" + "="*50)

        uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

    except KeyboardInterrupt:
        print("\n🛑 Servidor parado pelo usuário")
    except Exception as e:
        print(f"❌ Erro ao iniciar servidor: {e}")

if __name__ == "__main__":
    print("🔥 MoniPersonal - Teste Local")
    print("="*40)

    # Setup environment
    setup_environment()

    # Create database tables
    if not create_tables():
        sys.exit(1)

    # Create test data
    if not create_test_data():
        print("⚠️  Aviso: Não foi possível criar dados de teste, mas continuando...")

    # Start server
    start_server()