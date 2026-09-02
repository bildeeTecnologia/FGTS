"""
Middleware para rastrear performance de operações críticas
"""
import time
from datetime import datetime
from django.utils.timezone import now
from .models import PerformanceLog


class PerformanceTrackingMiddleware:
    """Middleware que registra tempo de execução de requisições críticas"""
    
    OPERACOES_RASTREADAS = {
        'relatorio-competencia': 'relatorio_competencia',
        'relatorio-competencia-export-csv': 'exportacao_csv',
        'relatorio-competencia-export-pdf': 'exportacao_pdf',
        'funcionario-import': 'importacao_funcionarios',
        'lancamento-import': 'importacao_lancamentos',
    }
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Iniciar rastreamento
        tempo_inicio = time.time()
        tempo_inicio_dt = now()
        
        # Tentar obter nome da operação
        operacao_key = self._get_operacao_key(request)
        
        try:
            response = self.get_response(request)
            status = 'sucesso'
            erro = ''
        except Exception as e:
            status = 'erro'
            erro = str(e)
            raise
        finally:
            # Calcular tempo de execução
            tempo_final = time.time()
            duracao = tempo_final - tempo_inicio
            
            # Registrar se é uma operação rastreada e demorou mais de 1 segundo
            if operacao_key and duracao > 1.0:
                self._registrar_performance(
                    request=request,
                    operacao=self.OPERACOES_RASTREADAS[operacao_key],
                    status=status,
                    duracao=duracao,
                    tempo_inicio_dt=tempo_inicio_dt,
                    erro=erro
                )
        
        return response
    
    def _get_operacao_key(self, request):
        """Extrai chave da operação da URL ou nome da view"""
        try:
            # Tentar obter do resolver_match
            if hasattr(request, 'resolver_match') and request.resolver_match:
                url_name = request.resolver_match.url_name
                if url_name in self.OPERACOES_RASTREADAS:
                    return url_name
        except:
            pass
        return None
    
    def _registrar_performance(self, request, operacao, status, duracao, tempo_inicio_dt, erro):
        """Registra log de performance no banco de dados"""
        try:
            usuario = request.user if request.user.is_authenticated else None
            
            # Extrair IP do cliente
            ip_cliente = self._get_ip_cliente(request)
            
            # Extrair empresa do request (se houver)
            empresa_id = None
            if hasattr(request, 'session') and 'empresa_selecionada' in request.session:
                empresa_id = request.session.get('empresa_selecionada')
            
            # Criar log
            PerformanceLog.objects.create(
                operacao=operacao,
                status=status,
                usuario=usuario,
                empresa_id=empresa_id,
                tempo_inicio=tempo_inicio_dt,
                tempo_final=now(),
                duracao_segundos=round(duracao, 3),
                mensagem_erro=erro,
                ip_cliente=ip_cliente,
                user_agent=request.META.get('HTTP_USER_AGENT', '')[:500],
                entrada_dados={
                    'metodo': request.method,
                    'url': request.path,
                    'params': dict(request.GET),
                },
            )
        except Exception as e:
            # Não interromper o fluxo se falhar o log
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Erro ao registrar performance log: {str(e)}")
    
    @staticmethod
    def _get_ip_cliente(request):
        """Extrai IP do cliente (considerando proxies)"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
