"""
Sistema de Conferência de Lançamentos
Validação obrigatória antes de consolidar/pagar
"""

from decimal import Decimal
from datetime import datetime
from typing import Tuple
from django.db import models, transaction
from django.conf import settings
from lancamentos.models import Lancamento


class ConferenciaLancamento(models.Model):
    """Registro de conferência/validação de lançamento antes de pagamento"""

    STATUS_CHOICES = [
        ('PENDENTE', 'Pendente de Conferência'),
        ('CONFERIDO', 'Conferido - OK'),
        ('PROBLEMA', 'Conferido - Com Problema'),
        ('REJEITADO', 'Rejeitado'),
    ]

    lancamento = models.OneToOneField(
        Lancamento,
        on_delete=models.CASCADE,
        related_name='conferencia'
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDENTE')
    
    # Quem conferiu
    conferido_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='conferencias_lancamentos'
    )
    data_conferencia = models.DateTimeField(null=True, blank=True)
    
    # Validações
    valor_conferido = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Valor conferido manualmente (se diferente de calculado)"
    )
    observacoes = models.TextField(blank=True)
    
    # Rastreamento
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'lancamentos_conferencia'
        verbose_name = 'Conferência de Lançamento'
        verbose_name_plural = 'Conferências de Lançamentos'

    def __str__(self):
        return f"Conferência {self.lancamento} - {self.status}"

    def conferir(self, usuario, valor_conferido: Decimal = None, observacoes: str = "") -> bool:
        """
        Marca lançamento como conferido

        Args:
            usuario: Usuário que está conferindo
            valor_conferido: Valor conferido (se diferente do calculado)
            observacoes: Observações/notas sobre a conferência

        Returns:
            True se conferência foi válida, False se há problema
        """
        self.conferido_por = usuario
        self.data_conferencia = datetime.now()
        self.observacoes = observacoes
        self.valor_conferido = valor_conferido

        # Validações automáticas
        problemas = self._validar()

        if problemas:
            self.status = 'PROBLEMA'
        else:
            self.status = 'CONFERIDO'

        self.save()
        return self.status == 'CONFERIDO'

    def rejeitar(self, usuario, motivo: str = ""):
        """Marca lançamento como rejeitado"""
        self.conferido_por = usuario
        self.data_conferencia = datetime.now()
        self.status = 'REJEITADO'
        self.observacoes = motivo
        self.save()

    def _validar(self) -> list:
        """
        Executa validações automáticas

        Returns:
            Lista de problemas encontrados (vazia = sem problemas)
        """
        problemas = []

        # 1. Validar se valor_fgts está positivo
        if self.lancamento.valor_fgts <= 0:
            problemas.append("Valor FGTS inválido (≤ 0)")

        # 2. Validar se valor_fgts é coerente com base_fgts (alíquota do vínculo)
        from empresas.models_grupo import get_aliquota_fgts
        aliquota = get_aliquota_fgts(self.lancamento.vinculo)
        base_calc = self.lancamento.valor_fgts / aliquota if aliquota else Decimal('0')
        if abs(base_calc - self.lancamento.base_fgts) > Decimal('1'):  # Tolerância de R$ 1
            problemas.append(f"Base FGTS incongruente: calculada {base_calc:.2f}, informada {self.lancamento.base_fgts:.2f}")

        # 3. Validar se competência é válida (formato MM/YYYY)
        try:
            from datetime import datetime
            datetime.strptime(self.lancamento.competencia, '%m/%Y')
        except ValueError:
            problemas.append(f"Competência inválida: {self.lancamento.competencia}")

        # 4. Validar se data_pagamento faz sentido (posterior à competência)
        if self.lancamento.data_pagamento:
            comp_date = datetime.strptime(self.lancamento.competencia + '/01', '%m/%Y/%d').date()
            if self.lancamento.data_pagamento < comp_date:
                problemas.append(f"Data de pagamento anterior à competência")

        # 5. Se valor_conferido foi fornecido, validar diferença
        if self.valor_conferido is not None:
            diff = abs(self.valor_conferido - self.lancamento.valor_fgts)
            percentual = (diff / self.lancamento.valor_fgts * 100) if self.lancamento.valor_fgts > 0 else 0
            if percentual > 5:  # Mais de 5% de diferença
                problemas.append(f"Valor conferido diverge em {percentual:.1f}% (calculado: {self.lancamento.valor_fgts:.2f}, conferido: {self.valor_conferido:.2f})")

        return problemas

    @classmethod
    def gerar_relatorio_conferencia(cls, empresa, competencia: str = None):
        """
        Gera relatório de conferências para análise

        Returns:
            Dict com estatísticas
        """
        qs = cls.objects.filter(lancamento__empresa=empresa)
        
        if competencia:
            qs = qs.filter(lancamento__competencia=competencia)

        total = qs.count()
        conferidos = qs.filter(status='CONFERIDO').count()
        problemas = qs.filter(status='PROBLEMA').count()
        rejeitados = qs.filter(status='REJEITADO').count()
        pendentes = qs.filter(status='PENDENTE').count()

        return {
            'empresa': empresa,
            'competencia': competencia,
            'total_lancamentos': total,
            'conferidos': conferidos,
            'com_problemas': problemas,
            'rejeitados': rejeitados,
            'pendentes': pendentes,
            'taxa_conferencia': (conferidos / total * 100) if total > 0 else 0,
            'percentual_problemas': (problemas / total * 100) if total > 0 else 0,
        }

    @classmethod
    def pode_consolidar_competencia(cls, empresa, competencia: str) -> Tuple[bool, str]:
        """
        Verifica se uma competência pode ser consolidada/paga

        Returns:
            (pode_consolidar, mensagem)
        """
        conferencias = cls.objects.filter(
            lancamento__empresa=empresa,
            lancamento__competencia=competencia
        )

        if not conferencias.exists():
            return False, "Nenhuma conferência registrada para esta competência"

        rejeitados = conferencias.filter(status='REJEITADO').count()
        if rejeitados > 0:
            return False, f"{rejeitados} lançamentos foram rejeitados"

        pendentes = conferencias.filter(status='PENDENTE').count()
        if pendentes > 0:
            return False, f"{pendentes} lançamentos ainda estão pendentes"

        problemas = conferencias.filter(status='PROBLEMA').count()
        if problemas > 0:
            # Pode consolidar mesmo com problemas, mas com aviso
            msg = f"ATENÇÃO: {problemas} lançamentos com problemas registrados"
            return True, msg

        return True, "Todas as conferências OK - Pronto para consolidar"
