"""
Rotas administrativas do sistema MoniPersonal
"""
from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import func
import structlog

from app.core.database import get_db
from app.models import Aluno, Avaliacao
from app.middleware.auth import require_admin
from app.utils.logging import info_log, debug_log, error_log
from app.utils.datetime_utils import now_sao_paulo, utc_to_sao_paulo

# Configurar router
router = APIRouter(prefix="/admin", tags=["admin"])

# Configurar templates
templates = Jinja2Templates(directory="templates")

# Logger
logger = structlog.get_logger()


@router.get("/dashboard", response_class=HTMLResponse)
async def admin_dashboard(request: Request):
    """Dashboard administrativo principal"""
    debug_log("🎯 ADMIN/DASHBOARD: Rota acessada")

    return templates.TemplateResponse(
        "admin_dashboard.html",
        {
            "request": request,
            "title": "Dashboard Administrativo",
            "message": "🚧 Dashboard em desenvolvimento - Fase 2 da modularização"
        }
    )


@router.get("/alunos", response_class=HTMLResponse)
@require_admin()
async def admin_lista_alunos(
    request: Request,
    db: Session = Depends(get_db),
    session_data=None,
    jwt_data=None
):
    """Lista todos os alunos registrados (rota protegida)"""
    try:
        debug_log("🎯 ADMIN/ALUNOS: Rota acessada com sucesso")

        # Buscar todos os alunos
        alunos = db.query(Aluno).order_by(Aluno.nome).all()

        # Buscar estatísticas básicas para cada aluno
        alunos_stats = []
        for aluno in alunos:
            total_avaliacoes = db.query(Avaliacao).filter(Avaliacao.aluno_id == aluno.id).count()

            alunos_stats.append({
                "aluno": aluno,
                "total_avaliacoes": total_avaliacoes,
                "ultima_avaliacao": None  # TODO: implementar na próxima iteração
            })

        info_log(f"📊 ADMIN/ALUNOS: {len(alunos)} alunos encontrados")

        return templates.TemplateResponse(
            "admin_alunos.html",
            {
                "request": request,
                "alunos": alunos_stats,
                "total_alunos": len(alunos),
                "is_admin": True
            }
        )

    except Exception as e:
        error_log(f"❌ ADMIN/ALUNOS: Erro ao carregar lista: {str(e)}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor")


@router.get("/aluno/{nome}", response_class=HTMLResponse)
@require_admin()
async def admin_historico_aluno(
    request: Request,
    nome: str,
    db: Session = Depends(get_db),
    session_data=None,
    jwt_data=None
):
    """Exibe histórico de um aluno específico (rota protegida)"""
    try:
        debug_log(f"🎯 ADMIN/ALUNO/{nome}: Carregando histórico")

        # Buscar aluno
        aluno = db.query(Aluno).filter(Aluno.nome.ilike(f"%{nome}%")).first()

        if not aluno:
            raise HTTPException(status_code=404, detail="Aluno não encontrado")

        # Buscar avaliações do aluno
        avaliacoes = db.query(Avaliacao).filter(
            Avaliacao.aluno_id == aluno.id
        ).order_by(Avaliacao.data.desc()).all()

        # Converter timestamps para timezone local
        for avaliacao in avaliacoes:
            if avaliacao.data:
                avaliacao.data_local = utc_to_sao_paulo(avaliacao.data)

        info_log(f"📊 ADMIN/ALUNO: {len(avaliacoes)} avaliações encontradas para {aluno.nome}")

        return templates.TemplateResponse(
            "admin_historico_aluno.html",
            {
                "request": request,
                "aluno": aluno,
                "avaliacoes": avaliacoes,
                "total_avaliacoes": len(avaliacoes),
                "is_admin": True
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        error_log(f"❌ ADMIN/ALUNO/{nome}: Erro: {str(e)}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor")


@router.get("/debug-alunos")
@require_admin()
async def admin_debug_alunos(
    request: Request,
    db: Session = Depends(get_db),
    session_data=None,
    jwt_data=None
):
    """Endpoint de debug para verificar problemas de login dos alunos"""
    try:
        debug_log("🔧 ADMIN/DEBUG: Verificando configuração de alunos")

        alunos = db.query(Aluno).all()

        debug_info = []
        for aluno in alunos:
            aluno_info = {
                "id": aluno.id,
                "nome": aluno.nome,
                "email": aluno.email,
                "ativo": aluno.ativo,
                "tem_senha": bool(aluno.senha_hash),
                "tamanho_hash": len(aluno.senha_hash) if aluno.senha_hash else 0,
                "tipo_hash": "bcrypt" if aluno.senha_hash and aluno.senha_hash.startswith("$2") else "sha256"
            }
            debug_info.append(aluno_info)

        info_log(f"🔧 ADMIN/DEBUG: {len(alunos)} alunos analisados")

        return {
            "success": True,
            "total_alunos": len(alunos),
            "alunos": debug_info,
            "timestamp": now_sao_paulo().isoformat()
        }

    except Exception as e:
        error_log(f"❌ ADMIN/DEBUG: Erro: {str(e)}")
        return {"error": f"Erro ao verificar alunos: {str(e)}"}


@router.get("/stats")
@require_admin()
async def admin_estatisticas(
    request: Request,
    db: Session = Depends(get_db),
    session_data=None,
    jwt_data=None
):
    """Estatísticas gerais do sistema"""
    try:
        debug_log("📊 ADMIN/STATS: Calculando estatísticas")

        # Estatísticas básicas
        total_alunos = db.query(Aluno).count()
        total_avaliacoes = db.query(Avaliacao).count()
        alunos_ativos = db.query(Aluno).filter(Aluno.ativo == True).count()

        # Avaliações por mês (últimos 6 meses)
        avaliacoes_recentes = db.query(
            func.count(Avaliacao.id)
        ).filter(
            Avaliacao.data >= func.now() - func.interval('6 months')
        ).scalar()

        stats = {
            "total_alunos": total_alunos,
            "alunos_ativos": alunos_ativos,
            "total_avaliacoes": total_avaliacoes,
            "avaliacoes_recentes": avaliacoes_recentes,
            "timestamp": now_sao_paulo().isoformat()
        }

        info_log(f"📊 ADMIN/STATS: Estatísticas calculadas - {total_alunos} alunos, {total_avaliacoes} avaliações")

        return stats

    except Exception as e:
        error_log(f"❌ ADMIN/STATS: Erro: {str(e)}")
        return {"error": f"Erro ao calcular estatísticas: {str(e)}"}