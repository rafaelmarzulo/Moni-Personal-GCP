from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# Para desenvolvimento/teste rápido, usar SQLite
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///./monipersonal.db"
)

# Debug: log da DATABASE_URL (mascarar senha)
print(f"🔍 DATABASE_URL: {DATABASE_URL[:50]}...")
print(f"🔍 Is PostgreSQL: {DATABASE_URL.startswith('postgresql')}")

# Se for PostgreSQL na produção
if DATABASE_URL.startswith("postgresql"):
    print("✅ Usando PostgreSQL (Supabase)")

    # Configuração específica para Supabase
    engine = create_engine(
        DATABASE_URL,
        echo=False,
        pool_size=3,  # Reduzir para Free Tier
        max_overflow=5,
        pool_pre_ping=True,
        pool_recycle=3600,  # 1 hora
        connect_args={
            "sslmode": "require",
            "connect_timeout": 30,
            "application_name": "monipersonal-api",
            "options": "-c statement_timeout=30000"  # 30 segundos
        }
    )
else:
    # SQLite
    print("⚠️ Usando SQLite (fallback)")
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        echo=False
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# Dependency para obter sessão do banco
def get_db():
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        print(f"❌ Erro na sessão do banco: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()