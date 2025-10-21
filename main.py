from fastapi import FastAPI, Request, Form, Depends, HTTPException, status, Cookie
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from datetime import datetime
import os
import uvicorn
import hashlib
import time
import uuid
import base64
import json
from collections import deque
from datetime import datetime
import secrets
import structlog
from passlib.context import CryptContext
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
try:
    from zoneinfo import ZoneInfo  # Python 3.9+
except ImportError:
    from backports.zoneinfo import ZoneInfo  # Fallback para versões antigas

# ============= CONFIGURAÇÕES DE SEGURANÇA =============

# Detectar ambiente
IS_PRODUCTION = os.getenv("ENVIRONMENT", "development").lower() == "production"
IS_HTTPS = os.getenv("FORCE_HTTPS", "false").lower() == "true" or IS_PRODUCTION

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

def now_sao_paulo():
    """Retorna datetime atual no timezone de São Paulo"""
    return datetime.now(SAO_PAULO_TZ)

def utc_to_sao_paulo(utc_dt):
    """Converte datetime UTC para São Paulo"""
    if utc_dt.tzinfo is None:
        utc_dt = utc_dt.replace(tzinfo=ZoneInfo("UTC"))
    return utc_dt.astimezone(SAO_PAULO_TZ)

def sao_paulo_to_utc(sp_dt):
    """Converte datetime de São Paulo para UTC"""
    if sp_dt.tzinfo is None:
        sp_dt = sp_dt.replace(tzinfo=SAO_PAULO_TZ)
    return sp_dt.astimezone(ZoneInfo("UTC"))

# Configurar logger estruturado
logger = structlog.get_logger()

# Dicionário temporário para armazenar sessões (em produção usar Redis ou banco)
active_sessions = {}

# Sistema de logs em memória para debug
app_logs = deque(maxlen=1000)  # Manter últimos 1000 logs

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

def render_safe_error(request: Request, title: str, message: str, error_details: str, back_url: str = "/"):
    """Renderiza uma página de erro segura sem perder a sessão do usuário"""
    safe_html = f"<!DOCTYPE html><html lang='pt-br'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width, initial-scale=1'><title>{title} - MoniPersonal</title><link href='https://cdn.jsdelivr.net/npm/bootstrap-dark-5@1.1.3/dist/css/bootstrap-dark.min.css' rel='stylesheet'><link rel='stylesheet' href='https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.1/font/bootstrap-icons.css'><style>body {{ background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%); color: #ffffff; min-height: 100vh; }} .card {{ border: none; border-radius: 20px; box-shadow: 0 8px 32px rgba(214, 51, 132, 0.3); background: rgba(255, 255, 255, 0.1); backdrop-filter: blur(10px); }} .btn {{ border-radius: 25px; padding: 12px 24px; font-weight: 600; }}</style></head><body><div class='container mt-5'><div class='row justify-content-center'><div class='col-md-8'><div class='card'><div class='card-header bg-danger text-white'><h4><i class='bi bi-exclamation-triangle me-2'></i>{title}</h4></div><div class='card-body'><h5>{message}</h5><p class='text-muted'>Ocorreu um erro temporário. Suas informações estão seguras e sua sessão permanece ativa.</p><div class='mt-4'><a href='{back_url}' class='btn btn-primary me-2'><i class='bi bi-arrow-left me-1'></i>Voltar</a><a href='/meu-historico' class='btn btn-success me-2'><i class='bi bi-clock-history me-1'></i>Ver Histórico</a><a href='/formulario' class='btn btn-outline-info me-2'><i class='bi bi-plus-circle me-1'></i>Nova Avaliação</a><a href='/' class='btn btn-outline-secondary'><i class='bi bi-house me-1'></i>Início</a></div><details class='mt-4'><summary class='text-muted' style='cursor: pointer;'>Detalhes técnicos (para suporte)</summary><pre class='bg-light text-dark p-3 mt-2 small rounded'><code>{error_details}</code></pre><small class='text-muted'>Se este erro persistir, entre em contato com o suporte técnico.</small></details></div></div></div></div></div></body></html>"
    return HTMLResponse(content=safe_html, status_code=500)

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

# Importar configurações do banco e modelos
from database import SessionLocal, engine, Base
from models import Avaliacao, Aluno, Usuario
# Imports básicos - schemas importados quando necessário

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

    return session_data

def clear_session(token: str) -> None:
    """Remove uma sessão do dicionário ativo"""
    active_sessions.pop(token, None)

# Função movida para depois de get_db

def require_auth(session_token: str = Cookie(None)):
    """Dependency para verificar autenticação admin"""
    print(f"🔍 REQUIRE_AUTH: session_token={session_token}")

    # Tentar JWT primeiro
    jwt_data = verify_simple_jwt(session_token)
    print(f"🔍 REQUIRE_AUTH: jwt_data={jwt_data}")

    if jwt_data and jwt_data.get("user_type") == "admin":
        print("✅ REQUIRE_AUTH: Admin autenticado via JWT")
        return True

    # Fallback para sessões em memória
    session_data = verify_session(session_token)
    print(f"🔍 REQUIRE_AUTH: session_data={session_data}")

    if session_data and session_data.get("user_type") == "admin":
        print("✅ REQUIRE_AUTH: Admin autenticado via sessão")
        return True

    print("❌ REQUIRE_AUTH: Redirecionando para login")
    raise HTTPException(
        status_code=302,
        detail="Login necessário",
        headers={"Location": "/login?user_type=admin"}
    )

def is_admin_user(session_token: str = Cookie(None)):
    """Verifica se o usuário atual é admin sem forçar autenticação"""
    if not session_token:
        return False

    # Tentar JWT primeiro
    jwt_data = verify_simple_jwt(session_token)
    if jwt_data and jwt_data.get("user_type") == "admin":
        return True

    # Fallback para sessões em memória
    session_data = verify_session(session_token)
    if session_data and session_data.get("user_type") == "admin":
        return True

    return False

def require_auth_simple(session_token: str = Cookie(None)):
    """Versão mais simples só com JWT"""
    jwt_data = verify_simple_jwt(session_token)
    return jwt_data and jwt_data.get("user_type") == "admin"


def authenticate_aluno(email: str, password: str, db: Session) -> Aluno:
    """Autentica aluno por email e senha"""
    try:
        debug_log(f"🔍 AUTH ALUNO: Tentativa login email={email}")

        aluno = db.query(Aluno).filter(Aluno.email == email, Aluno.ativo == True).first()
        if not aluno:
            error_log(f"❌ AUTH ALUNO: Aluno não encontrado ou inativo - email={email}")
            return None

        info_log(f"👤 AUTH ALUNO: Aluno encontrado - {aluno.nome} (ID: {aluno.id})")

        # Verificar se tem senha hash
        if not aluno.senha_hash:
            error_log(f"❌ AUTH ALUNO: Aluno {aluno.nome} sem senha hash")
            return None

        debug_log(f"🔐 AUTH ALUNO: Hash no banco={aluno.senha_hash[:20] if len(aluno.senha_hash) > 20 else aluno.senha_hash}...")

        # Verificar senha
        senha_correta = verify_password(password, aluno.senha_hash)
        debug_log(f"🧪 AUTH ALUNO: Verificação senha={'OK' if senha_correta else 'FALHA'}")

        if not senha_correta:
            error_log(f"❌ AUTH ALUNO: Senha incorreta para {aluno.nome}")
            return None

        info_log(f"✅ AUTH ALUNO: Login bem-sucedido para {aluno.nome}")
        return aluno

    except Exception as e:
        error_log(f"💥 AUTH ALUNO: Erro na autenticação - {str(e)}")
        return None

# ============= CONFIGURAÇÕES DE RATE LIMITING =============

# Configurar rate limiter
limiter = Limiter(key_func=get_remote_address)

# Definir diferentes níveis de rate limiting
RATE_LIMITS = {
    "strict": "5/minute",      # Login, registro - operações críticas
    "moderate": "20/minute",   # Formulários, admin - operações normais
    "generous": "60/minute",   # Health checks, ping - monitoramento
    "conservative": "30/minute" # Readiness, debug - operações técnicas
}

# Modelos importados de models.py

app = FastAPI(title="Sistema de Reavaliação Física MoniPersonal")

# Handler personalizado para rate limit exceeded
async def custom_rate_limit_handler(request: Request, exc: RateLimitExceeded):
    """Handler personalizado para quando rate limit é excedido"""
    error_log(f"⚠️ RATE LIMIT: IP {get_remote_address(request)} excedeu limite: {exc.detail}")

    # Se é uma requisição AJAX/API, retornar JSON
    if request.headers.get("accept", "").startswith("application/json"):
        return HTTPException(
            status_code=429,
            detail={
                "error": "Muitas tentativas",
                "message": "Você fez muitas requisições. Aguarde um momento e tente novamente.",
                "retry_after": exc.retry_after
            }
        )

    # Para requisições web, renderizar página de erro amigável
    return render_safe_error(
        request,
        "Muitas Tentativas",
        "Você fez muitas requisições muito rapidamente.",
        f"Aguarde {exc.retry_after} segundos e tente novamente.",
        "/"
    )

# Adicionar middleware de rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, custom_rate_limit_handler)

# Configurar arquivos estáticos e templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Rotas utilitárias removidas após debug do CSS

# Inicializar banco automaticamente na startup
@app.on_event("startup")
async def startup_event():
    try:
        Base.metadata.create_all(bind=engine)
        print("✅ Banco de dados inicializado automaticamente")
    except Exception as e:
        print(f"Erro ao inicializar banco: {e}")

# Dependency para obter sessão do banco
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ============= SISTEMA DE AUTENTICAÇÃO UNIFICADO =============

def get_current_user(session_token: str = Cookie(None, alias=SESSION_COOKIE_NAME),
                    db: Session = Depends(get_db)) -> dict:
    """
    Dependency unificada para autenticação - funciona para admin e aluno
    Retorna: {"user_type": "admin|aluno", "user_id": int, "user_data": obj|None}
    """
    client_ip = "unknown"  # Será passado pelo contexto se disponível

    logger.info("auth_attempt",
               has_token=bool(session_token),
               token_preview=session_token[:20] if session_token else None,
               ip=client_ip)

    if not session_token:
        logger.warning("auth_failed", reason="no_token", ip=client_ip)
        raise HTTPException(
            status_code=302,
            detail="Login necessário",
            headers={"Location": "/login"}
        )

    # Verificar JWT
    jwt_data = verify_simple_jwt(session_token)
    if not jwt_data:
        logger.warning("auth_failed", reason="invalid_jwt", ip=client_ip)
        raise HTTPException(
            status_code=302,
            detail="Token inválido",
            headers={"Location": "/login"}
        )

    user_type = jwt_data.get("user_type")
    user_id = jwt_data.get("user_id")

    if user_type == "admin":
        # Admin não precisa buscar no banco
        logger.info("auth_success", user_type="admin", user_id=user_id, ip=client_ip)
        return {
            "user_type": "admin",
            "user_id": user_id,
            "user_data": None,
            "is_admin": True
        }

    elif user_type == "aluno":
        # Buscar aluno no banco
        aluno = db.query(Aluno).filter(Aluno.id == user_id, Aluno.ativo == True).first()
        if not aluno:
            logger.warning("auth_failed", reason="aluno_not_found",
                         user_id=user_id, ip=client_ip)
            raise HTTPException(
                status_code=302,
                detail="Aluno não encontrado",
                headers={"Location": "/login"}
            )

        logger.info("auth_success", user_type="aluno", user_id=user_id,
                   aluno_name=aluno.nome, ip=client_ip)
        return {
            "user_type": "aluno",
            "user_id": user_id,
            "user_data": aluno,
            "is_admin": False
        }

    else:
        logger.warning("auth_failed", reason="invalid_user_type",
                     user_type=user_type, ip=client_ip)
        raise HTTPException(
            status_code=302,
            detail="Tipo de usuário inválido",
            headers={"Location": "/login"}
        )

