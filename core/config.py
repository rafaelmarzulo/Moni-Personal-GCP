"""
Configurações centralizadas da aplicação MoniPersonal
"""
import os
from passlib.context import CryptContext
from collections import deque
from datetime import datetime
try:
    from zoneinfo import ZoneInfo  # Python 3.9+
except ImportError:
    from backports.zoneinfo import ZoneInfo  # Fallback para versões antigas

# ============= CONFIGURAÇÕES DE AMBIENTE =============

# Detectar ambiente
IS_PRODUCTION = os.getenv("ENVIRONMENT", "development").lower() == "production"
IS_HTTPS = os.getenv("FORCE_HTTPS", "false").lower() == "true" or IS_PRODUCTION

# ============= CONFIGURAÇÕES DE SEGURANÇA =============

# Configuração de cookies seguros (ajustada para DigitalOcean App Platform)
SECURE_COOKIE_CONFIG = {
    "httponly": True,
    "secure": IS_HTTPS,  # True em produção (HTTPS)
    "samesite": "lax",  # Menos restritivo que "strict" para compatibilidade
    "max_age": 86400,  # 24 horas
    "path": "/"
}

# Nome unificado do cookie de sessão
SESSION_COOKIE_NAME = "session_token"

# Configurar contexto de criptografia com bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ============= CONFIGURAÇÕES DE TIMEZONE =============

# Timezone do Brasil - São Paulo
SAO_PAULO_TZ = ZoneInfo("America/Sao_Paulo")

# ============= CONFIGURAÇÕES DE RATE LIMITING =============

# Diferentes níveis de rate limiting
RATE_LIMITS = {
    "strict": "5/minute",      # Login, registro - operações críticas
    "moderate": "20/minute",   # Formulários, admin - operações normais
    "conservative": "15/minute", # Debug, readiness - acesso controlado
    "generous": "60/minute",   # Health checks, ping - monitoramento
}

# ============= ARMAZENAMENTO TEMPORÁRIO =============

# Dicionário temporário para armazenar sessões (em produção usar Redis ou banco)
active_sessions = {}

# Sistema de logs em memória para debug
app_logs = deque(maxlen=1000)  # Manter últimos 1000 logs

# ============= CONFIGURAÇÕES DA APLICAÇÃO =============

APP_NAME = "MoniPersonal"
APP_VERSION = "1.0.0"