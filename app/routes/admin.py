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
@require_admin()
async def admin_dashboard(
    request: Request,
    db: Session = Depends(get_db),
    session_data=None,
    jwt_data=None
):
    """Dashboard administrativo principal"""
    try:
        debug_log("🎯 ADMIN/DASHBOARD: Rota acessada com sucesso")

        # Carregar estatísticas básicas para exibição imediata
        total_alunos = db.query(Aluno).count()
        total_avaliacoes = db.query(Avaliacao).count()
        alunos_ativos = db.query(Aluno).filter(Aluno.ativo == True).count()

        # Avaliações recentes (últimos 30 dias)
        from datetime import timedelta
        data_limite = now_sao_paulo() - timedelta(days=30)
        avaliacoes_recentes = db.query(Avaliacao).filter(
            Avaliacao.data >= data_limite
        ).count()

        info_log(f"📊 ADMIN/DASHBOARD: Estatísticas carregadas - {total_alunos} alunos, {total_avaliacoes} avaliações")

        return templates.TemplateResponse(
            "admin_dashboard.html",
            {
                "request": request,
                "title": "Dashboard Administrativo",
                "message": "Sistema MoniPersonal operacional",
                "total_alunos": total_alunos,
                "total_avaliacoes": total_avaliacoes,
                "alunos_ativos": alunos_ativos,
                "avaliacoes_recentes": avaliacoes_recentes,
                "is_admin": True
            }
        )

    except Exception as e:
        error_log(f"❌ ADMIN/DASHBOARD: Erro ao carregar dashboard: {str(e)}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor")


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

        # Buscar estatísticas detalhadas para cada aluno
        alunos_stats = []
        for aluno in alunos:
            # Buscar todas as avaliações do aluno
            avaliacoes = db.query(Avaliacao).filter(
                Avaliacao.aluno_id == aluno.id
            ).order_by(Avaliacao.data.desc()).all()

            total_avaliacoes = len(avaliacoes)

            # Estatísticas mais detalhadas
            ultima_avaliacao = avaliacoes[0] if avaliacoes else None
            primeira_avaliacao = avaliacoes[-1] if avaliacoes else None

            # Calcular progressos
            peso_atual = ultima_avaliacao.peso_kg if ultima_avaliacao and ultima_avaliacao.peso_kg else None
            peso_inicial = primeira_avaliacao.peso_kg if primeira_avaliacao and primeira_avaliacao.peso_kg else None

            imc_atual = ultima_avaliacao.imc if ultima_avaliacao and ultima_avaliacao.imc else None
            altura_atual = ultima_avaliacao.altura_cm if ultima_avaliacao and ultima_avaliacao.altura_cm else None

            # Calcular variação de peso
            variacao_peso = None
            if peso_atual is not None and peso_inicial is not None and total_avaliacoes > 1:
                variacao_peso = peso_atual - peso_inicial

            # Data da última avaliação
            data_ultima_avaliacao = None
            if ultima_avaliacao and ultima_avaliacao.data:
                data_ultima_avaliacao = utc_to_sao_paulo(ultima_avaliacao.data)

            alunos_stats.append({
                "aluno": aluno,
                "total_avaliacoes": total_avaliacoes,
                "ultima_avaliacao": ultima_avaliacao,
                "data_ultima_avaliacao": data_ultima_avaliacao,
                "peso_atual": peso_atual,
                "peso_inicial": peso_inicial,
                "variacao_peso": variacao_peso,
                "imc_atual": imc_atual,
                "altura_atual": altura_atual,
                "tem_progresso": total_avaliacoes > 1
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
    """Estatísticas detalhadas do sistema"""
    try:
        debug_log("📊 ADMIN/STATS: Calculando estatísticas detalhadas")

        # Estatísticas básicas
        total_alunos = db.query(Aluno).count()
        total_avaliacoes = db.query(Avaliacao).count()
        alunos_ativos = db.query(Aluno).filter(Aluno.ativo == True).count()

        # Avaliações recentes (últimos 30 dias)
        from datetime import timedelta
        data_limite_30d = now_sao_paulo() - timedelta(days=30)
        avaliacoes_recentes = db.query(Avaliacao).filter(
            Avaliacao.data >= data_limite_30d
        ).count()

        # Avaliações desta semana
        data_limite_7d = now_sao_paulo() - timedelta(days=7)
        avaliacoes_semana = db.query(Avaliacao).filter(
            Avaliacao.data >= data_limite_7d
        ).count()

        # Avaliações de hoje
        data_hoje = now_sao_paulo().replace(hour=0, minute=0, second=0, microsecond=0)
        avaliacoes_hoje = db.query(Avaliacao).filter(
            Avaliacao.data >= data_hoje
        ).count()

        # Estatísticas de IMC
        avaliacoes_com_imc = db.query(Avaliacao).filter(
            Avaliacao.imc.isnot(None)
        ).all()

        imc_stats = {
            "normal": 0,
            "sobrepeso": 0,
            "obesidade": 0,
            "baixo_peso": 0
        }

        for avaliacao in avaliacoes_com_imc:
            imc = avaliacao.imc
            if imc < 18.5:
                imc_stats["baixo_peso"] += 1
            elif imc < 25:
                imc_stats["normal"] += 1
            elif imc < 30:
                imc_stats["sobrepeso"] += 1
            else:
                imc_stats["obesidade"] += 1

        # Média de avaliações por aluno
        media_avaliacoes = total_avaliacoes / total_alunos if total_alunos > 0 else 0

        # Alunos com progresso (mais de 1 avaliação)
        alunos_com_progresso = db.query(Aluno.id).join(Avaliacao).group_by(Aluno.id).having(
            func.count(Avaliacao.id) > 1
        ).count()

        # Top 5 alunos mais ativos (por número de avaliações)
        top_alunos = db.query(
            Aluno.nome,
            func.count(Avaliacao.id).label('total_avaliacoes')
        ).join(Avaliacao).group_by(Aluno.id, Aluno.nome).order_by(
            func.count(Avaliacao.id).desc()
        ).limit(5).all()

        stats = {
            "total_alunos": total_alunos,
            "alunos_ativos": alunos_ativos,
            "total_avaliacoes": total_avaliacoes,
            "avaliacoes_recentes": avaliacoes_recentes,
            "avaliacoes_semana": avaliacoes_semana,
            "avaliacoes_hoje": avaliacoes_hoje,
            "media_avaliacoes": round(media_avaliacoes, 1),
            "alunos_com_progresso": alunos_com_progresso,
            "imc_stats": imc_stats,
            "top_alunos": [
                {"nome": nome, "avaliacoes": total}
                for nome, total in top_alunos
            ],
            "percentual_ativos": round((alunos_ativos / total_alunos * 100) if total_alunos > 0 else 0, 1),
            "percentual_com_progresso": round((alunos_com_progresso / total_alunos * 100) if total_alunos > 0 else 0, 1),
            "timestamp": now_sao_paulo().isoformat()
        }

        info_log(f"📊 ADMIN/STATS: Estatísticas detalhadas calculadas - {total_alunos} alunos, {total_avaliacoes} avaliações, {avaliacoes_recentes} recentes")

        return stats

    except Exception as e:
        error_log(f"❌ ADMIN/STATS: Erro: {str(e)}")
        return {"error": f"Erro ao calcular estatísticas: {str(e)}"}