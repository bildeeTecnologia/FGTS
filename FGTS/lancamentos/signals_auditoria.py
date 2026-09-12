"""
Invalida o cache da Auditoria de Lançamentos quando algo que afeta o resultado muda.

Conectado em lancamentos/apps.py (AppConfig.ready()).
"""
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from .models import Lancamento
from .models_lacuna import LacunaJustificativa
from .services.auditoria_vinculo import (
    invalidar_cache_vinculo,
    invalidar_cache_vinculos_empresa,
    invalidar_cache_vinculos_funcionario,
)


@receiver(post_save, sender=Lancamento)
@receiver(post_delete, sender=Lancamento)
def _invalidar_por_lancamento(sender, instance, **kwargs):
    if instance.vinculo_id:
        invalidar_cache_vinculo(instance.vinculo_id)


@receiver(post_save, sender=LacunaJustificativa)
@receiver(post_delete, sender=LacunaJustificativa)
def _invalidar_por_justificativa(sender, instance, **kwargs):
    invalidar_cache_vinculo(instance.vinculo_id)


@receiver(post_save, sender='empresas.FuncionarioVinculo')
def _invalidar_por_vinculo(sender, instance, **kwargs):
    invalidar_cache_vinculo(instance.pk)


@receiver(post_save, sender='funcionarios.Funcionario')
def _invalidar_por_funcionario(sender, instance, **kwargs):
    invalidar_cache_vinculos_funcionario(instance.pk)


@receiver(post_save, sender='empresas.Empresa')
def _invalidar_por_empresa(sender, instance, **kwargs):
    invalidar_cache_vinculos_empresa(instance.pk)


@receiver(post_save, sender='billing.BillingCustomer')
def _invalidar_por_billing_customer(sender, instance, **kwargs):
    invalidar_cache_vinculos_empresa(instance.empresa_id)


@receiver(post_save, sender='billing.Plan')
def _invalidar_por_plan(sender, instance, **kwargs):
    from billing.models import BillingCustomer
    empresa_ids = BillingCustomer.objects.filter(plan=instance).values_list('empresa_id', flat=True)
    for empresa_id in empresa_ids:
        invalidar_cache_vinculos_empresa(empresa_id)
