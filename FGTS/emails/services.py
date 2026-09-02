"""
Serviços de envio de email
"""
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


def _get_public_base_url() -> str:
    base_url = (getattr(settings, 'SITE_URL', None) or '').strip().rstrip('/')
    if base_url:
        return base_url
    if getattr(settings, 'ALLOWED_HOSTS', None):
        host = (settings.ALLOWED_HOSTS[0] or '').strip()
        if host and host != '*':
            if host.startswith('http://') or host.startswith('https://'):
                return host.rstrip('/')
            return f"https://{host}".rstrip('/')
    return 'http://localhost:8000'


class EmailService:
    """Serviço centralizado para envio de emails"""
    
    @staticmethod
    def enviar_email_simples(
        assunto: str,
        mensagem: str,
        destinatarios: list,
        remetente: str = None
    ) -> bool:
        """
        Envia um email simples em texto
        
        Args:
            assunto: Assunto do email
            mensagem: Corpo do email em texto
            destinatarios: Lista de emails destinatários
            remetente: Email remetente (opcional, usa DEFAULT_FROM_EMAIL)
            
        Returns:
            bool: True se enviado com sucesso
        """
        try:
            remetente = remetente or settings.DEFAULT_FROM_EMAIL
            send_mail(
                assunto,
                mensagem,
                remetente,
                destinatarios,
                fail_silently=False,
            )
            logger.info(f"Email enviado: {assunto} para {destinatarios}")
            return True
        except Exception as e:
            logger.error(f"Erro ao enviar email: {e}")
            return False
    
    @staticmethod
    def enviar_email_html(
        assunto: str,
        template_html: str,
        contexto: dict,
        destinatarios: list,
        remetente: str = None
    ) -> bool:
        """
        Envia um email com template HTML
        
        Args:
            assunto: Assunto do email
            template_html: Caminho do template HTML
            contexto: Dicionário com variáveis para o template
            destinatarios: Lista de emails destinatários
            remetente: Email remetente (opcional)
            
        Returns:
            bool: True se enviado com sucesso
        """
        try:
            remetente = remetente or settings.DEFAULT_FROM_EMAIL
            
            # Renderizar HTML
            html_content = render_to_string(template_html, contexto)
            
            # Criar email
            email = EmailMultiAlternatives(
                assunto,
                '',  # Texto alternativo vazio
                remetente,
                destinatarios
            )
            email.attach_alternative(html_content, "text/html")
            email.send()
            
            logger.info(f"Email HTML enviado: {assunto} para {destinatarios}")
            return True
        except Exception as e:
            logger.error(f"Erro ao enviar email HTML: {e}")
            return False


# Funções específicas para casos de uso comuns

def enviar_boas_vindas(usuario):
    """Envia email de boas-vindas para novo usuário"""
    return EmailService.enviar_email_simples(
        assunto='Bem-vindo ao Sistema FGTS',
        mensagem=f'''
Olá {usuario.get_full_name() or usuario.username},

Bem-vindo ao Sistema de Gestão FGTS!

Seu cadastro foi criado com sucesso. Você já pode começar a utilizar o sistema.

Atenciosamente,
Equipe FGTS
        '''.strip(),
        destinatarios=[usuario.email]
    )


def enviar_recuperacao_senha(usuario, token):
    """Envia email de recuperação de senha"""
    link = f"{_get_public_base_url()}/recuperar-senha/{token}/"
    
    return EmailService.enviar_email_simples(
        assunto='Recuperação de Senha - Sistema FGTS',
        mensagem=f'''
Olá {usuario.get_full_name() or usuario.username},

Recebemos uma solicitação de recuperação de senha.

Use o link abaixo para redefinir sua senha:
{link}

Se você não solicitou esta recuperação, ignore este email.

Atenciosamente,
Equipe FGTS
        '''.strip(),
        destinatarios=[usuario.email]
    )


def enviar_notificacao_lancamento(empresa, competencia):
    """Envia notificação sobre novos lançamentos"""
    usuarios = empresa.usuarios.filter(is_active=True)
    emails = [u.email for u in usuarios if u.email]
    
    if not emails:
        return False
    
    return EmailService.enviar_email_simples(
        assunto=f'Novos Lançamentos - {competencia}',
        mensagem=f'''
Olá,

Novos lançamentos foram processados para a empresa {empresa.nome_fantasia}.

Competência: {competencia}

Acesse o sistema para conferir os detalhes.

Atenciosamente,
Equipe FGTS
        '''.strip(),
        destinatarios=emails
    )


def enviar_alerta_trial(empresa, dias_restantes):
    """Envia alerta sobre fim do período trial"""
    usuarios = empresa.usuarios.filter(is_active=True)
    emails = [u.email for u in usuarios if u.email]
    
    if not emails:
        return False
    
    return EmailService.enviar_email_simples(
        assunto=f'⚠️ Período Trial - {dias_restantes} dias restantes',
        mensagem=f'''
Olá,

Seu período de teste está próximo do fim.

Empresa: {empresa.nome_fantasia}
Dias restantes: {dias_restantes}

Para continuar utilizando o sistema sem interrupções, 
acesse o painel e escolha um plano.

Atenciosamente,
Equipe FGTS
        '''.strip(),
        destinatarios=emails
    )
