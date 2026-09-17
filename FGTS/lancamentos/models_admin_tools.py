from django.db import models


class RecalcularAuditoria(models.Model):
    """Modelo âncora para a página "Recalcular auditoria" no admin. Não cria tabela."""

    class Meta:
        managed = False
        verbose_name = 'Recalcular Auditoria'
        verbose_name_plural = 'Recalcular Auditoria (cache)'
        app_label = 'lancamentos'
