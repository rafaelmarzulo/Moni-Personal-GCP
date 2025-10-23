"""
Rotas para alunos (formulário, histórico, etc.)
"""
from fastapi import APIRouter, Request, Form, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from datetime import datetime, date
import structlog

from app.core.database import get_db
from app.models import Aluno, Avaliacao
from app.middleware.auth import require_auth
from app.services.auth_service import verify_simple_jwt
from app.core.config import SESSION_COOKIE_NAME
from app.utils.logging import info_log, debug_log, error_log
from app.utils.datetime_utils import now_sao_paulo, utc_to_sao_paulo

# Configurar router
router = APIRouter(tags=["student"])

# Configurar templates
templates = Jinja2Templates(directory="templates")

# Logger
logger = structlog.get_logger()


@router.get("/meu-historico", response_class=HTMLResponse)
@require_auth(['aluno'])
async def meu_historico(
    request: Request,
    db: Session = Depends(get_db),
    session_data=None,
    jwt_data=None
):
    """Histórico pessoal do aluno logado"""
    try:
        # Obter ID do aluno logado
        aluno_id = None
        if jwt_data:
            aluno_id = jwt_data.get("user_id")
        elif session_data:
            aluno_id = session_data.get("user_id")

        if not aluno_id:
            debug_log("❌ HISTORICO: ID do aluno não encontrado")
            return RedirectResponse(url="/login")

        # Buscar aluno
        aluno = db.query(Aluno).filter(Aluno.id == aluno_id).first()
        if not aluno:
            debug_log(f"❌ HISTORICO: Aluno ID {aluno_id} não encontrado")
            return RedirectResponse(url="/login")

        # Buscar avaliações do aluno
        avaliacoes_raw = db.query(Avaliacao).filter(
            Avaliacao.aluno_id == aluno_id
        ).order_by(Avaliacao.data.desc()).all()

        # Converter tudo para tipos básicos Python para evitar problemas de serialização
        avaliacoes = []
        for av in avaliacoes_raw:
            data_local = utc_to_sao_paulo(av.data) if av.data else None

            # Criar dicionário com apenas tipos básicos
            avaliacao_dict = {
                'id': av.id,
                'peso_kg': float(av.peso_kg) if av.peso_kg else None,
                'altura_cm': float(av.altura_cm) if av.altura_cm else None,
                'imc': float(av.imc) if av.imc else None,
                'data': av.data.strftime('%Y-%m-%d %H:%M:%S') if av.data else None,
                'data_local': data_local.strftime('%Y-%m-%d %H:%M:%S') if data_local else None,
                'observacoes_medidas': str(av.observacoes_medidas) if av.observacoes_medidas else '',
                'percentual_gordura': float(av.percentual_gordura) if av.percentual_gordura else None,
                'circunferencia_cintura': float(av.circunferencia_cintura) if av.circunferencia_cintura else None,
                'circunferencia_quadril': float(av.circunferencia_quadril) if av.circunferencia_quadril else None
            }

            # Usar dicionário simples (sem SimpleNamespace)
            avaliacoes.append(avaliacao_dict)

        try:
            info_log(f"📊 HISTORICO: {len(avaliacoes)} avaliações para {aluno.nome}")
        except Exception as log_error:
            print(f"Erro no log: {log_error}")  # Log simples para debug

        # Converter aluno também
        aluno_dict = {
            'id': aluno.id,
            'nome': str(aluno.nome),
            'email': str(aluno.email)
        }

        return templates.TemplateResponse(
            "meu_historico.html",
            {
                "request": request,
                "aluno": aluno_dict,
                "avaliacoes": avaliacoes,
                "total_avaliacoes": len(avaliacoes),
                "is_admin": False
            }
        )

    except Exception as e:
        error_log(f"❌ HISTORICO: Erro: {str(e)}")
        return templates.TemplateResponse(
            "erro.html",
            {
                "request": request,
                "titulo": "Erro no Histórico",
                "mensagem": "Erro ao carregar seu histórico. Tente novamente.",
                "detalhes": str(e)
            }
        )


