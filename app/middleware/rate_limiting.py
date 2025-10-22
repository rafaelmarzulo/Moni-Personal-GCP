"""
Configuração de rate limiting para a aplicação
"""
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import FastAPI

from app.core.config import RATE_LIMITS


def setup_rate_limiting(app: FastAPI) -> Limiter:
    """
    Configura rate limiting para a aplicação FastAPI

    Returns:
        Limiter: Instância configurada do limiter
    """
    # Criar instância do limiter
    limiter = Limiter(key_func=get_remote_address)

    # Configurar handler de exceção personalizado
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    return limiter


def get_rate_limit(level: str) -> str:
    """
    Retorna o rate limit configurado para um nível específico

    Args:
        level: Nível do rate limit (strict, moderate, conservative, generous)

    Returns:
        str: Rate limit no formato "N/time_unit"
    """
    return RATE_LIMITS.get(level, RATE_LIMITS["moderate"])