def require_admin(user: dict = Depends(get_current_user)) -> dict:
    """Dependency que requer privilégios de admin"""
    if user["user_type"] != "admin":
        logger.warning("access_denied", required="admin",
                      user_type=user["user_type"], user_id=user["user_id"])
        raise HTTPException(
            status_code=403,
            detail="Acesso negado - admin necessário"
        )
    return user

def require_aluno(user: dict = Depends(get_current_user)) -> dict:
    """Dependency que requer ser aluno (retorna dados do aluno)"""
    if user["user_type"] != "aluno":
        logger.warning("access_denied", required="aluno",
                      user_type=user["user_type"], user_id=user["user_id"])
        raise HTTPException(
            status_code=403,
            detail="Acesso negado - apenas alunos"
        )
    return user

# ============= COMPATIBILIDADE (DEPRECATED) =============

def get_current_aluno(session_token: str = Cookie(None, alias=SESSION_COOKIE_NAME),
                     db: Session = Depends(get_db)):
    """
    DEPRECATED: Use get_current_user() instead
    Mantido para compatibilidade temporária
    """
    user = get_current_user(session_token, db)
    if user["user_type"] != "aluno":
        raise HTTPException(
            status_code=302,
            detail="Login de aluno necessário",
            headers={"Location": "/login"}
        )
    return user["user_data"]  # Retorna objeto Aluno para compatibilidade

# ==================== ROTAS DE AUTENTICAÇÃO ====================

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request, user_type: str = "aluno", is_admin: bool = Depends(is_admin_user)):
    """Página de login unificada para alunos e admins"""
    return templates.TemplateResponse(
        "login.html",
        {"request": request, "user_type": user_type, "is_admin": is_admin, "aluno": None}
    )

@app.post("/login")
@limiter.limit("10/minute")  # Strict: Login é crítico para segurança
async def login_submit(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    user_type: str = Form("aluno"),
    db: Session = Depends(get_db)
):
    client_ip = request.client.host if request.client else "unknown"

    logger.info("login_attempt",
                email=email,
                user_type=user_type,
                ip=client_ip,
                user_agent=request.headers.get("user-agent", "unknown"))

    # Verificar se é admin
    if email == "admin@monipersonal.com" and verify_password(password, ADMIN_PASSWORD_HASH):
        logger.info("admin_login_success", email=email, ip=client_ip)

        # Criar JWT
        jwt_token = create_simple_jwt("admin", 0)

        response = RedirectResponse(url="/admin/alunos", status_code=303)
        # Usar configuração segura unificada
        response.set_cookie(
            key=SESSION_COOKIE_NAME,
            value=jwt_token,
            **SECURE_COOKIE_CONFIG
        )

        logger.info("admin_session_created", ip=client_ip)
        return response

    # Verificar se é aluno
    aluno = authenticate_aluno(email, password, db)
    if aluno:
        logger.info("aluno_login_success",
                   aluno_id=aluno.id,
                   aluno_name=aluno.nome,
                   ip=client_ip)

        # Usar JWT com cookie unificado
        jwt_token = create_simple_jwt("aluno", aluno.id)

        response = RedirectResponse(url="/formulario", status_code=303)
        response.set_cookie(
            key=SESSION_COOKIE_NAME,  # Cookie unificado
            value=jwt_token,
            **SECURE_COOKIE_CONFIG    # Configuração segura
        )

        logger.info("aluno_session_created", aluno_id=aluno.id, ip=client_ip)
        return response

    # Login falhou
    logger.warning("login_failed",
                   email=email,
                   reason="invalid_credentials",
                   ip=client_ip)
    return templates.TemplateResponse(
        "login.html",
        {"request": request, "error": "Email ou senha inválidos", "user_type": user_type}
    )

@app.get("/logout")
async def logout(request: Request,
                session_token: str = Cookie(None, alias=SESSION_COOKIE_NAME)):
    """Logout unificado - limpa sessão e cookies"""
    client_ip = request.client.host if request.client else "unknown"

    # Log logout
    if session_token:
        jwt_data = verify_simple_jwt(session_token)
        if jwt_data:
            logger.info("logout_success",
                       user_type=jwt_data.get("user_type"),
                       user_id=jwt_data.get("user_id"),
                       ip=client_ip)
        # Limpar sessão se existir
        clear_session(session_token)
    else:
        logger.info("logout_no_session", ip=client_ip)

    response = RedirectResponse(url="/login", status_code=303)

    # Configurações para delete_cookie (sem max_age que causa erro)
    delete_cookie_config = {
        "path": SECURE_COOKIE_CONFIG["path"],
        "secure": SECURE_COOKIE_CONFIG["secure"],
        "httponly": SECURE_COOKIE_CONFIG["httponly"],
        "samesite": SECURE_COOKIE_CONFIG["samesite"]
    }

    # Deletar cookie unificado com configurações corretas
    response.delete_cookie(SESSION_COOKIE_NAME, **delete_cookie_config)
    response.delete_cookie(SESSION_COOKIE_NAME, path="/")
    response.delete_cookie(SESSION_COOKIE_NAME)


    # Limpar cookies antigos por compatibilidade
    response.delete_cookie("aluno_token", path="/")
    response.delete_cookie("aluno_token")
    return response

@app.get("/registro", response_class=HTMLResponse)
async def registro_page(request: Request, is_admin: bool = Depends(is_admin_user)):
    """Página de registro para novos alunos"""
    return templates.TemplateResponse("registro.html", {"request": request, "is_admin": is_admin, "aluno": None})

@app.post("/registro")
@limiter.limit(RATE_LIMITS["strict"])  # Strict: Registro precisa ser controlado
async def registro_submit(
    request: Request,
    nome: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    confirm_password: str = Form(...),
    telefone: str = Form(""),
    db: Session = Depends(get_db)
):
    # Validações
    if password != confirm_password:
        return templates.TemplateResponse(
            "registro.html",
            {"request": request, "error": "Senhas não coincidem"}
        )

    # Verificar se email já existe
    existing_aluno = db.query(Aluno).filter(Aluno.email == email).first()
    if existing_aluno:
        return templates.TemplateResponse(
            "registro.html",
            {"request": request, "error": "Email já cadastrado"}
        )

    # Criar novo aluno
    try:
        new_aluno = Aluno(
            nome=nome.strip(),
            email=email.strip().lower(),
            telefone=telefone.strip() if telefone else None,
            senha_hash=hash_password(password)
        )
        db.add(new_aluno)
        db.commit()
        db.refresh(new_aluno)

        # Login automático após registro
        jwt_token = create_simple_jwt("aluno", new_aluno.id)
        response = RedirectResponse(url="/formulario", status_code=303)
        response.set_cookie(
            key=SESSION_COOKIE_NAME,
            value=jwt_token,
            **SECURE_COOKIE_CONFIG
        )
        return response

    except Exception as e:
        db.rollback()
        return templates.TemplateResponse(
            "registro.html",
            {"request": request, "error": f"Erro ao criar conta: {str(e)}"}
        )

