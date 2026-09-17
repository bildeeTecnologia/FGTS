from django.db import models


class AjusteDataAdmissao(models.Model):
    """Modelo âncora para a página de ajuste de data_admissao no admin. Não cria tabela."""

    class Meta:
        managed = False
        verbose_name = 'Ajuste de Data de Admissão'
        verbose_name_plural = 'Ajuste de Data de Admissão'
        app_label = 'empresas'
