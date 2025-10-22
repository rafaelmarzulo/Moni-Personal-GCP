"""
Middleware e decoradores de autenticação
"""
from fastapi import Request, HTTPException, status
from fastapi.responses import RedirectResponse, HTMLResponse
from functools import wraps

from app.services.auth_service import verify_session, verify_simple_jwt
from app.core.config import SESSION_COOKIE_NAME
from app.utils.logging import debug_log


def render_safe_error(request: Request, title: str, message: str, error_details: str, back_url: str = "/"):
    """Renderiza uma página de erro segura sem perder a sessão do usuário"""
    safe_html = f"<!DOCTYPE html><html lang='pt-br'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width, initial-scale=1'><title>{title} - MoniPersonal</title><link href='https://cdn.jsdelivr.net/npm/bootstrap-dark-5@1.1.3/dist/css/bootstrap-dark.min.css' rel='stylesheet'><link rel='stylesheet' href='https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.1/font/bootstrap-icons.css'><style>body {{ background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%); color: #ffffff; min-height: 100vh; }} .card {{ border: none; border-radius: 20px; box-shadow: 0 8px 32px rgba(214, 51, 132, 0.3); background: rgba(255, 255, 255, 0.1); backdrop-filter: blur(10px); }} .btn {{ border-radius: 25px; padding: 12px 24px; font-weight: 600; }}</style></head><body><div class='container mt-5'><div class='row justify-content-center'><div class='col-md-8'><div class='card'><div class='card-header bg-danger text-white'><h4><i class='bi bi-exclamation-triangle me-2'></i>{title}</h4></div><div class='card-body'><h5>{message}</h5><p class='text-muted'>Ocorreu um erro temporário. Suas informações estão seguras e sua sessão permanece ativa.</p><div class='mt-4'><a href='{back_url}' class='btn btn-primary me-2'><i class='bi bi-arrow-left me-1'></i>Voltar</a><a href='/meu-historico' class='btn btn-success me-2'><i class='bi bi-clock-history me-1'></i>Ver Histórico</a><a href='/formulario' class='btn btn-outline-info me-2'><i class='bi bi-plus-circle me-1'></i>Nova Avaliação</a><a href='/' class='btn btn-outline-secondary'><i class='bi bi-house me-1'></i>Início</a></div><details class='mt-4'><summary class='text-muted' style='cursor: pointer;'>Detalhes técnicos (para suporte)</summary><pre class='bg-light text-dark p-3 mt-2 small rounded'><code>{error_details}</code></pre><small class='text-muted'>Se este erro persistir, entre em contato com o suporte técnico.</small></details></div></div></div></div></div></body></html>"
    return HTMLResponse(content=safe_html, status_code=500)


def require_auth(user_types: list = None):
    """
    Decorator para proteger rotas que requerem autenticação

    Args:
        user_types: Lista de tipos de usuário permitidos (ex: ['admin', 'aluno'])
                   Se None, permite qualquer usuário autenticado
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Encontrar o objeto Request nos argumentos
            request = None
            session_token = None

            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break

            if not request:
                # Tentar encontrar nos kwargs
                request = kwargs.get('request')

            if not request:
                raise HTTPException(status_code=500, detail="Request object not found")

            # Obter token de sessão do cookie ou parâmetro
            session_token = request.cookies.get(SESSION_COOKIE_NAME)
            if not session_token:
                session_token = kwargs.get('session_token')

            debug_log(f"🔍 REQUIRE_AUTH: session_token={session_token}")

            # Verificar autenticação por sessão
            session_data = verify_session(session_token)
            if session_data:
                debug_log(f"✅ REQUIRE_AUTH: Usuário autenticado via sessão: {session_data}")

                # Verificar tipo de usuário se especificado
                if user_types and session_data.get('user_type') not in user_types:
                    debug_log(f"❌ REQUIRE_AUTH: Tipo de usuário não permitido: {session_data.get('user_type')}")
                    raise HTTPException(status_code=403, detail="Acesso negado")

                # Adicionar dados da sessão aos kwargs para uso na função
                kwargs['session_data'] = session_data
                return await func(*args, **kwargs)

            # Verificar autenticação por JWT
            jwt_data = verify_simple_jwt(session_token)
            if jwt_data:
                debug_log(f"🔍 REQUIRE_AUTH: jwt_data={jwt_data}")

                # Verificar tipo de usuário se especificado
                if user_types and jwt_data.get('user_type') not in user_types:
                    debug_log(f"❌ REQUIRE_AUTH: Tipo de usuário JWT não permitido: {jwt_data.get('user_type')}")
                    raise HTTPException(status_code=403, detail="Acesso negado")

                debug_log(f"✅ REQUIRE_AUTH: {jwt_data.get('user_type', 'Usuario').title()} autenticado via JWT")

                # Adicionar dados do JWT aos kwargs
                kwargs['jwt_data'] = jwt_data
                return await func(*args, **kwargs)

            debug_log("❌ REQUIRE_AUTH: Token inválido ou expirado")

            # Se chegou aqui, não está autenticado
            if request.url.path.startswith('/admin'):
                return RedirectResponse(url="/admin-login")
            else:
                return RedirectResponse(url="/login")

        return wrapper
    return decorator


def require_admin():
    """Decorator específico para rotas administrativas"""
    return require_auth(['admin'])