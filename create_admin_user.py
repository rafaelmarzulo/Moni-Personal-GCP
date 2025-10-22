#!/usr/bin/env python3
"""
Script para criar usuário administrador inicial no banco de dados
"""
import os
import sys
from datetime import datetime
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

# Configurar path para importar módulos da aplicação
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Importar modelos e configurações
from app.core.database import engine, SessionLocal
from app.models import Usuario, Base
from app.services.auth_service import hash_password

def create_admin_user():
    """Cria usuário administrador inicial"""
    try:
        print("🔄 Criando usuário administrador inicial...")

        # Criar todas as tabelas se não existirem
        Base.metadata.create_all(bind=engine)

        # Criar sessão
        db = SessionLocal()

        try:
            # Verificar se admin já existe
            admin_exists = db.query(Usuario).filter(Usuario.email == "admin@monipersonal.com").first()

            if admin_exists:
                print("ℹ️  Usuário administrador já existe!")
                return True

            # Criar usuário administrador
            admin_password = "Monica@1985"  # Senha definida nas secrets
            admin_user = Usuario(
                email="admin@monipersonal.com",
                nome="Administrador",
                senha_hash=hash_password(admin_password),
                tipo="admin",
                ativo=True,
                created_at=datetime.now()
            )

            db.add(admin_user)
            db.commit()

            print("✅ Usuário administrador criado com sucesso!")
            print(f"📧 Email: admin@monipersonal.com")
            print(f"🔑 Senha: {admin_password}")

            return True

        except Exception as e:
            db.rollback()
            print(f"💥 Erro ao criar usuário: {e}")
            return False
        finally:
            db.close()

    except Exception as e:
        print(f"💥 Erro geral: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Executando criação do usuário administrador")
    success = create_admin_user()

    if success:
        print("✅ Usuário administrador criado/verificado com sucesso!")
        sys.exit(0)
    else:
        print("❌ Falha na criação do usuário administrador!")
        sys.exit(1)