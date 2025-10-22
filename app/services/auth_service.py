"""
Serviços de autenticação da aplicação
"""
import hashlib
import time
import uuid
import base64
import json
import os
from fastapi import HTTPException

from app.core.config import pwd_context, active_sessions


# Configurações de autenticação
SECRET_KEY = os.getenv("SECRET_KEY", "sua_chave_secreta_aqui")
ADMIN_PASSWORD_HASH = "5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8"  # "password"


def hash_password(password: str) -> str:
    """Hash de senha usando bcrypt"""
    return pwd_context.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    """Verifica senha contra hash bcrypt"""
    try:
        return pwd_context.verify(password, hashed)
    except:
        # Fallback para compatibilidade com senhas SHA256 existentes
        return hashlib.sha256(password.encode()).hexdigest() == hashed


def hash_password_legacy(password: str) -> str:
    """Hash SHA256 para compatibilidade com sistema antigo"""
    return hashlib.sha256(password.encode()).hexdigest()


def create_simple_jwt(user_type: str, user_id: int) -> str:
    """Cria um token JWT simples sem dependências externas"""
    payload = {
        "user_type": user_type,
        "user_id": user_id,
        "exp": time.time() + 86400,  # 24 horas
        "iat": time.time()
    }
    # Codificar payload em base64
    payload_json = json.dumps(payload)
    payload_b64 = base64.urlsafe_b64encode(payload_json.encode()).decode()

    # Criar assinatura simples
    signature_data = f"{payload_b64}:{SECRET_KEY}"
    signature = hashlib.sha256(signature_data.encode()).hexdigest()

    return f"{payload_b64}.{signature}"


def verify_simple_jwt(token: str) -> dict:
    """Verifica um token JWT simples"""
    try:
        if not token or "." not in token:
            return None

        payload_b64, signature = token.split(".", 1)

        # Verificar assinatura
        signature_data = f"{payload_b64}:{SECRET_KEY}"
        expected_signature = hashlib.sha256(signature_data.encode()).hexdigest()

        if signature != expected_signature:
            return None

        # Decodificar payload
        payload_json = base64.urlsafe_b64decode(payload_b64.encode()).decode()
        payload = json.loads(payload_json)

        # Verificar expiração
        if time.time() > payload.get("exp", 0):
            return None

        return payload
    except Exception as e:
        print(f"JWT ERROR: {e}")
        return None


def create_session_token(user_type: str, user_id: int) -> str:
    """Cria um token de sessão único e armazena os dados da sessão"""
    token = str(uuid.uuid4()).replace('-', '')
    session_data = {
        "user_type": user_type,
        "user_id": user_id,
        "created_at": time.time(),
        "valid": True
    }
    active_sessions[token] = session_data
    return token


def verify_session(token: str = None) -> dict:
    """Verifica se um token de sessão é válido e retorna os dados da sessão"""
    if not token:
        return None

    session_data = active_sessions.get(token)
    if not session_data:
        return None

    # Verificar se a sessão não expirou (24 horas)
    if time.time() - session_data.get("created_at", 0) > 86400:
        # Sessão expirada, remover
        active_sessions.pop(token, None)
        return None

    if not session_data.get("valid", False):
        return None

    return session_data


def invalidate_session(token: str) -> bool:
    """Invalida uma sessão específica"""
    if token in active_sessions:
        active_sessions.pop(token)
        return True
    return False