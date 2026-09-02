import logging
import traceback
from django.utils.deprecation import MiddlewareMixin
from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.dispatch import receiver
from django.urls import resolve
from .models import AuditLog
from .signals import get_client_ip, get_user_agent, log_action

logger = logging.getLogger(__name__)


@receiver(user_logged_in)
def log_user_login(sender, request, user, **kwargs):
    """Log de login do usuário"""
    try:
        ip = get_client_ip(request)
        user_agent = get_user_agent(request)
        
        AuditLog.objects.create(
            user=user,
            action='LOGIN',
            module='auth',
            view_name='auth.login',
            url_path=request.path,
            ip_address=ip,
            user_agent=user_agent,
            method='POST',
            status_code=302,
            object_repr=f"Login do usuário: {user.username}",
            description=f"Usuário {user.username} realizou login com sucesso"
        )
    except Exception as e:
        # Log silencioso - não interrompe o login
        logger.error(f"Erro ao registrar log de auditoria no middleware: {e}")


@receiver(user_logged_out)
def log_user_logout(sender, request, user, **kwargs):
    """Log de logout do usuário"""
    ip = get_client_ip(request)
    user_agent = get_user_agent(request)
    
    if user:
        AuditLog.objects.create(
            user=user,
            action='LOGOUT',
            module='auth',
            view_name='auth.logout',
            url_path=request.path,
            ip_address=ip,
            user_agent=user_agent,
            method='POST',
            status_code=302,
            object_repr=f"Logout do usuário: {user.username}",
            description=f"Usuário {user.username} realizou logout"
        )


def get_module_from_path(path):
    """Extrai o módulo/app do caminho da URL"""
    if '/empresas' in path:
        return 'empresas'
    elif '/funcionarios' in path:
        return 'funcionarios'
    elif '/lancamentos' in path:
        return 'lancamentos'
    elif '/relatorio' in path:
        return 'relatorio'
    elif '/indices' in path:
        return 'indices'
    elif '/coefjam' in path:
        return 'coefjam'
    elif '/configuracoes' in path:
        return 'configuracoes'
    elif '/billing' in path:
        return 'billing'
    else:
        return 'outro'


class AuditLogsMiddleware(MiddlewareMixin):
    """
    Middleware para registrar requisições HTTP e capturar informações do cliente
    Captura: Quem, Quando, Onde (módulo), O que (ação), Por que (descrição)
    """
    
    EXCLUDED_PATHS = [
        '/static/',
        '/media/',
        '/admin/jsi18n/',
    ]
    
    def should_log_request(self, path):
        """Verifica se a requisição deve ser registrada"""
        return not any(path.startswith(excluded) for excluded in self.EXCLUDED_PATHS)
    
    def process_view(self, request, view_func, view_args, view_kwargs):
        """Armazena informações antes de processar a view"""
        request.client_ip = get_client_ip(request)
        request.user_agent = get_user_agent(request)
        request.view_func = view_func
        request.view_kwargs = view_kwargs
        return None

    def process_exception(self, request, exception):
        """Registra exceções não tratadas (HTTP 500) com stacktrace.

        Isso resolve o principal gap do audit log atual: ele registrava o 500,
        mas sem a causa. Aqui tentamos capturar tipo/mensagem + traceback.
        """

        if not self.should_log_request(request.path):
            return None

        # Evitar duplicidade: process_response pode rodar depois
        setattr(request, '_audit_exception_logged', True)

        path = request.path
        method = getattr(request, 'method', '')
        module = get_module_from_path(path)
        user = getattr(request, 'user', None)
        ip = getattr(request, 'client_ip', '')
        user_agent = getattr(request, 'user_agent', '')

        try:
            match = resolve(path)
            view_name = f"{match.app_name}:{match.url_name}" if match.app_name else match.url_name
        except Exception:
            view_name = ''

        error_message = f"{exception.__class__.__name__}: {exception}"
        tb = ''.join(traceback.format_exception(type(exception), exception, exception.__traceback__))
        tb_truncated = tb[-12000:]  # limita tamanho para não inflar o banco

        # Sempre logar no logger para também cair em arquivo/console
        logger.exception("Erro 500 não tratado em %s %s (%s)", method, path, view_name)

        try:
            AuditLog.objects.create(
                user=user if getattr(user, 'is_authenticated', False) else None,
                action='OTHER',
                module=module,
                view_name=view_name,
                url_path=path,
                ip_address=ip,
                user_agent=user_agent,
                method=method,
                status_code=500,
                object_repr=f"EXCEPTION {method} {path}",
                description=tb_truncated,
                error_message=error_message,
            )
        except Exception as e:
            logger.error("Erro ao registrar exceção no AuditLog: %s", str(e))

        return None
    
    def process_response(self, request, response):
        """Registra a resposta após processar a view"""
        if not self.should_log_request(request.path):
            return response

        # Se já registramos a exceção, não duplicar no process_response
        if getattr(request, '_audit_exception_logged', False):
            return response
        
        # Registrar requisições de alteração (POST, PUT, DELETE)
        if request.method in ['POST', 'DELETE', 'PUT', 'PATCH'] and request.user.is_authenticated:
            user = request.user
            ip = getattr(request, 'client_ip', '')
            user_agent = getattr(request, 'user_agent', '')
            path = request.path
            method = request.method
            status_code = response.status_code
            
            # Determinar a ação baseado no método
            if method == 'POST':
                action = 'CREATE' if 'novo' in path or 'create' in path.lower() else 'UPDATE'
            elif method == 'DELETE':
                action = 'DELETE'
            else:
                action = 'UPDATE'
            
            # Extrair módulo do caminho
            module = get_module_from_path(path)
            
            # Tentar obter view_name
            try:
                match = resolve(path)
                view_name = f"{match.app_name}:{match.url_name}" if match.app_name else match.url_name
            except:
                view_name = ''
            
            # Descrição da ação
            status_text = 'OK' if status_code < 400 else f'Erro {status_code}'
            description = f"{method} request para {module}: {status_text}"
            
            error_message = '' if status_code < 400 else f"HTTP {status_code}"
            
            object_repr = f"{method} {path}"
            
            try:
                AuditLog.objects.create(
                    user=user,
                    action=action,
                    module=module,
                    view_name=view_name,
                    url_path=path,
                    ip_address=ip,
                    user_agent=user_agent,
                    method=method,
                    status_code=status_code,
                    object_repr=object_repr,
                    description=description,
                    error_message=error_message
                )
            except Exception as e:
                logger.error(f"Erro ao registrar log de auditoria no middleware: {str(e)}")
        
        return response
