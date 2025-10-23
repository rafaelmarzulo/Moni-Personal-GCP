"""
MoniPersonal - Aplicação Refatorada e Modularizada
Versão inicial com as principais rotas separadas em módulos
"""
from fastapi import FastAPI, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from datetime import datetime
import uvicorn

# Importar configurações centralizadas
from app.core.config import APP_NAME, APP_VERSION

# Importar middleware
from app.middleware.rate_limiting import setup_rate_limiting

# Importar rotas
from app.routes.auth import router as auth_router
from app.routes.public import router as public_router
from app.routes.admin import router as admin_router
from app.routes.student import router as student_router

# Importar configurações para debug
from app.core.config import app_logs
from app.middleware.auth import require_admin

# Importar database
from app.core.database import SessionLocal, engine, Base, get_db

# Importar models para inicialização
from app.models import Avaliacao, Aluno, Usuario

# Importar utilitários
from app.utils.logging import info_log


# Criar aplicação FastAPI
app = FastAPI(
    title=APP_NAME,
    version=APP_VERSION,
    description="Sistema de Monitoramento Pessoal - Versão Modularizada"
)

# Configurar rate limiting
limiter = setup_rate_limiting(app)

# Configurar arquivos estáticos e templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


# ==================== INICIALIZAÇÃO DO BANCO ====================

def init_database():
    """Inicializa o banco de dados automaticamente"""
    try:
        # Criar todas as tabelas se não existirem
        Base.metadata.create_all(bind=engine)
        info_log("✅ Banco de dados inicializado automaticamente")

        # Inicializar usuários padrão
        init_default_users()

        return True
    except Exception as e:
        info_log(f"❌ Erro ao inicializar banco: {str(e)}")
        return False


def init_default_users():
    """Inicializa usuários padrão se não existirem"""
    try:
        from app.services.auth_service import hash_password

        with SessionLocal() as db:
            # Verificar se já existem usuários
            usuario_count = db.query(Usuario).count()

            if usuario_count > 0:
                info_log("ℹ️ Usuários já existem no sistema")
                return

            # Criar usuário administrador
            admin_user = Usuario(
                email="admin@monipersonal.com",
                nome="Administrador",
                senha_hash=hash_password("Monica@1985"),
                tipo="admin",
                ativo=True,
                created_at=datetime.now()
            )

            # Criar usuário aluno Rafael
            rafael_user = Usuario(
                email="rafaelmarzulo@gmail.com",
                nome="Rafael Marzulo",
                senha_hash=hash_password("teste123"),
                tipo="aluno",
                ativo=True,
                created_at=datetime.now()
            )

            db.add(admin_user)
            db.add(rafael_user)
            db.commit()

            info_log("✅ Usuários padrão criados:")
            info_log("   - Admin: admin@monipersonal.com / Monica@1985")
            info_log("   - Aluno: rafaelmarzulo@gmail.com / teste123")

    except Exception as e:
        info_log(f"❌ Erro ao criar usuários padrão: {str(e)}")


# ==================== INCLUIR ROTAS ====================

# Aplicar rate limiting nas rotas
auth_router.dependencies = [Depends(limiter.limit("10/minute"))]
public_router.dependencies = [Depends(limiter.limit("60/minute"))]
admin_router.dependencies = [Depends(limiter.limit("15/minute"))]
student_router.dependencies = [Depends(limiter.limit("20/minute"))]

# Incluir rotas
app.include_router(auth_router, tags=["autenticação"])
app.include_router(public_router, tags=["público"])
app.include_router(admin_router, tags=["administração"])
app.include_router(student_router, tags=["alunos"])


# ==================== ROTA RAIZ ====================

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Redireciona para a página de login"""
    return RedirectResponse(url="/login")


# ==================== HEALTH CHECK ====================

@app.get("/health")
async def health_check():
    """Health check endpoint para Cloud Run"""
    try:
        # Verificar se o banco está acessível
        with SessionLocal() as db:
            db.execute("SELECT 1")
        return {"status": "healthy", "timestamp": datetime.now().isoformat()}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}


# ==================== DEBUG ROUTES ====================

@app.get("/debug/users")
async def debug_users():
    """Endpoint para verificar/criar usuários no Supabase"""
    try:
        with SessionLocal() as db:
            # Verificar usuários existentes
            usuarios = db.query(Usuario).all()

            result = {
                "total_usuarios": len(usuarios),
                "usuarios": [{"id": u.id, "email": u.email, "nome": u.nome, "tipo": u.tipo, "ativo": u.ativo} for u in usuarios]
            }

            # Se não há usuários, criar os padrão
            if len(usuarios) == 0:
                from app.services.auth_service import hash_password

                # Criar usuário administrador
                admin_user = Usuario(
                    email="admin@monipersonal.com",
                    nome="Administrador",
                    senha_hash=hash_password("Monica@1985"),
                    tipo="admin",
                    ativo=True,
                    created_at=datetime.now()
                )

                # Criar usuário aluno Rafael
                rafael_user = Usuario(
                    email="rafaelmarzulo@gmail.com",
                    nome="Rafael Marzulo",
                    senha_hash=hash_password("teste123"),
                    tipo="aluno",
                    ativo=True,
                    created_at=datetime.now()
                )

                db.add(admin_user)
                db.add(rafael_user)
                db.commit()

                result["message"] = "Usuários padrão criados com sucesso!"
                result["created_users"] = [
                    {"email": "admin@monipersonal.com", "senha": "Monica@1985"},
                    {"email": "rafaelmarzulo@gmail.com", "senha": "teste123"}
                ]

            return result

    except Exception as e:
        return {"error": str(e), "type": str(type(e))}

@app.get("/debug/logs", response_class=HTMLResponse)
@require_admin()
async def debug_logs(request: Request, session_data=None, jwt_data=None):
    """Página de logs do sistema para debug"""
    try:
        # Converter deque para lista e inverter para mostrar mais recentes primeiro
        logs_list = list(app_logs)
        logs_list.reverse()

        return templates.TemplateResponse(
            "admin_logs.html",
            {
                "request": request,
                "logs": logs_list,
                "total_logs": len(logs_list),
                "is_admin": True
            }
        )
    except Exception as e:
        return templates.TemplateResponse(
            "erro.html",
            {
                "request": request,
                "title": "Erro ao carregar logs",
                "message": f"Erro ao carregar logs do sistema: {str(e)}",
                "back_url": "/admin/dashboard"
            }
        )


# ==================== ROTAS LEGADAS (EM MIGRAÇÃO) ====================
# Estas rotas estão sendo gradualmente migradas para os módulos apropriados
# TODO: Migrar rotas restantes nas próximas fases


# ==================== EVENTOS DE INICIALIZAÇÃO ====================

@app.on_event("startup")
async def startup_event():
    """Executa na inicialização da aplicação"""
    info_log(f"🚀 Iniciando {APP_NAME} v{APP_VERSION} - Versão Modularizada")

    # Inicializar banco de dados
    if init_database():
        info_log("✅ Sistema pronto para uso")
    else:
        info_log("⚠️ Sistema iniciado com problemas no banco de dados")


@app.on_event("shutdown")
async def shutdown_event():
    """Executa no encerramento da aplicação"""
    info_log(f"🔴 Encerrando {APP_NAME}")


# ==================== EXECUÇÃO ====================

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        workers=1
    )