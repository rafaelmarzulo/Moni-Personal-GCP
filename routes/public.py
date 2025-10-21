"""
Rotas públicas (health checks, ping, readiness, etc.)
"""
from fastapi import APIRouter, Request, Depends
from sqlalchemy.orm import Session

from database import get_db
from app.core.config import APP_NAME, APP_VERSION
from app.utils.datetime_utils import now_sao_paulo


# Configurar router
router = APIRouter()


@router.get("/health")
async def health_check(request: Request):
    """Health check endpoint para DigitalOcean App Platform"""
    return {
        "status": "healthy",
        "timestamp": now_sao_paulo().isoformat(),
        "service": "monipersonal-api",
        "version": APP_VERSION
    }


@router.get("/ping")
async def ping(request: Request):
    """Endpoint simples de ping"""
    return {"status": "ok", "message": "pong"}


@router.get("/readiness")
async def readiness_check(request: Request, db: Session = Depends(get_db)):
    """Verifica se a aplicação está pronta (inclui verificação do banco)"""
    try:
        # Teste simples de conexão com banco usando text()
        from sqlalchemy import text
        db.execute(text("SELECT 1"))
        return {
            "status": "ready",
            "timestamp": now_sao_paulo().isoformat(),
            "database": "connected",
            "service": "monipersonal-api"
        }
    except Exception as e:
        return {
            "status": "not_ready",
            "timestamp": now_sao_paulo().isoformat(),
            "database": "disconnected",
            "error": str(e),
            "service": "monipersonal-api"
        }