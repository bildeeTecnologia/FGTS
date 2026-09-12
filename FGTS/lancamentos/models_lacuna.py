# Documentação de uso: empresas/templates/ajuda/manual.html#auditoria-lancamentos
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class LacunaJustificativa(models.Model):
    """Justificativa autodeclarada para uma competência esperada sem lançamento."""

    MOTIVO_CHOICES = [
        ('afastamento_inss', 'Afastamento (INSS)'),
        ('licenca_nao_remunerada', 'Licença não remunerada'),
        ('auxilio_doenca', 'Auxílio-doença'),
        ('licenca_maternidade_paternidade', 'Licença maternidade/paternidade'),
        ('suspensao_contratual', 'Suspensão contratual'),
        ('erro_importacao_dado_historico_ausente', 'Erro de importação / dado histórico ausente'),
        ('outro', 'Outro'),
    ]

    vinculo = models.ForeignKey(
        'empresas.FuncionarioVinculo',
        on_delete=models.CASCADE,
        related_name='lacunas_justificadas',
    )
    competencia = models.CharField(max_length=7, help_text='MM/YYYY')
    parcela_13 = models.PositiveSmallIntegerField(
        null=True, blank=True,
        choices=[(1, '13º Salário - 1ª Parcela'), (2, '13º Salário - 2ª Parcela')],
    )
    motivo = models.CharField(max_length=50, choices=MOTIVO_CHOICES)
    observacao = models.TextField(blank=True)
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='lacunas_justificadas',
    )
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'lancamentos_lacuna_justificativa'
        verbose_name = 'Justificativa de Lacuna'
        verbose_name_plural = 'Justificativas de Lacuna'
        constraints = [
            models.UniqueConstraint(
                fields=['vinculo', 'competencia', 'parcela_13'],
                name='uniq_lacuna_por_vinculo_competencia_parcela',
            )
        ]
        ordering = ['-criado_em']

    def clean(self):
        super().clean()
        if self.motivo == 'outro' and not (self.observacao or '').strip():
            raise ValidationError({'observacao': 'Informe uma observação ao selecionar o motivo "Outro".'})

    def __str__(self):
        parcela_label = f" (13º {self.parcela_13}ª parcela)" if self.parcela_13 else ""
        return f"Lacuna {self.vinculo} — {self.competencia}{parcela_label}: {self.get_motivo_display()}"
