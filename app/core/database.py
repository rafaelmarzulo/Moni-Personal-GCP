from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# Para desenvolvimento/teste rápido, usar SQLite
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "sqlite:///./monipersonal.db"
)

# Se for PostgreSQL na produção
if DATABASE_URL.startswith("postgresql"):
    engine = create_engine(DATABASE_URL, echo=False)
else:
    # SQLite
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
    finally:
        db.close()