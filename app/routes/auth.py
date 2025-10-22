"""
Rotas de autenticação (login, logout, registro)
"""
from fastapi import APIRouter, Request, Form, Depends, Cookie
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
import structlog

from database import get_db
from models import Aluno, Usuario
from app.services.auth_service import (
    verify_password, create_simple_jwt, verify_simple_jwt,
    ADMIN_PASSWORD_HASH, hash_password, create_session_token,
    invalidate_session
)
from app.core.config import SECURE_COOKIE_CONFIG, SESSION_COOKIE_NAME, RATE_LIMITS
from app.middleware.rate_limiting import setup_rate_limiting
from app.utils.logging import debug_log

# Configurar router
router = APIRouter()

# Configurar templates
templates = Jinja2Templates(directory="templates")

# Logger
logger = structlog.get_logger()


def is_admin_user(session_token: str = Cookie(None, alias=SESSION_COOKIE_NAME)) -> bool:
    """Verifica se o usuário atual é admin"""
    if not session_token:
        return False

    jwt_data = verify_simple_jwt(session_token)
    return jwt_data and jwt_data.get("user_type") == "admin"


def clear_session(token: str):
    """Limpa uma sessão específica"""
    invalidate_session(token)


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request, user_type: str = "aluno", is_admin: bool = Depends(is_admin_user)):
    """Página de login unificada para alunos e admins"""
    return templates.TemplateResponse(
        "login.html",
        {"request": request, "user_type": user_type, "is_admin": is_admin, "aluno": None}
    )


@router.post("/login")
async def login_submit(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    user_type: str = Form("aluno"),
    db: Session = Depends(get_db)
):
    """Processa login de alunos e admins"""
    client_ip = request.client.host if request.client else "unknown"

    logger.info("login_attempt",
                email=email,
                user_type=user_type,
                ip=client_ip,
                user_agent=request.headers.get("user-agent", "unknown"))

    # Verificar se é admin
    if email == "admin@monipersonal.com" and verify_password(password, ADMIN_PASSWORD_HASH):
        logger.info("admin_login_success", email=email, ip=client_ip)

        # Criar token JWT
        token = create_simple_jwt("admin", 0)

        response = RedirectResponse(url="/admin/dashboard", status_code=303)
        response.set_cookie(
            key=SESSION_COOKIE_NAME,
            value=token,
            **SECURE_COOKIE_CONFIG
        )
        return response

    # Verificar login de aluno
    if user_type == "aluno":
        aluno = db.query(Aluno).filter(Aluno.email == email, Aluno.ativo == True).first()

        if aluno and verify_password(password, aluno.senha_hash):
            logger.info("student_login_success",
                       email=email,
                       user_id=aluno.id,
                       ip=client_ip)

            # Criar token JWT
            token = create_simple_jwt("aluno", aluno.id)

            response = RedirectResponse(url="/meu-historico", status_code=303)
            response.set_cookie(
                key=SESSION_COOKIE_NAME,
                value=token,
                **SECURE_COOKIE_CONFIG
            )
            return response

    # Login falhou
    logger.warning("login_failed",
                  email=email,
                  user_type=user_type,
                  ip=client_ip)

    return templates.TemplateResponse(
        "login.html",
        {
            "request": request,
            "error": "Email ou senha incorretos",
            "user_type": user_type,
            "is_admin": False,
            "aluno": None
        }
    )


@router.get("/logout")
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

    # Criar response de logout
    response = RedirectResponse(url="/login", status_code=303)

    # Limpar cookie
    response.delete_cookie(
        key=SESSION_COOKIE_NAME,
        path="/",
        domain=None
    )

    return response


@router.get("/registro", response_class=HTMLResponse)
async def registro_page(request: Request):
    """Página de registro para novos alunos"""
    return templates.TemplateResponse("registro.html", {"request": request})


@router.post("/registro")
async def registro_submit(
    request: Request,
    nome: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    confirm_password: str = Form(...),
    telefone: str = Form(...),
    data_nascimento: str = Form(...),
    db: Session = Depends(get_db)
):
    """Processa registro de novos alunos"""
    try:
        # Validar senhas
        if password != confirm_password:
            return templates.TemplateResponse(
                "registro.html",
                {"request": request, "error": "As senhas não coincidem"}
            )

        # Verificar se email já existe
        existing_aluno = db.query(Aluno).filter(Aluno.email == email).first()
        if existing_aluno:
            return templates.TemplateResponse(
                "registro.html",
                {"request": request, "error": "Email já cadastrado"}
            )

        # Criar novo aluno
        novo_aluno = Aluno(
            nome=nome,
            email=email,
            telefone=telefone,
            senha_hash=hash_password(password),
            ativo=True
        )

        if data_nascimento:
            from datetime import datetime
            novo_aluno.data_nascimento = datetime.strptime(data_nascimento, "%Y-%m-%d").date()

        db.add(novo_aluno)
        db.commit()
        db.refresh(novo_aluno)

        logger.info("student_registration_success",
                   email=email,
                   user_id=novo_aluno.id)

        # Redirecionar para login com sucesso
        return RedirectResponse(url="/login?registered=true", status_code=303)

    except Exception as e:
        logger.error("registration_error", error=str(e), email=email)
        return templates.TemplateResponse(
            "registro.html",
            {"request": request, "error": f"Erro ao criar conta: {str(e)}"}
        )