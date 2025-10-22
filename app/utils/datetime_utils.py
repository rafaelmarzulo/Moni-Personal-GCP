"""
Utilitários para manipulação de datetime com timezone brasileiro
"""
from datetime import datetime
try:
    from zoneinfo import ZoneInfo
except ImportError:
    from backports.zoneinfo import ZoneInfo

from app.core.config import SAO_PAULO_TZ


def now_sao_paulo():
    """Retorna datetime atual no timezone de São Paulo"""
    return datetime.now(SAO_PAULO_TZ)


def utc_to_sao_paulo(utc_dt):
    """Converte datetime UTC para São Paulo"""
    if utc_dt is None:
        return None
    if utc_dt.tzinfo is None:
        utc_dt = utc_dt.replace(tzinfo=ZoneInfo("UTC"))
    return utc_dt.astimezone(SAO_PAULO_TZ)


def sao_paulo_to_utc(sp_dt):
    """Converte datetime de São Paulo para UTC"""
    if sp_dt.tzinfo is None:
        sp_dt = sp_dt.replace(tzinfo=SAO_PAULO_TZ)
    return sp_dt.astimezone(ZoneInfo("UTC"))