@router.get("/formulario", response_class=HTMLResponse)
@require_auth(['aluno'])
async def formulario_page(
    request: Request,
    db: Session = Depends(get_db),
    session_data=None,
    jwt_data=None
):
    """Página do formulário de avaliação"""
    try:
        # Obter ID do aluno logado
        aluno_id = None
        if jwt_data:
            aluno_id = jwt_data.get("user_id")
        elif session_data:
            aluno_id = session_data.get("user_id")

        if not aluno_id:
            return RedirectResponse(url="/login")

        # Buscar dados completos do aluno
        aluno = db.query(Aluno).filter(Aluno.id == aluno_id).first()
        if not aluno:
            return RedirectResponse(url="/login")

        debug_log(f"📝 FORMULARIO: Página acessada por {aluno.nome}")

        return templates.TemplateResponse(
            "formulario.html",
            {
                "request": request,
                "aluno": aluno,
                "aluno_nome": aluno.nome,
                "aluno_email": aluno.email,
                "data_atual": now_sao_paulo().strftime("%Y-%m-%d"),
                "is_admin": False
            }
        )

    except Exception as e:
        error_log(f"❌ FORMULARIO: Erro: {str(e)}")
        return templates.TemplateResponse(
            "erro.html",
            {
                "request": request,
                "titulo": "Erro no Formulário",
                "mensagem": "Erro ao carregar formulário. Tente novamente.",
                "detalhes": str(e)
            }
        )


@router.post("/formulario", response_class=HTMLResponse)
async def formulario_submit(
    request: Request,
    # Campos da avaliação física
    peso: float = Form(...),
    altura: float = Form(...),
    observacoes: str = Form(""),

    db: Session = Depends(get_db)
):
    """Processa submissão do formulário de avaliação"""
    try:
        debug_log(f"📝 FORMULARIO/SUBMIT: Recebendo dados - peso: {peso}kg, altura: {altura}cm")

        # Obter token de sessão
        session_token = request.cookies.get(SESSION_COOKIE_NAME)
        jwt_data = verify_simple_jwt(session_token) if session_token else None

        if not jwt_data or jwt_data.get("user_type") != "aluno":
            debug_log("❌ FORMULARIO/SUBMIT: Usuário não autenticado")
            return RedirectResponse(url="/login", status_code=303)

        aluno_id = jwt_data.get("user_id")

        # Buscar ou criar aluno
        aluno = db.query(Aluno).filter(Aluno.id == aluno_id).first()
        if not aluno:
            error_log(f"❌ FORMULARIO/SUBMIT: Aluno ID {aluno_id} não encontrado")
            return RedirectResponse(url="/login", status_code=303)

        # Criar nova avaliação
        nova_avaliacao = Avaliacao(
            aluno_id=aluno_id,
            nome=aluno.nome,  # Preencher com nome do aluno
            data=now_sao_paulo(),
            peso_kg=peso,
            altura_cm=altura,
            observacoes_medidas=observacoes or ""
        )

        # Calcular IMC
        if altura > 0:
            imc = peso / ((altura / 100) ** 2)
            nova_avaliacao.imc = round(imc, 2)

        db.add(nova_avaliacao)
        db.commit()
        db.refresh(nova_avaliacao)

        info_log(f"✅ FORMULARIO/SUBMIT: Nova avaliação criada para {aluno.nome} - IMC: {nova_avaliacao.imc}")

        # Redirecionar para histórico
        return RedirectResponse(url="/meu-historico?success=true", status_code=303)

    except ValueError as e:
        error_log(f"❌ FORMULARIO/SUBMIT: Erro de validação: {str(e)}")
        return templates.TemplateResponse(
            "formulario.html",
            {
                "request": request,
                "error": f"Dados inválidos: {str(e)}",
                "is_admin": False
            }
        )
    except Exception as e:
        error_log(f"❌ FORMULARIO/SUBMIT: Erro: {str(e)}")
        return templates.TemplateResponse(
            "formulario.html",
            {
                "request": request,
                "error": f"Erro ao salvar avaliação: {str(e)}",
                "is_admin": False
            }
        )


@router.get("/perfil", response_class=HTMLResponse)
@require_auth(['aluno'])
async def perfil_aluno(
    request: Request,
    db: Session = Depends(get_db),
    session_data=None,
    jwt_data=None
):
    """Página de perfil do aluno"""
    try:
        # Obter ID do aluno logado
        aluno_id = None
        if jwt_data:
            aluno_id = jwt_data.get("user_id")
        elif session_data:
            aluno_id = session_data.get("user_id")

        if not aluno_id:
            return RedirectResponse(url="/login")

        # Buscar aluno
        aluno = db.query(Aluno).filter(Aluno.id == aluno_id).first()
        if not aluno:
            return RedirectResponse(url="/login")

        debug_log(f"👤 PERFIL: Carregando perfil de {aluno.nome}")

        return templates.TemplateResponse(
            "perfil_aluno.html",
            {
                "request": request,
                "aluno": aluno,
                "is_admin": False
            }
        )

    except Exception as e:
        error_log(f"❌ PERFIL: Erro: {str(e)}")
        return templates.TemplateResponse(
            "erro.html",
            {
                "request": request,
                "titulo": "Erro no Perfil",
                "mensagem": "Erro ao carregar perfil. Tente novamente.",
                "detalhes": str(e)
            }
        )