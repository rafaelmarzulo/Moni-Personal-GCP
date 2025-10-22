#!/usr/bin/env python3
"""
Script de migração para adicionar colunas faltantes na tabela avaliacoes
"""
import os
import sys
from sqlalchemy import create_engine, text, Column, Text
from sqlalchemy.orm import sessionmaker
import traceback

# Importar configurações do projeto
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from database import engine, SessionLocal

def migrate_database():
    """Inicializa o banco e adiciona as colunas faltantes na tabela avaliacoes"""
    try:
        print("🔄 Iniciando migração do banco de dados...")

        # Primeiro, criar todas as tabelas se não existirem
        from models import Base
        print("📋 Criando tabelas se necessário...")
        Base.metadata.create_all(bind=engine)
        print("✅ Tabelas criadas/verificadas")

        # Conectar ao banco
        with engine.connect() as connection:
            print("📋 Verificando tipo de banco de dados...")

            # Detectar se é SQLite ou PostgreSQL
            try:
                # Tentar comando PostgreSQL
                result = connection.execute(text("SELECT version()"))
                db_version = result.fetchone()[0]
                is_postgresql = "PostgreSQL" in db_version
                print(f"🔍 Banco detectado: {'PostgreSQL' if is_postgresql else 'SQLite'}")
            except:
                is_postgresql = False
                print("🔍 Banco detectado: SQLite")

            # Verificar e adicionar colunas com sintaxe apropriada
            if is_postgresql:
                # PostgreSQL - usar information_schema
                print("📋 Verificando colunas com sintaxe PostgreSQL...")

                # Verificar meta_agua_melhorar
                result = connection.execute(text("""
                    SELECT column_name
                    FROM information_schema.columns
                    WHERE table_name='avaliacoes' AND column_name='meta_agua_melhorar'
                """))
                if not result.fetchone():
                    print("➕ Adicionando coluna meta_agua_melhorar...")
                    connection.execute(text("ALTER TABLE avaliacoes ADD COLUMN meta_agua_melhorar TEXT"))
                    print("✅ Coluna meta_agua_melhorar adicionada")
                else:
                    print("ℹ️  Coluna meta_agua_melhorar já existe")

                # Verificar rotina_treino
                result = connection.execute(text("""
                    SELECT column_name
                    FROM information_schema.columns
                    WHERE table_name='avaliacoes' AND column_name='rotina_treino'
                """))
                if not result.fetchone():
                    print("➕ Adicionando coluna rotina_treino...")
                    connection.execute(text("ALTER TABLE avaliacoes ADD COLUMN rotina_treino TEXT"))
                    print("✅ Coluna rotina_treino adicionada")
                else:
                    print("ℹ️  Coluna rotina_treino já existe")

            else:
                # SQLite - usar PRAGMA
                print("📋 Verificando colunas com sintaxe SQLite...")

                result = connection.execute(text("PRAGMA table_info(avaliacoes)"))
                existing_columns = [row[1] for row in result.fetchall()]
                print(f"📋 Colunas existentes: {existing_columns}")

                # Adicionar meta_agua_melhorar se não existir
                if 'meta_agua_melhorar' not in existing_columns:
                    print("➕ Adicionando coluna meta_agua_melhorar...")
                    connection.execute(text("ALTER TABLE avaliacoes ADD COLUMN meta_agua_melhorar TEXT"))
                    print("✅ Coluna meta_agua_melhorar adicionada")
                else:
                    print("ℹ️  Coluna meta_agua_melhorar já existe")

                # Adicionar rotina_treino se não existir
                if 'rotina_treino' not in existing_columns:
                    print("➕ Adicionando coluna rotina_treino...")
                    connection.execute(text("ALTER TABLE avaliacoes ADD COLUMN rotina_treino TEXT"))
                    print("✅ Coluna rotina_treino adicionada")
                else:
                    print("ℹ️  Coluna rotina_treino já existe")

            # Commit das mudanças
            connection.commit()
            print("🎉 Migração concluída com sucesso!")

            # Verificar estrutura final
            print("\n📊 Verificando estrutura final da tabela:")
            if is_postgresql:
                result = connection.execute(text("""
                    SELECT column_name, data_type, is_nullable
                    FROM information_schema.columns
                    WHERE table_name='avaliacoes'
                    ORDER BY ordinal_position
                """))
                for row in result:
                    print(f"  - {row[0]} ({row[1]}) {'NULL' if row[2] == 'YES' else 'NOT NULL'}")
            else:
                result = connection.execute(text("PRAGMA table_info(avaliacoes)"))
                for row in result.fetchall():
                    print(f"  - {row[1]} ({row[2]}) {'NULL' if row[3] == 0 else 'NOT NULL'}")

    except Exception as e:
        print(f"💥 Erro durante migração: {e}")
        print(f"📋 Detalhes: {traceback.format_exc()}")
        return False

    return True

if __name__ == "__main__":
    print("🚀 Executando migração do banco de dados MoniPersonal")
    success = migrate_database()

    if success:
        print("✅ Migração executada com sucesso!")
        sys.exit(0)
    else:
        print("❌ Falha na migração!")
        sys.exit(1)