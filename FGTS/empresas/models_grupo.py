from decimal import Decimal
from django.db import models
from django.conf import settings


class TipoVinculo(models.Model):
    """Parametriza o tipo de contratação e a alíquota de FGTS correspondente. Gerenciado pelo admin Django."""
    codigo = models.CharField(max_length=20, unique=True, verbose_name='Código')
    descricao = models.CharField(max_length=100, verbose_name='Descrição')
    percentual_fgts = models.DecimalField(
        max_digits=5, decimal_places=2,
        verbose_name='Percentual FGTS (%)',
        help_text='Ex: 8.00 para CLT, 2.00 para Aprendiz',
    )
    ativo = models.BooleanField(default=True, verbose_name='Ativo')

    class Meta:
        verbose_name = 'Tipo de vínculo'
        verbose_name_plural = 'Tipos de vínculo'
        ordering = ['codigo']

    def __str__(self):
        return f"{self.descricao} ({self.percentual_fgts}%)"

    @property
    def aliquota(self) -> Decimal:
        """Retorna a alíquota como fração (ex: Decimal('0.02') para 2%)."""
        return self.percentual_fgts / Decimal('100')


class GrupoEmpresa(models.Model):
    nome = models.CharField(max_length=255, unique=True)
    cnpj_base = models.CharField(max_length=20, blank=True, null=True)
    data_criacao = models.DateField(auto_now_add=True)
    observacoes = models.TextField(blank=True, null=True)
    empresa_principal = models.OneToOneField(
        'empresas.Empresa',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='grupo_principal',
        verbose_name='Empresa principal do grupo',
        help_text='Define a empresa proprietária/raiz do grupo para escopo e isolamento.',
    )

    def __str__(self):
        return self.nome

class FuncionarioVinculo(models.Model):
    STATUS_CHOICES = [
        ("ativo", "Ativo"),
        ("transferido", "Transferido"),
        ("demitido", "Demitido"),
    ]
    MOTIVO_SAIDA_CHOICES = [
        ("transferencia", "Transferência"),
        ("rescisao_indireta","Rescisão indireta"),
        ("rescisao_experiencia_antecipado_empregador", "Rescisão experiencia antecipado empregador"),
        ("rescisao_experiencia_antecipado_trabalhador", "Rescisão experiencia antecipado trabalhador"),
        ("rescisao_termino_contrato_experiencia", "Rescisão termino contrato experiencia"),
        ("rescisao_acordo", "Rescisão acordo"),
        ("termino_contrato", "Término de contrato"),
        ("pedido_demissao", "Pedido de demissão"),
        ("demissao_sem_justa_causa", "Demissão sem justa causa"),
        ("demissao_justa_causa", "Demissão por justa causa"),
        ("outro", "Outro"),
    ]
    funcionario = models.ForeignKey('funcionarios.Funcionario', on_delete=models.CASCADE, related_name='vinculos')
    empresa = models.ForeignKey('empresas.Empresa', on_delete=models.CASCADE)
    matricula = models.CharField(max_length=30, blank=True, null=True, db_index=True, verbose_name='Matrícula')
    data_admissao = models.DateField()
    data_demissao = models.DateField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ativo', verbose_name='Status do vínculo')
    motivo_saida = models.CharField(max_length=50, choices=MOTIVO_SAIDA_CHOICES, blank=True, null=True)
    observacoes = models.TextField(blank=True, null=True)
    cargo = models.CharField(max_length=100, blank=True, null=True)
    salario = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    data_transferencia = models.DateField(blank=True, null=True)
    tipo_vinculo = models.ForeignKey(
        TipoVinculo,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='vinculos',
        verbose_name='Tipo de vínculo',
        help_text='Nulo = CLT (8%). Altere apenas para corrigir cadastros incorretos; para efetivação de aprendiz crie um novo vínculo.',
    )

    def is_ativo_em_competencia(self, competencia):
        """
        Retorna True se o vínculo estava ativo na competência informada.
        Aceita: 'MM/YYYY', 'YYYY-MM', 'YYYY/MM' ou datetime.date
        """
        import datetime
        competencia_date = None
        if isinstance(competencia, str):
            try:
                if '/' in competencia:
                    parts = competencia.split('/')
                    if len(parts) == 2:
                        # MM/YYYY
                        if len(parts[1]) == 4:
                            mes, ano = int(parts[0]), int(parts[1])
                            competencia_date = datetime.date(ano, mes, 1)
                        # YYYY/MM
                        elif len(parts[0]) == 4:
                            ano, mes = int(parts[0]), int(parts[1])
                            competencia_date = datetime.date(ano, mes, 1)
                elif '-' in competencia:
                    parts = competencia.split('-')
                    if len(parts) == 2 and len(parts[0]) == 4:
                        # YYYY-MM
                        ano, mes = int(parts[0]), int(parts[1])
                        competencia_date = datetime.date(ano, mes, 1)
            except Exception:
                return False
        elif isinstance(competencia, datetime.date):
            competencia_date = competencia.replace(day=1)
        else:
            return False

        if competencia_date is None:
            return False

        # Considerar ativo durante todo o mês de admissão e demissão (ignorar o dia)
        admissao_mes_ano = (self.data_admissao.year, self.data_admissao.month)
        competencia_mes_ano = (competencia_date.year, competencia_date.month)
        if self.data_demissao:
            demissao_mes_ano = (self.data_demissao.year, self.data_demissao.month)
            admitido = competencia_mes_ano >= admissao_mes_ano
            nao_demitido = competencia_mes_ano <= demissao_mes_ano
        else:
            admitido = competencia_mes_ano >= admissao_mes_ano
            nao_demitido = True
        return admitido and nao_demitido

    def save(self, *args, **kwargs):
        """Sincroniza o status do vínculo com data_demissao e motivo_saida"""
        if self.motivo_saida == 'transferencia':
            self.status = 'transferido'
        elif self.data_demissao:
            self.status = 'demitido'
        else:
            self.status = 'ativo'
        super().save(*args, **kwargs)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['empresa', 'matricula'],
                name='uniq_vinculo_matricula_por_empresa',
                condition=models.Q(matricula__isnull=False) & ~models.Q(matricula=''),
            )
        ]

    def __str__(self):
        matricula_label = (self.matricula or '').strip()
        ident = f"Matrícula {matricula_label}" if matricula_label else f"Vínculo {self.pk}"
        periodo = f"{self.data_admissao} a {self.data_demissao or 'atual'}"
        return f"{self.funcionario.nome} - {self.empresa.nome} ({ident}) ({periodo})"


def get_aliquota_fgts(vinculo) -> Decimal:
    """Retorna a alíquota FGTS fracionária do vínculo (ex: Decimal('0.02')). Padrão: 0.08 (CLT)."""
    if vinculo is not None and getattr(vinculo, 'tipo_vinculo_id', None):
        return vinculo.tipo_vinculo.percentual_fgts / Decimal('100')
    return Decimal('0.08')

class TransferenciaFuncionario(models.Model):
    funcionario = models.ForeignKey('funcionarios.Funcionario', on_delete=models.CASCADE)
    empresa_origem = models.ForeignKey('empresas.Empresa', on_delete=models.CASCADE, related_name='transferencias_saida')
    empresa_destino = models.ForeignKey('empresas.Empresa', on_delete=models.CASCADE, related_name='transferencias_entrada')
    data_transferencia = models.DateField(blank=True, null=True)
    usuario_responsavel = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    observacoes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.funcionario.nome}: {self.empresa_origem.nome} → {self.empresa_destino.nome} em {self.data_transferencia}"
