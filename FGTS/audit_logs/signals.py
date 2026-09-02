import logging
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.contenttypes.models import ContentType
from .models import AuditLog
from empresas.models import Empresa
from funcionarios.models import Funcionario
from lancamentos.models import Lancamento

logger = logging.getLogger(__name__)


def get_client_ip(request):
    """Obtém o IP do cliente a partir da requisição"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def get_user_agent(request):
    """Obtém o User Agent do cliente"""
    return request.META.get('HTTP_USER_AGENT', '')


def log_action(user, action, content_type=None, object_id=None, object_repr='', 
               changes=None, ip_address=None, user_agent='', status_code=None, error_message=''):
    """
    Função genérica para registrar uma ação no sistema
    """
    if changes is None:
        changes = {}
    
    try:
        AuditLog.objects.create(
            user=user,
            action=action,
            content_type=content_type,
            object_id=object_id,
            object_repr=object_repr,
            changes=changes,
            ip_address=ip_address,
            user_agent=user_agent,
            status_code=status_code,
            error_message=error_message
        )
    except Exception as e:
        logger.error(f"Erro ao registrar log de auditoria: {str(e)}")


# Signals para registrar criação de objetos
@receiver(post_save, sender=Empresa)
def log_empresa_save(sender, instance, created, **kwargs):
    """Log para criação/atualização de Empresa"""
    # Aguardar que a instância tenha sido completamente salva
    if not instance.pk:
        return
    
    if created:
        action = 'CREATE'
        object_repr = f"Empresa: {instance.nome}"
    else:
        action = 'UPDATE'
        object_repr = f"Empresa: {instance.nome}"
    
    content_type = ContentType.objects.get_for_model(Empresa)
    log_action(
        user=None,  # Será preenchido via middleware
        action=action,
        content_type=content_type,
        object_id=instance.pk,
        object_repr=object_repr
    )


@receiver(post_save, sender=Funcionario)
def log_funcionario_save(sender, instance, created, **kwargs):
    """Log para criação/atualização de Funcionário"""
    if not instance.pk:
        return
    
    if created:
        action = 'CREATE'
    else:
        action = 'UPDATE'
    
    content_type = ContentType.objects.get_for_model(Funcionario)
    log_action(
        user=None,
        action=action,
        content_type=content_type,
        object_id=instance.pk,
        object_repr=f"Funcionário: {instance.nome} - CPF: {instance.cpf}"
    )


@receiver(post_save, sender=Lancamento)
def log_lancamento_save(sender, instance, created, **kwargs):
    """Log para criação/atualização de Lançamento"""
    if not instance.pk:
        return
    
    if created:
        action = 'CREATE'
    else:
        action = 'UPDATE'
    
    content_type = ContentType.objects.get_for_model(Lancamento)
    try:
        funcionario_nome = instance.funcionario.nome
    except:
        funcionario_nome = f"Funcionário ID {instance.funcionario_id}"
    
    log_action(
        user=None,
        action=action,
        content_type=content_type,
        object_id=instance.pk,
        object_repr=f"Lançamento: {funcionario_nome} - Competência: {instance.competencia}"
    )


@receiver(post_delete, sender=Lancamento)
def log_lancamento_delete(sender, instance, **kwargs):
    """Log para exclusão de Lançamento"""
    content_type = ContentType.objects.get_for_model(Lancamento)
    try:
        funcionario_nome = instance.funcionario.nome
    except:
        funcionario_nome = f"Funcionário ID {instance.funcionario_id}"
    
    log_action(
        user=None,
        action='DELETE',
        content_type=content_type,
        object_id=instance.id,
        object_repr=f"Lançamento: {funcionario_nome} - Competência: {instance.competencia}"
    )
