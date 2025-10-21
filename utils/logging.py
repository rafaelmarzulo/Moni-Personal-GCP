"""
Utilitários de logging da aplicação
"""
import structlog
from app.core.config import app_logs
from app.utils.datetime_utils import now_sao_paulo

# Configurar logger estruturado
logger = structlog.get_logger()


def log_to_memory(level: str, message: str):
    """Adiciona log à memória para visualização web"""
    timestamp = now_sao_paulo().isoformat()
    log_entry = {
        "timestamp": timestamp,
        "level": level,
        "message": message
    }
    app_logs.append(log_entry)
    print(f"[{timestamp}] {level}: {message}")


def debug_log(message: str):
    log_to_memory("DEBUG", message)


def info_log(message: str):
    log_to_memory("INFO", message)


def error_log(message: str):
    log_to_memory("ERROR", message)