# ==================== ROTAS PÚBLICAS ====================

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Redireciona para a página de login"""
    return RedirectResponse(url="/login")

@app.get("/health")
@limiter.limit(RATE_LIMITS["generous"])  # Generous: Health checks para monitoramento
async def health_check(request: Request):
    """Health check endpoint para DigitalOcean App Platform"""
    return {
        "status": "healthy",
        "timestamp": now_sao_paulo().isoformat(),
        "service": "monipersonal-api",
        "version": "1.0.0"
    }

@app.get("/ping")
@limiter.limit(RATE_LIMITS["generous"])  # Generous: Ping para monitoramento
async def ping(request: Request):
    """Endpoint simples de ping"""
    return {"status": "ok", "message": "pong"}

@app.get("/readiness")
@limiter.limit(RATE_LIMITS["conservative"])  # Conservative: Readiness inclui DB check
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
        logger.error("readiness_check_failed", error=str(e))
        raise HTTPException(
            status_code=503,
            detail={
                "status": "not_ready",
                "database": "disconnected",
                "error": str(e)
            }
        )

@app.get("/formulario", response_class=HTMLResponse)
async def formulario_get(
    request: Request,
    aluno_id: Optional[int] = None,
    db: Session = Depends(get_db),
    user_data: dict = Depends(get_current_user)
):
    """Exibe o formulário de reavaliação (admin ou aluno)"""

    if user_data.get("user_type") == "admin":
        # Admin: pode selecionar aluno ou criar para aluno específico
        alunos = db.query(Aluno).filter(Aluno.ativo == True).order_by(Aluno.nome).all()

        selected_aluno = None
        if aluno_id:
            selected_aluno = db.query(Aluno).filter(Aluno.id == aluno_id, Aluno.ativo == True).first()

        return templates.TemplateResponse("formulario.html", {
            "request": request,
            "aluno": selected_aluno,  # Aluno selecionado pelo admin
            "is_admin": True,
            "alunos": alunos,  # Lista de alunos para seleção
            "selected_aluno_id": aluno_id
        })

    elif user_data.get("user_type") == "aluno":
        # Aluno regular: usar seus próprios dados
        aluno_id = user_data.get("user_id")
        aluno = db.query(Aluno).filter(Aluno.id == aluno_id, Aluno.ativo == True).first()
        if not aluno:
            logger.error("formulario_aluno_not_found", aluno_id=aluno_id)
            raise HTTPException(
                status_code=302,
                detail="Aluno não encontrado",
                headers={"Location": "/login"}
            )

        return templates.TemplateResponse("formulario.html", {
            "request": request,
            "aluno": aluno,
            "is_admin": False,
            "alunos": None
        })

    else:
        logger.error("formulario_invalid_user_type", user_type=user_data.get("user_type"))
        raise HTTPException(
            status_code=403,
            detail="Tipo de usuário inválido"
        )

@app.post("/formulario", response_class=HTMLResponse)
@limiter.limit(RATE_LIMITS["moderate"])  # Moderate: Formulários são operações normais
async def formulario_post(
    request: Request,
    # Campos antigos (manter compatibilidade)
    peso: Optional[str] = Form(""),
    medidas: Optional[str] = Form(""),

    # Novos campos de medidas corporais
    peso_kg: float = Form(...),
    altura_cm: Optional[float] = Form(None),
    percentual_gordura: Optional[float] = Form(None),

    # Circunferências essenciais
    circunferencia_pescoco: float = Form(...),
    circunferencia_cintura: float = Form(...),
    circunferencia_quadril: float = Form(...),

    observacoes_medidas: Optional[str] = Form(""),

    # Outros campos do formulário
    faltou_algo: str = Form(...),
    gostou_mais_menos: str = Form(...),
    meta_agua: str = Form(...),
    meta_agua_melhorar: str = Form(...),
    alimentacao: str = Form(...),
    melhorias: List[str] = Form([]),
    outros_melhorias: Optional[str] = Form(""),
    pedido_especial: str = Form(...),
    rotina_treino: str = Form(...),
    sugestao_geral: str = Form(...),
    aceite_info: bool = Form(False),
    aceite: bool = Form(False),

    # Novo campo para admin selecionar aluno
    admin_aluno_id: Optional[int] = Form(None),

    db: Session = Depends(get_db),
    session_token: str = Cookie(None)
):
    """Processa o formulário de reavaliação"""

    # Determinar qual aluno usar baseado no tipo de usuário
    is_admin = is_admin_user(session_token)

    if is_admin:
        # Admin: deve selecionar um aluno
        if not admin_aluno_id:
            alunos = db.query(Aluno).filter(Aluno.ativo == True).order_by(Aluno.nome).all()
            return templates.TemplateResponse(
                "formulario.html",
                {
                    "request": request,
                    "error": "Você deve selecionar um aluno para criar a avaliação",
                    "is_admin": True,
                    "alunos": alunos,
                    "selected_aluno_id": admin_aluno_id
                }
            )

        aluno = db.query(Aluno).filter(Aluno.id == admin_aluno_id, Aluno.ativo == True).first()
        if not aluno:
            return templates.TemplateResponse(
                "formulario.html",
                {
                    "request": request,
                    "error": "Aluno selecionado não encontrado",
                    "is_admin": True,
                    "alunos": db.query(Aluno).filter(Aluno.ativo == True).order_by(Aluno.nome).all()
                }
            )
    else:
        # Aluno regular: usar autenticação normal
        if not session_token:
            return RedirectResponse(url="/login", status_code=302)

        jwt_data = verify_simple_jwt(session_token)
        if not jwt_data or jwt_data.get("user_type") != "aluno":
            return RedirectResponse(url="/login", status_code=302)

        aluno_id = jwt_data.get("user_id")
        aluno = db.query(Aluno).filter(Aluno.id == aluno_id, Aluno.ativo == True).first()
        if not aluno:
            return RedirectResponse(url="/login", status_code=302)

    if not aceite or not aceite_info:
        return templates.TemplateResponse(
            "formulario.html",
            {"request": request, "error": "Você deve aceitar os termos", "aluno": aluno}
        )

    try:
        # Calcular IMC se altura estiver disponível
        imc = None
        if altura_cm and peso_kg:
            altura_m = altura_cm / 100
            imc = peso_kg / (altura_m ** 2)

        # Criar nova avaliação vinculada ao aluno logado
        avaliacao = Avaliacao(
            aluno_id=aluno.id,
            nome=aluno.nome,  # Usar nome do aluno logado

            # Campos antigos (compatibilidade)
            peso=peso.strip() if peso else f"{peso_kg}kg",
            medidas=medidas.strip() if medidas else f"Pescoço: {circunferencia_pescoco}cm, Cintura: {circunferencia_cintura}cm, Quadril: {circunferencia_quadril}cm",

            # Novos campos de medidas
            peso_kg=peso_kg,
            altura_cm=altura_cm,
            percentual_gordura=percentual_gordura,
            imc=imc,

            # Circunferências essenciais
            circunferencia_pescoco=circunferencia_pescoco,
            circunferencia_cintura=circunferencia_cintura,
            circunferencia_quadril=circunferencia_quadril,

            observacoes_medidas=observacoes_medidas.strip() if observacoes_medidas else "",

            # Outros campos
            faltou_algo=faltou_algo.strip(),
            gostou_mais_menos=gostou_mais_menos.strip(),
            meta_agua=meta_agua.strip(),
            meta_agua_melhorar=meta_agua_melhorar.strip(),
            alimentacao=alimentacao.strip(),
            melhorias=",".join(melhorias) if melhorias else "",
            outros_melhorias=outros_melhorias.strip() if outros_melhorias else "",
            pedido_especial=pedido_especial.strip(),
            rotina_treino=rotina_treino.strip(),
            sugestao_geral=sugestao_geral.strip()
        )

        db.add(avaliacao)
        db.commit()
        db.refresh(avaliacao)

        return templates.TemplateResponse(
            "sucesso.html",
            {"request": request, "nome": aluno.nome, "aluno": aluno, "is_admin": is_admin}
        )
    
    except Exception as e:
        db.rollback()
        return templates.TemplateResponse(
            "formulario.html",
            {"request": request, "error": f"Erro ao salvar dados: {str(e)}", "aluno": aluno}
        )

# ==================== ROTAS DE MIGRAÇÃO (TEMPORÁRIA) ====================

@app.get("/migrate-db")
async def migrate_database(db: Session = Depends(get_db)):
    """Migração para adicionar coluna aluno_id na tabela avaliacoes"""
    from sqlalchemy import text
    try:
        # Verificar se a coluna já existe
        result = db.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name='avaliacoes' AND column_name='aluno_id'"))
        column_exists = result.fetchone()

        if not column_exists:
            # Adicionar coluna aluno_id
            db.execute(text("ALTER TABLE avaliacoes ADD COLUMN aluno_id INTEGER"))
            # Adicionar constraint de foreign key
            db.execute(text("ALTER TABLE avaliacoes ADD CONSTRAINT fk_avaliacoes_aluno FOREIGN KEY (aluno_id) REFERENCES alunos(id)"))
            db.commit()
            return {"message": "✅ Migração executada com sucesso! Coluna aluno_id adicionada."}
        else:
            return {"message": "ℹ️ Coluna aluno_id já existe."}

    except Exception as e:
        db.rollback()
        return {"error": f"Erro na migração: {str(e)}"}

@app.get("/migrate-dados-antigos")
async def migrate_dados_antigos(db: Session = Depends(get_db)):
    """Migra dados antigos dos campos texto para campos específicos"""
    try:
        import re

        # Buscar avaliações que têm dados antigos mas não têm dados nos novos campos
        avaliacoes = db.query(Avaliacao).filter(
            Avaliacao.peso_kg.is_(None),  # Sem dados novos
            Avaliacao.peso.isnot(None)    # Mas com dados antigos
        ).all()

        migrated_count = 0

        for avaliacao in avaliacoes:
            try:
                # Migrar peso
                if avaliacao.peso and not avaliacao.peso_kg:
                    peso_match = re.search(r'(\d+(?:\.\d+)?)', avaliacao.peso.replace(',', '.'))
                    if peso_match:
                        avaliacao.peso_kg = float(peso_match.group(1))

                # Migrar medidas do campo texto para campos específicos
                if avaliacao.medidas:
                    medidas_texto = avaliacao.medidas.lower()

                    # Regex patterns para extrair apenas os valores essenciais
                    patterns = {
                        'circunferencia_pescoco': r'pescoço[:\s]*(\d+(?:\.\d+)?)',
                        'circunferencia_cintura': r'cintura[:\s]*(\d+(?:\.\d+)?)',
                        'circunferencia_quadril': r'quadril[:\s]*(\d+(?:\.\d+)?)',
                    }

                    for campo, pattern in patterns.items():
                        if not getattr(avaliacao, campo):  # Se não tem valor ainda
                            match = re.search(pattern, medidas_texto)
                            if match:
                                # Pegar o primeiro grupo que não é None
                                valor = next((g for g in match.groups() if g), None)
                                if valor:
                                    setattr(avaliacao, campo, float(valor.replace(',', '.')))

                migrated_count += 1

            except Exception as e:
                print(f"Erro ao migrar avaliação {avaliacao.id}: {e}")
                continue

        # Salvar mudanças
        db.commit()

        return {
            "message": f"Migração concluída! {migrated_count} avaliações processadas.",
            "migrated": migrated_count,
            "total_found": len(avaliacoes)
        }

    except Exception as e:
        db.rollback()
        return {"error": f"Erro na migração: {str(e)}"}

@app.get("/migrate-medidas")
async def migrate_medidas_corporais(db: Session = Depends(get_db)):
    """Migração para adicionar campos específicos de medidas corporais"""
    from sqlalchemy import text
    try:
        # Lista de novos campos para adicionar
        novos_campos = [
            ("peso_kg", "REAL"),
            ("altura_cm", "REAL"),
            ("percentual_gordura", "REAL"),
            ("circunferencia_pescoco", "REAL"),
            ("circunferencia_braco_direito", "REAL"),
            ("circunferencia_braco_esquerdo", "REAL"),
            ("circunferencia_antebraco_direito", "REAL"),
            ("circunferencia_antebraco_esquerdo", "REAL"),
            ("circunferencia_torax", "REAL"),
            ("circunferencia_cintura", "REAL"),
            ("circunferencia_abdome", "REAL"),
            ("circunferencia_quadril", "REAL"),
            ("circunferencia_coxa_direita", "REAL"),
            ("circunferencia_coxa_esquerda", "REAL"),
            ("circunferencia_panturrilha_direita", "REAL"),
            ("circunferencia_panturrilha_esquerda", "REAL"),
            ("dobra_bicipital", "REAL"),
            ("dobra_tricipital", "REAL"),
            ("dobra_subescapular", "REAL"),
            ("dobra_suprailiaca", "REAL"),
            ("dobra_abdominal", "REAL"),
            ("dobra_coxa", "REAL"),
            ("imc", "REAL"),
            ("observacoes_medidas", "TEXT")
        ]

        campos_adicionados = []
        campos_existentes = []

        for campo, tipo in novos_campos:
            # Verificar se a coluna já existe
            result = db.execute(text(f"SELECT column_name FROM information_schema.columns WHERE table_name='avaliacoes' AND column_name='{campo}'"))
            column_exists = result.fetchone()

            if not column_exists:
                # Adicionar nova coluna
                db.execute(text(f"ALTER TABLE avaliacoes ADD COLUMN {campo} {tipo}"))
                campos_adicionados.append(campo)
            else:
                campos_existentes.append(campo)

        # Tornar os campos peso e medidas antigos nullable para compatibilidade
        try:
            db.execute(text("ALTER TABLE avaliacoes ALTER COLUMN peso DROP NOT NULL"))
            db.execute(text("ALTER TABLE avaliacoes ALTER COLUMN medidas DROP NOT NULL"))
        except:
            pass  # Pode falhar se já forem nullable

        db.commit()

        message = f"Migração de medidas corporais concluída!"
        if campos_adicionados:
            message += f"\n📝 Campos adicionados: {', '.join(campos_adicionados)}"
        if campos_existentes:
            message += f"\nCampos já existentes: {', '.join(campos_existentes)}"

        return {"message": message}

    except Exception as e:
        db.rollback()
        return {"error": f"Erro na migração de medidas: {str(e)}"}

# ==================== ROTAS ADMINISTRATIVAS ADICIONAIS ====================

@app.get("/admin/reset-passwords", response_class=HTMLResponse)
async def admin_reset_passwords(request: Request, db: Session = Depends(get_db), auth: bool = Depends(require_auth)):
    """Página para resetar senhas de alunos"""
    try:
        alunos = db.query(Aluno).filter(Aluno.ativo == True).order_by(Aluno.nome).all()
        return templates.TemplateResponse(
            "admin_reset_passwords.html",
            {"request": request, "alunos": alunos}
        )
    except Exception as e:
        return HTMLResponse(
            content=f"<h1>Erro:</h1><p>{str(e)}</p>",
            status_code=500
        )

@app.get("/admin/avaliacoes", response_class=HTMLResponse)
async def admin_todas_avaliacoes(
    request: Request,
    db: Session = Depends(get_db),
    auth: bool = Depends(require_auth),
    aluno: str = None,
    ordem: str = "data_desc",
    limite: int = 100
):
    """Página com todas as avaliações do sistema com filtros"""
    try:
        # Query base
        query = db.query(Avaliacao)

        # Filtro por aluno
        if aluno:
            query = query.filter(Avaliacao.nome.ilike(f"%{aluno}%"))

        # Ordenação
        if ordem == "data_asc":
            query = query.order_by(Avaliacao.data.asc())
        elif ordem == "data_desc":
            query = query.order_by(Avaliacao.data.desc())
        elif ordem == "nome_asc":
            query = query.order_by(Avaliacao.nome.asc())
        elif ordem == "nome_desc":
            query = query.order_by(Avaliacao.nome.desc())
        elif ordem == "peso_asc":
            query = query.order_by(Avaliacao.peso_kg.asc().nullslast())
        elif ordem == "peso_desc":
            query = query.order_by(Avaliacao.peso_kg.desc().nullslast())
        else:
            query = query.order_by(Avaliacao.data.desc())

        # Limite
        avaliacoes = query.limit(limite).all()

        # Buscar todos os alunos únicos para o filtro
        alunos_unicos = db.query(Avaliacao.nome).distinct().order_by(Avaliacao.nome).all()
        alunos_unicos = [nome[0] for nome in alunos_unicos if nome[0]]

        # Processar melhorias para exibição
        for avaliacao in avaliacoes:
            if avaliacao.melhorias:
                avaliacao.melhorias_processadas = [
                    m.strip() for m in avaliacao.melhorias.split(",") if m.strip()
                ]
            else:
                avaliacao.melhorias_processadas = []

        return templates.TemplateResponse(
            "admin_avaliacoes.html",
            {
                "request": request,
                "avaliacoes": avaliacoes,
                "alunos_unicos": alunos_unicos,
                "filtro_aluno": aluno or "",
                "ordem_atual": ordem,
                "limite_atual": limite
            }
        )
    except Exception as e:
        return HTMLResponse(
            content=f"<h1>Erro:</h1><p>{str(e)}</p>",
            status_code=500
        )

@app.get("/admin/avaliacao/{avaliacao_id}")
async def admin_detalhes_avaliacao(
    avaliacao_id: int,
    db: Session = Depends(get_db),
    auth: bool = Depends(require_auth)
):
    """API para buscar detalhes de uma avaliação específica"""
    try:
        # Carregar avaliação com relacionamento aluno usando joinedload
        from sqlalchemy.orm import joinedload
        avaliacao = db.query(Avaliacao).options(
            joinedload(Avaliacao.aluno)
        ).filter(Avaliacao.id == avaliacao_id).first()

        if not avaliacao:
            raise HTTPException(status_code=404, detail="Avaliação não encontrada")

        # Processar melhorias
        melhorias = []
        if avaliacao.melhorias:
            melhorias = [m.strip() for m in avaliacao.melhorias.split(",") if m.strip()]

        # Preparar dados para retorno
        detalhes = {
            "id": avaliacao.id,
            "nome": avaliacao.nome,
            "data": avaliacao.data.strftime('%d/%m/%Y às %H:%M') if avaliacao.data else None,
            "peso_kg": getattr(avaliacao, 'peso_kg', None),
            "altura_cm": getattr(avaliacao, 'altura_cm', None),
            "idade": getattr(avaliacao, 'idade', None),
            "melhorias": melhorias,
            "aluno_email": avaliacao.aluno.email if avaliacao.aluno else "Email não disponível",
            # Medidas corporais essenciais
            "pescoco_cm": getattr(avaliacao, 'circunferencia_pescoco', None),
            "cintura_cm": getattr(avaliacao, 'circunferencia_cintura', None),
            "quadril_cm": getattr(avaliacao, 'circunferencia_quadril', None)
        }

        return detalhes
    except HTTPException:
        raise
    except Exception as e:
        error_log(f"Erro ao carregar detalhes da avaliação {avaliacao_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro interno do servidor: {str(e)}")

@app.get("/admin/relatorios", response_class=HTMLResponse)
async def admin_relatorios(request: Request, db: Session = Depends(get_db), auth: bool = Depends(require_auth)):
    """Página de relatórios e estatísticas"""
    try:
        # Estatísticas básicas
        total_alunos = db.query(Aluno).filter(Aluno.ativo == True).count()
        total_avaliacoes = db.query(Avaliacao).count()

        # Alunos mais ativos (com mais avaliações)
        alunos_ativos = db.query(
            Aluno.nome,
            func.count(Avaliacao.id).label('total_avaliacoes')
        ).join(Avaliacao, Aluno.id == Avaliacao.aluno_id).group_by(Aluno.nome).order_by(func.count(Avaliacao.id).desc()).limit(10).all()

        # Últimas avaliações
        ultimas_avaliacoes = db.query(Avaliacao).order_by(Avaliacao.data.desc()).limit(10).all()

        return templates.TemplateResponse(
            "admin_relatorios.html",
            {
                "request": request,
                "total_alunos": total_alunos,
                "total_avaliacoes": total_avaliacoes,
                "alunos_ativos": alunos_ativos,
                "ultimas_avaliacoes": ultimas_avaliacoes
            }
        )
    except Exception as e:
        return HTMLResponse(
            content=f"<h1>Erro:</h1><p>{str(e)}</p>",
            status_code=500
        )

# ==================== ROTAS DE DEBUG (TEMPORÁRIA) ====================

@app.get("/debug/migrate")
async def debug_migrate(request: Request, session_token: str = Cookie(None)):
    """Executar migração do banco de dados via web"""
    # Verificar se é admin
    jwt_data = verify_simple_jwt(session_token)
    if not (jwt_data and jwt_data.get("user_type") == "admin"):
        return {"error": "Acesso negado. Faça login como admin primeiro."}

    try:
        info_log("🚀 Iniciando migração via web...")

        # Importar e executar migração
        import subprocess
        import sys
        import os

        # Executar migração
        result = subprocess.run([sys.executable, "migrate_db.py"],
                              capture_output=True, text=True, cwd=".")

        info_log(f"Migração executada. Código de saída: {result.returncode}")
        info_log(f"Stdout: {result.stdout}")
        if result.stderr:
            error_log(f"Stderr: {result.stderr}")

        return {
            "success": result.returncode == 0,
            "message": "Migração executada com sucesso!" if result.returncode == 0 else "Erro na migração",
            "output": result.stdout,
            "error": result.stderr if result.stderr else None,
            "return_code": result.returncode
        }

    except Exception as e:
        error_log(f"Erro ao executar migração: {str(e)}")
        return {"error": f"Erro ao executar migração: {str(e)}"}

@app.get("/debug/logs", response_class=HTMLResponse)
@limiter.limit(RATE_LIMITS["conservative"])  # Conservative: Debug só para admins
async def debug_logs(request: Request, session_token: str = Cookie(None)):
    """Visualizar logs da aplicação via web"""
    # Verificar se é admin
    jwt_data = verify_simple_jwt(session_token)
    if not (jwt_data and jwt_data.get("user_type") == "admin"):
        return RedirectResponse(url="/login?user_type=admin", status_code=302)

    # Converter logs para lista e inverter (mais recentes primeiro)
    logs_list = list(app_logs)
    logs_list.reverse()

    logs_html = ""
    for log in logs_list[:100]:  # Mostrar últimos 100 logs
        level = log["level"]
        color = {
            "ERROR": "red",
            "INFO": "blue",
            "DEBUG": "gray"
        }.get(level, "black")

        logs_html += f"<div style='margin: 5px 0; padding: 5px; border-left: 3px solid {color};'><small style='color: gray;'>{log['timestamp']}</small><strong style='color: {color};'>[{level}]</strong><span>{log['message']}</span></div>"

    logs_content = logs_html if logs_html else "<p>Nenhum log encontrado</p>"
    html_page = f"""<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Debug Logs • Sistema de Reavaliação Física MoniPersonal</title>

    <!-- Favicon -->
    <link rel="icon" type="image/png" href="/static/favicon.png">

    <!-- Bootstrap Dark Theme -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap-dark-5@1.1.3/dist/css/bootstrap-dark.min.css" rel="stylesheet" crossorigin="anonymous">

    <!-- Bootstrap Icons -->
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.1/font/bootstrap-icons.css">

    <style>
        body {{
            background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%);
            color: #ffffff;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            min-height: 100vh;
        }}
        .log-entry {{
            margin: 8px 0;
            padding: 12px;
            border-radius: 8px;
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(10px);
            border-left: 4px solid;
        }}
        .log-ERROR {{ border-left-color: #dc3545; }}
        .log-INFO {{ border-left-color: #0dcaf0; }}
        .log-DEBUG {{ border-left-color: #6c757d; }}
        .navbar-brand {{
            background: linear-gradient(45deg, #d63384, #6f42c1);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-weight: bold;
        }}
        .btn-custom {{
            background: linear-gradient(45deg, #d63384, #6f42c1);
            border: none;
            border-radius: 25px;
            padding: 8px 16px;
            color: white;
            text-decoration: none;
            transition: all 0.3s ease;
        }}
        .btn-custom:hover {{
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(214, 51, 132, 0.4);
            color: white;
        }}
    </style>
</head>
<body>
    <!-- Navbar -->
    <nav class="navbar navbar-expand-lg navbar-dark bg-dark mb-4">
        <div class="container">
            <a class="navbar-brand" href="/admin/alunos">
                <i class="bi bi-activity me-2"></i>MoniPersonal Admin
            </a>
            <div class="navbar-nav ms-auto">
                <a class="nav-link" href="/admin/alunos">
                    <i class="bi bi-arrow-left me-1"></i>Voltar
                </a>
            </div>
        </div>
    </nav>

    <div class="container">
        <!-- Header -->
        <div class="row mb-4">
            <div class="col-12">
                <div class="d-flex justify-content-between align-items-center">
                    <h1><i class="bi bi-bug me-2"></i>Debug Logs</h1>
                    <div>
                        <button onclick="location.reload()" class="btn btn-custom me-2">
                            <i class="bi bi-arrow-clockwise me-1"></i>Atualizar
                        </button>
                    </div>
                </div>
                <p class="text-muted">Últimos 100 logs da aplicação (atualizados automaticamente a cada 30s)</p>
            </div>
        </div>

        <!-- Logs Content -->
        <div class="row">
            <div class="col-12">
                <div class="card bg-transparent border-0">
                    <div class="card-body p-0">
                        {logs_content}
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- Bootstrap JS -->
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js"></script>

    <!-- Auto-refresh -->
    <script>
        // Auto-refresh a cada 30 segundos
        setTimeout(() => location.reload(), 30000);

        // Adicionar classes CSS aos logs
        document.addEventListener('DOMContentLoaded', function() {{
            const logDivs = document.querySelectorAll('div[style*="border-left"]');
            logDivs.forEach(div => {{
                const level = div.querySelector('strong').textContent.match(/\[(.*)\]/)[1];
                div.className = `log-entry log-${{level}}`;
                div.removeAttribute('style');
            }});
        }});
    </script>
</body>
</html>"""
    return HTMLResponse(content=html_page)

@app.get("/debug/session")
async def debug_session(session_token: str = Cookie(None)):
    """Debug da sessão atual"""
    session_data = verify_session(session_token)
    return {
        "session_token": session_token,
        "session_data": session_data,
        "active_sessions_count": len(active_sessions)
    }

@app.post("/debug/test-login")
async def debug_test_login(
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    """Rota para testar login de aluno diretamente"""
    print(f"🧪 DEBUG LOGIN: Testando {email} com senha {password}")

    # Buscar aluno
    aluno = db.query(Aluno).filter(Aluno.email == email, Aluno.ativo == True).first()

    if not aluno:
        return {
            "success": False,
            "message": "Aluno não encontrado",
            "email_testado": email
        }

    # Testar senha manualmente
    hash_atual = aluno.senha_hash
    hash_da_senha_teste = hash_password(password)
    senha_correta = verify_password(password, hash_atual)

    return {
        "success": senha_correta,
        "aluno_nome": aluno.nome,
        "aluno_email": aluno.email,
        "aluno_id": aluno.id,
        "senha_testada": password,
        "hash_no_banco": hash_atual[:20] + "...",
        "hash_da_senha_teste": hash_da_senha_teste[:20] + "...",
        "hashes_coincidem": hash_atual == hash_da_senha_teste,
        "verify_password_result": senha_correta,
        "message": "Login funcionaria!" if senha_correta else "Senha incorreta"
    }

@app.get("/debug/aluno/{email}")
async def debug_aluno_info(email: str, db: Session = Depends(get_db)):
    """Debug de informações do aluno"""
    aluno = db.query(Aluno).filter(Aluno.email == email).first()

    if not aluno:
        return {"error": "Aluno não encontrado", "email": email}

    return {
        "aluno_id": aluno.id,
        "nome": aluno.nome,
        "email": aluno.email,
        "ativo": aluno.ativo,
        "telefone": aluno.telefone,
        "hash_senha": aluno.senha_hash[:20] + "...",
        "hash_completo_length": len(aluno.senha_hash),
        "created_at": str(aluno.created_at) if aluno.created_at else None
    }

@app.get("/debug/test-checkbox-simple", response_class=HTMLResponse)
async def debug_test_checkbox_simple():
    """Teste ultra-simples de checkbox sem CSS customizado"""
    return HTMLResponse(content="""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Teste Checkbox Simples</title>
        <!-- Apenas Bootstrap padrão -->
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
    </head>
    <body class="p-4">
        <h2>Teste de Checkboxes</h2>

        <div class="form-check mb-3">
            <input class="form-check-input" type="checkbox" id="teste1" name="teste1">
            <label class="form-check-label" for="teste1">
                Checkbox 1 - Apenas Bootstrap padrão
            </label>
        </div>

        <div class="form-check mb-3">
            <input class="form-check-input" type="checkbox" id="teste2" name="teste2" checked>
            <label class="form-check-label" for="teste2">
                Checkbox 2 - Marcado por padrão
            </label>
        </div>

        <hr>

        <input type="checkbox" id="teste3" name="teste3">
        <label for="teste3">Checkbox 3 - HTML puro (sem classes Bootstrap)</label>

        <hr>

        <p><strong>Se você vê 3 checkboxes acima, o problema é no CSS customizado do site.</strong></p>
        <p><strong>Se não vê nenhum, o problema é mais profundo.</strong></p>
    </body>
    </html>
    """)

@app.get("/debug/test-form-no-theme", response_class=HTMLResponse)
async def debug_test_form_no_theme():
    """Teste do formulário sem CSS customizado"""
    return HTMLResponse(content="""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Teste Formulário Sem Tema</title>
        <!-- Apenas Bootstrap padrão -->
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
    </head>
    <body class="p-4">
        <h2>Teste - Só os Checkboxes do Formulário</h2>

        <!-- Exatamente como está no formulario.html -->
        <div class="alert alert-light border rounded-3">
            <p class="mb-2">
                Estou ciente que não devo omitir nenhuma informação que seja necessária sobre esse mês
                que passou.
                E para que a prescrição do novo treino fique individualizada para as minhas
                necessidades, preciso enviar
                as fotos de frente, lado e costa no grupo de suporte do WhatsApp, para ser avaliado onde
                teve melhora
                e onde ainda preciso melhorar.
            </p>
            <div class="form-check">
                <input class="form-check-input" type="checkbox" id="aceite_info" name="aceite_info"
                    required>
                <label class="form-check-label" for="aceite_info">
                    Aceite e assinatura da informação acima *
                </label>
            </div>
        </div>

        <!-- Aceite -->
        <div class="mb-4">
            <div class="form-check">
                <input class="form-check-input" type="checkbox" name="aceite" value="true" id="aceite"
                    required>
                <label class="form-check-label" for="aceite">
                    <strong>Declaro que todas as informações fornecidas são verdadeiras *</strong>
                </label>
            </div>
        </div>

        <p><strong>Se você vê os 2 checkboxes acima, o problema é o CSS do tema base.html</strong></p>
    </body>
    </html>
    """)

@app.get("/debug/test-form-render", response_class=HTMLResponse)
async def debug_test_form_render(request: Request):
    """Visualizar formulário diretamente para debug de checkboxes"""
    # Criar um aluno fake para teste
    fake_aluno = type('obj', (object,), {
        'id': 999,
        'nome': 'Teste Debug',
        'email': 'teste@debug.com'
    })

    return templates.TemplateResponse("formulario.html", {
        "request": request,
        "aluno": fake_aluno
    })

@app.get("/debug/test-form", response_class=HTMLResponse)
async def debug_test_form():
    """Formulário para testar login"""
    return HTMLResponse(content="""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Debug - Teste de Login</title>
        <meta charset="utf-8">
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; }
            .form-group { margin: 20px 0; }
            input, button { padding: 10px; margin: 5px; }
            .result { background: #f0f0f0; padding: 20px; margin: 20px 0; white-space: pre-wrap; }
        </style>
    </head>
    <body>
        <h1>🔍 Debug - Teste de Login</h1>

        <form id="testForm">
            <div class="form-group">
                <label>Email do aluno:</label><br>
                <input type="email" id="email" placeholder="rafael@exemplo.com" style="width: 300px;">
            </div>

            <div class="form-group">
                <label>Senha para testar:</label><br>
                <input type="text" id="password" placeholder="teste123" style="width: 300px;">
            </div>

            <button type="submit">🧪 Testar Login</button>
        </form>

        <div id="result" class="result" style="display: none;"></div>

        <script>
        document.getElementById('testForm').addEventListener('submit', async function(e) {
            e.preventDefault();

            const email = document.getElementById('email').value;
            const password = document.getElementById('password').value;

            const formData = new FormData();
            formData.append('email', email);
            formData.append('password', password);

            try {
                const response = await fetch('/debug/test-login', {
                    method: 'POST',
                    body: formData
                });

                const result = await response.json();

                document.getElementById('result').style.display = 'block';
                document.getElementById('result').innerHTML =
                    '<h3>Resultado do Teste:</h3>' +
                    JSON.stringify(result, null, 2);

            } catch (error) {
                document.getElementById('result').style.display = 'block';
                document.getElementById('result').innerHTML = 'Erro: ' + error.message;
            }
        });
        </script>
    </body>
    </html>
    """)

# ==================== ROTAS ADMINISTRATIVAS (PROTEGIDAS) ====================

@app.get("/admin/test")
async def admin_test(session_token: str = Cookie(None)):
    """Rota de teste simples para admin"""
    print(f"🧪 ADMIN TEST: session_token={session_token}")

    # Testar JWT
    jwt_data = verify_simple_jwt(session_token)
    print(f"🧪 ADMIN TEST: jwt_data={jwt_data}")

    # Testar sessão
    session_data = verify_session(session_token)
    print(f"🧪 ADMIN TEST: session_data={session_data}")

    return {
        "message": "Admin test route",
        "session_token": session_token[:20] + "..." if session_token else None,
        "jwt_data": jwt_data,
        "session_data": session_data,
        "is_admin_jwt": jwt_data and jwt_data.get("user_type") == "admin",
        "is_admin_session": session_data and session_data.get("user_type") == "admin",
        "active_sessions_count": len(active_sessions)
    }

@app.get("/admin/simple", response_class=HTMLResponse)
async def admin_simple(request: Request, session_token: str = Cookie(None)):
    """Rota admin simples sem dependencies para teste"""
    print(f"🎯 ADMIN SIMPLE: session_token={session_token}")

    jwt_data = verify_simple_jwt(session_token)
    is_admin = jwt_data and jwt_data.get("user_type") == "admin"

    if not is_admin:
        return RedirectResponse(url="/login?user_type=admin", status_code=302)

    return HTMLResponse(content=f"<html><body><h1>Admin Simples Funcionando!</h1><p>JWT Data: {jwt_data}</p><p><a href='/admin/alunos'>Ir para Admin Alunos</a></p><p><a href='/logout'>Logout</a></p></body></html>")

@app.post("/admin/reset-senha/{aluno_id}")
async def admin_reset_senha_aluno(
    aluno_id: int,
    nova_senha: str = Form(...),
    db: Session = Depends(get_db),
    auth: bool = Depends(require_auth)
):
    """Reset de senha de aluno pelo admin"""
    try:
        info_log(f"🔄 RESET SENHA: Aluno ID={aluno_id}, Nova senha={nova_senha}")

        aluno = db.query(Aluno).filter(Aluno.id == aluno_id).first()
        if not aluno:
            error_log(f"RESET SENHA: Aluno {aluno_id} não encontrado")
            return {"error": "Aluno não encontrado"}

        # Calcular novo hash
        novo_hash = hash_password(nova_senha)
        debug_log(f"🔐 RESET SENHA: Hash antigo={aluno.senha_hash[:20]}...")
        debug_log(f"🔐 RESET SENHA: Hash novo={novo_hash[:20]}...")

        # Atualizar senha
        aluno.senha_hash = novo_hash
        db.commit()

        # Verificar se foi salvo
        aluno_verificado = db.query(Aluno).filter(Aluno.id == aluno_id).first()
        info_log(f"RESET SENHA: Hash salvo={aluno_verificado.senha_hash[:20]}...")

        # Testar se a nova senha funciona
        teste_auth = verify_password(nova_senha, aluno_verificado.senha_hash)
        info_log(f"🧪 RESET SENHA: Teste autenticação={teste_auth}")

        if teste_auth:
            info_log(f"RESET SENHA: Sucesso para {aluno.nome}")
        else:
            error_log(f"RESET SENHA: Falha na verificação para {aluno.nome}")

        return {"success": f"Senha do aluno {aluno.nome} resetada com sucesso"}
    except Exception as e:
        error_log(f"RESET SENHA: Erro - {str(e)}")
        db.rollback()
        return {"error": f"Erro ao resetar senha: {str(e)}"}

@app.get("/admin/alunos", response_class=HTMLResponse)
async def admin_lista_alunos(request: Request, db: Session = Depends(get_db), auth: bool = Depends(require_auth)):
    """Lista todos os alunos registrados (rota protegida)"""
    print("🎯 ADMIN/ALUNOS: Rota acessada com sucesso")
    try:
        # Buscar alunos da tabela alunos, não das avaliações
        alunos = db.query(Aluno).order_by(Aluno.nome).all()
        print(f"📊 ADMIN/ALUNOS: {len(alunos)} alunos encontrados")

        return templates.TemplateResponse(
            "admin_alunos.html",
            {"request": request, "alunos": alunos, "is_admin": True}
        )
    except Exception as e:
        print(f"ADMIN/ALUNOS: Erro - {str(e)}")
        return render_safe_error(
            request=request,
            title="Erro no Sistema",
            message="Ocorreu um erro interno. Tente novamente ou entre em contato com o suporte.",
            error_details=str(e),
            back_url="/admin/alunos"
        )

@app.get("/admin/debug-timezone")
async def admin_debug_timezone(auth: bool = Depends(require_auth)):
    """Endpoint de debug para verificar configuração de timezone"""
    try:
        import subprocess

        # Horários em diferentes formatos
        agora_sao_paulo = now_sao_paulo()
        agora_utc = datetime.utcnow()
        agora_local = datetime.now()

        # Informações do sistema
        try:
            timezone_sistema = subprocess.run(['timedatectl', 'show', '--property=Timezone', '--value'],
                                            capture_output=True, text=True).stdout.strip()
        except:
            timezone_sistema = "Não disponível"

        return {
            "sistema": {
                "timezone": timezone_sistema,
                "datetime_local": agora_local.isoformat(),
                "timezone_info": str(agora_local.tzinfo) if agora_local.tzinfo else "Naive"
            },
            "aplicacao": {
                "now_sao_paulo": agora_sao_paulo.isoformat(),
                "timezone_sp": str(agora_sao_paulo.tzinfo),
                "utc_equivalente": sao_paulo_to_utc(agora_sao_paulo).isoformat()
            },
            "comparacao": {
                "utcnow_antigo": agora_utc.isoformat(),
                "diferenca_horas": (agora_sao_paulo.replace(tzinfo=None) - agora_utc).total_seconds() / 3600
            },
            "testes": {
                "conversao_utc_para_sp": utc_to_sao_paulo(agora_utc).isoformat(),
                "conversao_sp_para_utc": sao_paulo_to_utc(agora_sao_paulo).isoformat()
            }
        }
    except Exception as e:
        return {"error": f"Erro ao verificar timezone: {str(e)}"}

@app.get("/admin/debug-alunos")
async def admin_debug_alunos(db: Session = Depends(get_db), auth: bool = Depends(require_auth)):
    """Endpoint de debug para verificar problemas de login dos alunos"""
    try:
        alunos = db.query(Aluno).filter(Aluno.ativo == True).all()

        problemas = []
        for aluno in alunos:
            problema = {
                "id": aluno.id,
                "nome": aluno.nome,
                "email": aluno.email,
                "problemas": []
            }

            # Verificar se tem senha hash
            if not aluno.senha_hash:
                problema["problemas"].append("Sem senha hash")
            else:
                # Verificar se a senha hash parece ser bcrypt ou SHA256
                if len(aluno.senha_hash) == 64:
                    problema["problemas"].append("Senha SHA256 (legado)")
                elif aluno.senha_hash.startswith("$2b$"):
                    problema["problemas"].append("Senha bcrypt (OK)")
                else:
                    problema["problemas"].append("Formato de hash desconhecido")

            # Verificar email válido
            if "@" not in aluno.email:
                problema["problemas"].append("Email inválido")

            if problema["problemas"]:
                problemas.append(problema)

        return {
            "total_alunos": len(alunos),
            "alunos_com_problemas": len(problemas),
            "problemas": problemas
        }
    except Exception as e:
        return {"error": f"Erro ao verificar alunos: {str(e)}"}

@app.get("/admin/aluno/{nome}", response_class=HTMLResponse)
async def admin_historico_aluno(request: Request, nome: str, db: Session = Depends(get_db), auth: bool = Depends(require_auth)):
    """Exibe histórico de um aluno específico (rota protegida)"""
    try:
        avaliacoes = db.query(Avaliacao).filter(
            Avaliacao.nome == nome
        ).order_by(Avaliacao.data.desc()).all()
        
        for avaliacao in avaliacoes:
            if avaliacao.melhorias:
                avaliacao.melhorias_processadas = [
                    m.strip() for m in avaliacao.melhorias.split(",") if m.strip()
                ]
            else:
                avaliacao.melhorias_processadas = []
        
        return templates.TemplateResponse(
            "historico.html",
            {"request": request, "nome": nome, "avaliacoes": avaliacoes, "is_admin": True}
        )
    except Exception as e:
        return render_safe_error(
            request=request,
            title="Erro no Relatório",
            message="Não foi possível gerar o relatório do aluno.",
            error_details=str(e),
            back_url="/admin/relatorios"
        )

@app.get("/admin/comparar/{nome}", response_class=HTMLResponse)
async def admin_comparar_progresso(request: Request, nome: str, db: Session = Depends(get_db), auth: bool = Depends(require_auth)):
    """Compara o progresso de um aluno (rota protegida)"""
    try:
        avaliacoes = db.query(Avaliacao).filter(
            Avaliacao.nome == nome
        ).order_by(Avaliacao.data.asc()).all()
        
        for avaliacao in avaliacoes:
            if avaliacao.melhorias:
                avaliacao.melhorias_processadas = [
                    m.strip() for m in avaliacao.melhorias.split(",") if m.strip()
                ]
            else:
                avaliacao.melhorias_processadas = []
        
        return templates.TemplateResponse(
            "comparacao.html", 
            {"request": request, "nome": nome, "avaliacoes": avaliacoes, "is_admin": True}
        )
    except Exception as e:
        return HTMLResponse(
            content=f"<div style='padding: 20px; font-family: Arial;'><h1>Erro no Sistema</h1><p><strong>Detalhes:</strong> {str(e)}</p><p><a href='/admin/alunos' style='color: #007bff;'>Voltar ao Painel Admin</a> | <a href='/login' style='color: #007bff;'>Fazer Login</a></p></div>",
            status_code=500
        )

@app.get("/admin/relatorio/{nome}", response_class=HTMLResponse)
async def admin_relatorio_aluno(request: Request, nome: str, db: Session = Depends(get_db), auth: bool = Depends(require_auth)):
    """Gera relatório em PDF/impressão para um aluno (rota protegida)"""
    try:
        avaliacoes = db.query(Avaliacao).filter(
            Avaliacao.nome == nome
        ).order_by(Avaliacao.data.desc()).all()
        
        for avaliacao in avaliacoes:
            if avaliacao.melhorias:
                avaliacao.melhorias_processadas = [
                    m.strip() for m in avaliacao.melhorias.split(",") if m.strip()
                ]
            else:
                avaliacao.melhorias_processadas = []
        
        return templates.TemplateResponse(
            "relatorio.html", 
            {"request": request, "nome": nome, "avaliacoes": avaliacoes, "is_admin": True}
        )
    except Exception as e:
        return HTMLResponse(
            content=f"<div style='padding: 20px; font-family: Arial;'><h1>Erro no Sistema</h1><p><strong>Detalhes:</strong> {str(e)}</p><p><a href='/admin/alunos' style='color: #007bff;'>Voltar ao Painel Admin</a> | <a href='/login' style='color: #007bff;'>Fazer Login</a></p></div>",
            status_code=500
        )

# ==================== ROTAS PÚBLICAS BÁSICAS (sem autenticação) ====================

@app.get("/alunos", response_class=HTMLResponse)
async def lista_alunos(request: Request, db: Session = Depends(get_db), auth: bool = Depends(require_auth)):
    """Lista todos os alunos (apenas para admins)"""
    try:
        alunos_query = db.query(Avaliacao.nome).distinct().all()
        alunos = [aluno[0] for aluno in alunos_query]
        alunos.sort()
        
        return templates.TemplateResponse(
            "alunos.html", 
            {"request": request, "alunos": alunos}
        )
    except Exception as e:
        return HTMLResponse(
            content=f"<div style='padding: 20px; font-family: Arial;'><h1>Erro no Sistema</h1><p><strong>Detalhes:</strong> {str(e)}</p><p><a href='/admin/alunos' style='color: #007bff;'>Voltar ao Painel Admin</a> | <a href='/login' style='color: #007bff;'>Fazer Login</a></p></div>",
            status_code=500
        )

@app.get("/meu-historico", response_class=HTMLResponse)
async def meu_historico(request: Request, aluno: Aluno = Depends(get_current_aluno), db: Session = Depends(get_db), is_admin: bool = Depends(is_admin_user)):
    """Exibe histórico do aluno logado (apenas suas próprias avaliações)"""
    try:
        # Buscar avaliações apenas do aluno logado
        avaliacoes = db.query(Avaliacao).filter(
            Avaliacao.aluno_id == aluno.id
        ).order_by(Avaliacao.data.desc()).all()

        for avaliacao in avaliacoes:
            if avaliacao.melhorias:
                avaliacao.melhorias_processadas = [
                    m.strip() for m in avaliacao.melhorias.split(",") if m.strip()
                ]
            else:
                avaliacao.melhorias_processadas = []

        return templates.TemplateResponse(
            "historico.html",
            {"request": request, "nome": aluno.nome, "avaliacoes": avaliacoes, "is_admin": is_admin, "aluno": aluno}
        )
    except Exception as e:
        return render_safe_error(
            request=request,
            title="Erro no Sistema",
            message="Ocorreu um erro interno. Tente novamente ou entre em contato com o suporte.",
            error_details=str(e),
            back_url="/admin/alunos"
        )

def avaliacoes_para_json(avaliacoes):
    """Converte lista de avaliações para formato JSON serializável"""
    avaliacoes_json = []
    for avaliacao in avaliacoes:
        avaliacao_dict = {
            'id': avaliacao.id,
            'nome': avaliacao.nome,
            'data': avaliacao.data.isoformat() if avaliacao.data else None,
            'peso_kg': getattr(avaliacao, 'peso_kg', None),
            'altura_cm': getattr(avaliacao, 'altura_cm', None),
            # Medidas essenciais
            'pescoco_cm': getattr(avaliacao, 'circunferencia_pescoco', None),
            'cintura_cm': getattr(avaliacao, 'circunferencia_cintura', None),
            'quadril_cm': getattr(avaliacao, 'circunferencia_quadril', None),
            'melhorias_processadas': getattr(avaliacao, 'melhorias_processadas', [])
        }
        avaliacoes_json.append(avaliacao_dict)
    return avaliacoes_json

@app.get("/meu-progresso", response_class=HTMLResponse)
async def meu_progresso(request: Request, aluno: Aluno = Depends(get_current_aluno), db: Session = Depends(get_db), is_admin: bool = Depends(is_admin_user)):
    """Compara o progresso do aluno logado (apenas suas próprias avaliações)"""
    try:
        # Buscar avaliações apenas do aluno logado
        avaliacoes = db.query(Avaliacao).filter(
            Avaliacao.aluno_id == aluno.id
        ).order_by(Avaliacao.data.asc()).all()

        for avaliacao in avaliacoes:
            if avaliacao.melhorias:
                avaliacao.melhorias_processadas = [
                    m.strip() for m in avaliacao.melhorias.split(",") if m.strip()
                ]
            else:
                avaliacao.melhorias_processadas = []

        # Converter para formato JSON serializável para o JavaScript
        avaliacoes_json = avaliacoes_para_json(avaliacoes)

        return templates.TemplateResponse(
            "comparacao.html",
            {"request": request, "nome": aluno.nome, "avaliacoes": avaliacoes, "avaliacoes_json": avaliacoes_json, "is_admin": is_admin, "aluno": aluno}
        )
    except Exception as e:
        error_log(f"Erro em meu_progresso para aluno {aluno.nome if 'aluno' in locals() else 'desconhecido'}: {str(e)}")

        # Renderizar página de erro segura sem perder a sessão
        error_html = f"<!DOCTYPE html><html lang='pt-br'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width, initial-scale=1'><title>Erro no Sistema - MoniPersonal</title><link href='https://cdn.jsdelivr.net/npm/bootstrap-dark-5@1.1.3/dist/css/bootstrap-dark.min.css' rel='stylesheet'><link rel='stylesheet' href='https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.1/font/bootstrap-icons.css'><style>body {{ background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%); color: #ffffff; min-height: 100vh; }} .card {{ border: none; border-radius: 20px; box-shadow: 0 8px 32px rgba(214, 51, 132, 0.3); background: rgba(255, 255, 255, 0.1); backdrop-filter: blur(10px); }}</style></head><body><div class='container mt-5'><div class='row justify-content-center'><div class='col-md-8'><div class='card'><div class='card-header bg-danger text-white'><h4><i class='bi bi-exclamation-triangle me-2'></i>Erro no Sistema</h4></div><div class='card-body'><h5>Não foi possível carregar sua comparação de progresso</h5><p class='text-muted'>Ocorreu um erro temporário. Suas informações estão seguras.</p><div class='mt-4'><a href='/meu-historico' class='btn btn-primary me-2'><i class='bi bi-clock-history me-1'></i>Ver Histórico</a><a href='/formulario' class='btn btn-success me-2'><i class='bi bi-plus-circle me-1'></i>Nova Avaliação</a><a href='/logout' class='btn btn-outline-secondary'><i class='bi bi-box-arrow-right me-1'></i>Sair e Tentar Novamente</a></div><details class='mt-4'><summary class='text-muted' style='cursor: pointer;'>Detalhes técnicos (para suporte)</summary><pre class='bg-light p-3 mt-2 small'><code>{str(e)}</code></pre></details></div></div></div></div></div></body></html>"
        return HTMLResponse(content=error_html, status_code=500)

@app.get("/comparar/{nome}", response_class=HTMLResponse)
async def comparar_progresso(request: Request, nome: str, db: Session = Depends(get_db), auth: bool = Depends(require_auth)):
    """Compara o progresso de um aluno (apenas admins)"""
    try:
        avaliacoes = db.query(Avaliacao).filter(
            Avaliacao.nome == nome
        ).order_by(Avaliacao.data.asc()).all()

        for avaliacao in avaliacoes:
            if avaliacao.melhorias:
                avaliacao.melhorias_processadas = [
                    m.strip() for m in avaliacao.melhorias.split(",") if m.strip()
                ]
            else:
                avaliacao.melhorias_processadas = []

        # Converter para formato JSON serializável para o JavaScript
        avaliacoes_json = avaliacoes_para_json(avaliacoes)

        return templates.TemplateResponse(
            "comparacao.html",
            {"request": request, "nome": nome, "avaliacoes": avaliacoes, "avaliacoes_json": avaliacoes_json, "is_admin": True}
        )
    except Exception as e:
        return HTMLResponse(
            content=f"<div style='padding: 20px; font-family: Arial;'><h1>Erro no Sistema</h1><p><strong>Detalhes:</strong> {str(e)}</p><p><a href='/admin/alunos' style='color: #007bff;'>Voltar ao Painel Admin</a> | <a href='/login' style='color: #007bff;'>Fazer Login</a></p></div>",
            status_code=500
        )

@app.get("/comparar/{nome}/pdf")
async def comparar_progresso_pdf(request: Request, nome: str, db: Session = Depends(get_db), user_data: dict = Depends(get_current_user)):
    """Exporta comparação de progresso em PDF - Admin ou Aluno (próprios dados)"""
    try:
        from fastapi.responses import Response
        import io
        from reportlab.lib.pagesizes import A4, letter
        from reportlab.lib import colors
        from reportlab.lib.units import inch
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from datetime import datetime
        import os

        # Verificar permissões
        if user_data["user_type"] == "aluno":
            # Aluno só pode baixar seus próprios dados
            aluno = user_data["user_data"]
            if aluno.nome != nome:
                logger.warning("pdf_access_denied", aluno_name=aluno.nome, requested_name=nome)
                raise HTTPException(
                    status_code=403,
                    detail="Você só pode exportar seus próprios dados"
                )

        # Buscar avaliações do aluno
        avaliacoes = db.query(Avaliacao).filter(
            Avaliacao.nome == nome
        ).order_by(Avaliacao.data.asc()).all()

        if not avaliacoes:
            return HTMLResponse(
                content="<h1>Erro</h1><p>Nenhuma avaliação encontrada para este aluno.</p>",
                status_code=404
            )

        # Criar buffer para o PDF
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        styles = getSampleStyleSheet()

        # Estilo customizado
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Title'],
            fontSize=18,
            spaceAfter=30,
            textColor=colors.HexColor('#d4af37')
        )

        header_style = ParagraphStyle(
            'CustomHeader',
            parent=styles['Heading2'],
            fontSize=14,
            spaceAfter=12,
            textColor=colors.HexColor('#1a1a1a')
        )

        # Conteúdo do PDF
        story = []

        # Logo (se existir)
        logo_path = "static/img/logo-monipersonal.png"
        if os.path.exists(logo_path):
            try:
                logo = Image(logo_path, width=2*inch, height=2*inch)
                story.append(logo)
                story.append(Spacer(1, 12))
            except:
                pass

        # Título
        title = Paragraph(f"Relatório de Progresso - {nome}", title_style)
        story.append(title)
        story.append(Spacer(1, 12))

        # Informações gerais
        info = Paragraph(f"<b>Data do relatório:</b> {datetime.now().strftime('%d/%m/%Y às %H:%M')}<br/>"
                        f"<b>Total de avaliações:</b> {len(avaliacoes)}<br/>"
                        f"<b>Período:</b> {avaliacoes[0].data.strftime('%d/%m/%Y')} a {avaliacoes[-1].data.strftime('%d/%m/%Y')}",
                        styles['Normal'])
        story.append(info)
        story.append(Spacer(1, 20))

        # Tabela comparativa
        if len(avaliacoes) >= 2:
            story.append(Paragraph("Comparação de Evolução", header_style))

            # Dados para tabela
            table_data = [['Métrica', 'Primeira Avaliação', 'Última Avaliação', 'Evolução']]

            primeira = avaliacoes[0]
            ultima = avaliacoes[-1]

            # Peso
            if primeira.peso_kg and ultima.peso_kg:
                evolucao_peso = ultima.peso_kg - primeira.peso_kg
                table_data.append([
                    'Peso (kg)',
                    f"{primeira.peso_kg:.1f}",
                    f"{ultima.peso_kg:.1f}",
                    f"{evolucao_peso:+.1f}"
                ])
            elif primeira.peso and ultima.peso:
                # Fallback para campo antigo, tentar converter
                try:
                    peso_primeira = float(primeira.peso.replace(',', '.'))
                    peso_ultima = float(ultima.peso.replace(',', '.'))
                    evolucao_peso = peso_ultima - peso_primeira
                    table_data.append([
                        'Peso (kg)',
                        f"{peso_primeira:.1f}",
                        f"{peso_ultima:.1f}",
                        f"{evolucao_peso:+.1f}"
                    ])
                except (ValueError, AttributeError):
                    pass

            # IMC
            if primeira.imc and ultima.imc:
                evolucao_imc = ultima.imc - primeira.imc
                table_data.append([
                    'IMC',
                    f"{primeira.imc:.1f}",
                    f"{ultima.imc:.1f}",
                    f"{evolucao_imc:+.1f}"
                ])

            # Medidas corporais (usar novos campos)
            medidas_campos = [
                'circunferencia_torax', 'circunferencia_cintura', 'circunferencia_quadril',
                'circunferencia_braco_direito', 'circunferencia_braco_esquerdo',
                'circunferencia_coxa_direita', 'circunferencia_coxa_esquerda'
            ]
            medidas_nomes = [
                'Tórax', 'Cintura', 'Quadril',
                'Braço Direito', 'Braço Esquerdo',
                'Coxa Direita', 'Coxa Esquerda'
            ]

            for campo, nome in zip(medidas_campos, medidas_nomes):
                val_primeira = getattr(primeira, campo, None)
                val_ultima = getattr(ultima, campo, None)

                if val_primeira and val_ultima:
                    try:
                        evolucao = val_ultima - val_primeira
                        table_data.append([
                            f'{nome} (cm)',
                            f"{val_primeira:.1f}",
                            f"{val_ultima:.1f}",
                            f"{evolucao:+.1f}"
                        ])
                    except:
                        pass

            # Criar tabela
            if len(table_data) > 1:
                table = Table(table_data)
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#d4af37')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 12),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                story.append(table)
                story.append(Spacer(1, 20))

        # Histórico de avaliações
        story.append(Paragraph("Histórico Detalhado", header_style))

        for i, avaliacao in enumerate(avaliacoes):
            story.append(Paragraph(f"<b>Avaliação {i+1} - {avaliacao.data.strftime('%d/%m/%Y')}</b>", styles['Heading3']))

            # Dados da avaliação
            peso_display = "N/A"
            if avaliacao.peso_kg:
                peso_display = f"{avaliacao.peso_kg:.1f}"
            elif avaliacao.peso:
                peso_display = str(avaliacao.peso)

            dados = f"<b>Peso:</b> {peso_display} kg<br/>"
            if avaliacao.imc:
                dados += f"<b>IMC:</b> {avaliacao.imc:.1f}<br/>"

            # Adicionar altura se disponível
            if avaliacao.altura_cm:
                dados += f"<b>Altura:</b> {avaliacao.altura_cm:.0f} cm<br/>"

            story.append(Paragraph(dados, styles['Normal']))

            # Observações se houver
            if avaliacao.sugestao_geral and avaliacao.sugestao_geral.strip():
                story.append(Paragraph(f"<b>Observações:</b> {avaliacao.sugestao_geral}", styles['Normal']))

            story.append(Spacer(1, 12))

        # Construir PDF
        doc.build(story)
        buffer.seek(0)

        # Retornar PDF com nome correto do aluno
        # Usar o nome do primeiro aluno das avaliações ou o nome passado como parâmetro
        nome_aluno = avaliacoes[0].nome if avaliacoes else nome
        data_hoje = now_sao_paulo().strftime('%d-%m-%Y')
        filename = f"relatorio_progresso_{nome_aluno.replace(' ', '_')}_{data_hoje}.pdf"

        return Response(
            content=buffer.getvalue(),
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )

    except ImportError as e:
        error_log(f"Erro de importação para PDF: {str(e)}")
        return HTMLResponse(
            content="<h1>Erro</h1><p>Bibliotecas necessárias para PDF não estão instaladas. Entre em contato com o administrador.</p>",
            status_code=500
        )
    except Exception as e:
        error_log(f"Erro ao gerar PDF de comparação: {str(e)}")
        return HTMLResponse(
            content=f"<h1>Erro</h1><p>Não foi possível gerar o PDF: {str(e)}</p>",
            status_code=500
        )

@app.get("/relatorio/{nome}", response_class=HTMLResponse)
async def relatorio_aluno(request: Request, nome: str, db: Session = Depends(get_db), auth: bool = Depends(require_auth)):
    """Gera relatório em PDF/impressão para um aluno (apenas admins)"""
    try:
        avaliacoes = db.query(Avaliacao).filter(
            Avaliacao.nome == nome
        ).order_by(Avaliacao.data.desc()).all()
        
        for avaliacao in avaliacoes:
            if avaliacao.melhorias:
                avaliacao.melhorias_processadas = [
                    m.strip() for m in avaliacao.melhorias.split(",") if m.strip()
                ]
            else:
                avaliacao.melhorias_processadas = []
        
        return templates.TemplateResponse(
            "relatorio.html", 
            {"request": request, "nome": nome, "avaliacoes": avaliacoes}
        )
    except Exception as e:
        return HTMLResponse(
            content=f"<div style='padding: 20px; font-family: Arial;'><h1>Erro no Sistema</h1><p><strong>Detalhes:</strong> {str(e)}</p><p><a href='/admin/alunos' style='color: #007bff;'>Voltar ao Painel Admin</a> | <a href='/login' style='color: #007bff;'>Fazer Login</a></p></div>",
            status_code=500
        )

# ==================== ROTA DE INICIALIZAÇÃO ====================

@app.get("/init-db", response_class=HTMLResponse)
async def init_database(request: Request, force: str = None, confirm: str = None, admin_auth: bool = Depends(require_auth)):
    """Inicializa o banco de dados criando as tabelas - REQUER AUTENTICAÇÃO ADMIN"""
    try:
        if force == "true":
            # Dupla confirmação necessária para operações destrutivas
            if confirm != "DELETE_ALL_DATA":
                return HTMLResponse(
                    content="""
                    <div style="font-family: Arial; padding: 20px; max-width: 600px; margin: 0 auto;">
                        <h1>CONFIRMAÇÃO NECESSÁRIA</h1>
                        <div style="background: #dc3545; color: white; padding: 20px; border-radius: 5px; margin: 20px 0;">
                            <h3>OPERAÇÃO DESTRUTIVA</h3>
                            <p><strong>ATENÇÃO: Esta operação irá DELETAR TODOS OS DADOS!</strong></p>
                            <ul>
                                <li>Todas as avaliações serão perdidas</li>
                                <li>Todos os usuários serão removidos</li>
                                <li>Todo o histórico será apagado</li>
                                <li><strong>NÃO HÁ COMO DESFAZER!</strong></li>
                            </ul>
                        </div>

                        <h3>Para confirmar, digite "DELETE_ALL_DATA" no campo abaixo:</h3>
                        <form method="get">
                            <input type="hidden" name="force" value="true">
                            <input type="text" name="confirm" placeholder="Digite: DELETE_ALL_DATA"
                                   style="width: 300px; padding: 10px; font-size: 16px; margin: 10px 0;">
                            <br>
                            <button type="submit" style="background: #dc3545; color: white; padding: 15px 30px; border: none; font-size: 16px; cursor: pointer;">
                                CONFIRMAR DELEÇÃO TOTAL
                            </button>
                        </form>

                        <div style="margin-top: 30px;">
                            <a href="/init-db" style="background: #28a745; color: white; padding: 10px 20px; text-decoration: none;">
                                Voltar ao Modo Seguro
                            </a>
                            <a href="/admin/alunos" style="background: #6c757d; color: white; padding: 10px 20px; text-decoration: none; margin-left: 10px;">
                                Cancelar e Voltar
                            </a>
                        </div>
                    </div>
                    """,
                    status_code=200
                )

            # Log crítico da operação destrutiva
            error_log(f"🚨 OPERAÇÃO DESTRUTIVA CONFIRMADA - Admin deletou todos os dados! IP: {request.client.host}")

            # Backup rápido antes da deleção
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            database_url = os.getenv("DATABASE_URL", "sqlite:///./monipersonal.db")

            try:
                if database_url.startswith("postgresql"):
                    # Backup PostgreSQL antes da deleção
                    backup_name = f"backup_before_deletion_{timestamp}.sql"
                    import subprocess
                    from urllib.parse import urlparse

                    parsed = urlparse(database_url)
                    cmd = ["pg_dump", f"--host={parsed.hostname or 'localhost'}",
                          f"--port={parsed.port or 5432}", f"--username={parsed.username}",
                          f"--dbname={parsed.path[1:]}", "--no-password", "--clean"]

                    env = os.environ.copy()
                    if parsed.password:
                        env["PGPASSWORD"] = parsed.password

                    with open(backup_name, 'w') as backup_file:
                        result = subprocess.run(cmd, stdout=backup_file, stderr=subprocess.PIPE, env=env, text=True)

                    if result.returncode == 0:
                        info_log(f"Backup PostgreSQL criado antes da deleção: {backup_name}")
                    else:
                        error_log(f"Erro no backup PostgreSQL antes da deleção: {result.stderr}")
                else:
                    # Backup SQLite antes da deleção
                    backup_name = f"backup_before_deletion_{timestamp}.db"
                    sqlite_db_path = database_url.replace("sqlite:///", "").replace("sqlite://", "")

                    if os.path.exists(sqlite_db_path):
                        shutil.copy2(sqlite_db_path, backup_name)
                        info_log(f"Backup SQLite criado antes da deleção: {backup_name}")
                    else:
                        info_log(f"Arquivo SQLite não encontrado para backup: {sqlite_db_path}")

            except Exception as backup_error:
                error_log(f"Erro ao criar backup antes da deleção: {backup_error}")

            Base.metadata.drop_all(bind=engine)
            Base.metadata.create_all(bind=engine)
        else:
            # Modo seguro: apenas cria tabelas se não existirem
            info_log("🔒 SAFE INIT: Criando apenas tabelas que não existem")
            Base.metadata.create_all(bind=engine)
        
        # Testa a conexão inserindo um registro de teste
        db = SessionLocal()
        test_avaliacao = Avaliacao(
            nome="Sistema Teste",
            peso="0kg",
            medidas="Teste inicial",
            faltou_algo="Nada",
            gostou_mais_menos="Teste",
            meta_agua="Teste",
            alimentacao="Teste",
            melhorias="",  # Campo removido
            outros_melhorias="",  # Campo removido
            pedido_especial="",
            sugestao_geral=""
        )
        db.add(test_avaliacao)
        db.commit()
        db.close()
        
        mode_message = "TABELAS REMOVIDAS E RECRIADAS!" if force == "true" else "Modo seguro: apenas tabelas novas foram criadas"

        bg_color = '#fff3cd' if force == 'true' else '#d1ecf1'
        html_content = f"<div style='font-family: Arial; padding: 20px; max-width: 600px; margin: 0 auto;'><h1>Banco de dados inicializado com sucesso!</h1><div style='background: {bg_color}; padding: 15px; border-radius: 5px; margin: 20px 0;'><strong>{mode_message}</strong></div><h3>Opções de navegação:</h3><ul style='list-style-type: none; padding: 0;'><li style='margin: 10px 0;'><a href='/login' style='color: #0d6efd; text-decoration: none;'>Fazer Login</a></li><li style='margin: 10px 0;'><a href='/registro' style='color: #0d6efd; text-decoration: none;'>Registrar Novo Usuário</a></li><li style='margin: 10px 0;'><a href='/formulario' style='color: #0d6efd; text-decoration: none;'>Ir para Formulário</a></li><li style='margin: 10px 0;'><a href='/admin/alunos' style='color: #0d6efd; text-decoration: none;'>Área Administrativa</a></li></ul><div style='background: #f8d7da; padding: 15px; border-radius: 5px; margin-top: 20px; color: #721c24;'><strong>AVISO IMPORTANTE:</strong><br>Se você perdeu dados por engano, entre em contato com o administrador do sistema imediatamente. O parâmetro ?force=true remove TODOS os dados existentes.</div></div>"
        return HTMLResponse(content=html_content, status_code=200)
    except Exception as e:
        return HTMLResponse(
            content=f"<h1>Erro ao inicializar banco:</h1><p><strong>Erro:</strong> {str(e)}</p><p><strong>Tipo:</strong> {type(e).__name__}</p><p><a href='/formulario'>Voltar ao formulário</a></p>",
            status_code=500
        )

@app.get("/admin/backup", response_class=HTMLResponse)
async def backup_page(request: Request, admin_auth: bool = Depends(require_auth)):
    """Exibe página de backup - APENAS ADMIN"""
    environment = os.getenv("ENVIRONMENT", "production")
    return templates.TemplateResponse(
        "admin_backup.html",
        {"request": request, "environment": environment}
    )

@app.post("/admin/backup", response_class=HTMLResponse)
async def criar_backup_manual(request: Request, admin_auth: bool = Depends(require_auth)):
    """Cria backup manual do banco de dados - APENAS ADMIN"""
    try:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        database_url = os.getenv("DATABASE_URL", "sqlite:///./monipersonal.db")

        if database_url.startswith("postgresql"):
            # Backup PostgreSQL
            import subprocess
            backup_name = f"backup_manual_{timestamp}.sql"

            # Extrair informações de conexão da URL do PostgreSQL
            from urllib.parse import urlparse
            parsed = urlparse(database_url)

            # Comando pg_dump para PostgreSQL
            cmd = [
                "pg_dump",
                f"--host={parsed.hostname or 'localhost'}",
                f"--port={parsed.port or 5432}",
                f"--username={parsed.username}",
                f"--dbname={parsed.path[1:]}",  # Remove a barra inicial
                "--no-password",
                "--verbose",
                "--clean",
                "--no-owner",
                "--no-privileges"
            ]

            # Definir senha via environment se disponível
            env = os.environ.copy()
            if parsed.password:
                env["PGPASSWORD"] = parsed.password

            # Executar pg_dump
            with open(backup_name, 'w') as backup_file:
                result = subprocess.run(cmd, stdout=backup_file, stderr=subprocess.PIPE, env=env, text=True)

            if result.returncode == 0:
                info_log(f"Backup PostgreSQL criado: {backup_name}")
                success_message = f"Backup PostgreSQL criado com sucesso em {datetime.now().strftime('%d/%m/%Y às %H:%M:%S')}"
            else:
                error_msg = result.stderr or "Erro desconhecido no pg_dump"
                raise Exception(f"Erro no pg_dump: {error_msg}")

        else:
            # Backup SQLite
            backup_name = f"backup_manual_{timestamp}.db"
            sqlite_db_path = database_url.replace("sqlite:///", "").replace("sqlite://", "")

            if os.path.exists(sqlite_db_path):
                import shutil
                shutil.copy2(sqlite_db_path, backup_name)
                info_log(f"Backup SQLite criado: {backup_name}")
                success_message = f"Backup SQLite criado com sucesso em {datetime.now().strftime('%d/%m/%Y às %H:%M:%S')}"
            else:
                raise Exception(f"Arquivo SQLite não encontrado: {sqlite_db_path}")

        return templates.TemplateResponse(
            "admin_backup.html",
            {
                "request": request,
                "success": True,
                "backup_name": backup_name,
                "message": success_message,
                "environment": os.getenv("ENVIRONMENT", "production")
            }
        )

    except Exception as e:
        error_log(f"Erro ao criar backup manual: {str(e)}")
        return templates.TemplateResponse(
            "admin_backup.html",
            {
                "request": request,
                "error": f"Erro ao criar backup: {str(e)}",
                "environment": os.getenv("ENVIRONMENT", "production")
            }
        )

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)