"""
Módulo BPO — Bureau de Processamento de Folha

Permite que escritórios de folha (BPO) gerenciem múltiplas empresas clientes
sob uma única conta, pagando um valor por CNPJ ativo/mês com rateio proporcional
ao adicionar novos clientes no meio do ciclo de cobrança.
"""

import calendar
from datetime import date
from decimal import Decimal, ROUND_HALF_UP

from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.utils import timezone

from empresas.models import Empresa


def calcular_rateio(preco_por_cnpj: Decimal, dia_cobranca: int, data_base: date = None):
    """
    Calcula o valor proporcional a ser cobrado ao ativar um novo CNPJ no meio do ciclo.

    Retorna uma tupla (valor_rateio, proximo_vencimento, dias_restantes).
    - valor_rateio: Decimal, valor a cobrar imediatamente (proporcional)
    - proximo_vencimento: date, próxima data de cobrança do ciclo completo
    - dias_restantes: int, dias restantes no ciclo atual
    """
    hoje = data_base or date.today()

    # Determina próxima data de vencimento
    if hoje.day < dia_cobranca:
        proximo = date(hoje.year, hoje.month, dia_cobranca)
    else:
        if hoje.month == 12:
            proximo = date(hoje.year + 1, 1, dia_cobranca)
        else:
            proximo = date(hoje.year, hoje.month + 1, dia_cobranca)

    dias_restantes = (proximo - hoje).days
    dias_no_ciclo = calendar.monthrange(hoje.year, hoje.month)[1]

    if dias_restantes <= 0 or dias_no_ciclo <= 0:
        return Decimal('0.00'), proximo, 0

    valor = preco_por_cnpj * Decimal(dias_restantes) / Decimal(dias_no_ciclo)
    valor = valor.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    return valor, proximo, dias_restantes


class PlanoBPO(models.Model):
    """
    Plano de assinatura para escritórios BPO.
    Preço é por CNPJ ativo/mês; limites são configuráveis pelo admin Django.
    """

    nome = models.CharField(
        max_length=100,
        verbose_name='Nome do Plano',
        help_text='Ex.: BPO Starter, BPO Pro, BPO Enterprise'
    )
    preco_por_cnpj = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name='Preço por CNPJ/mês (R$)',
        help_text='Valor cobrado mensalmente por cada empresa ativa no BPO'
    )
    max_funcionarios_por_cnpj = models.IntegerField(
        null=True,
        blank=True,
        verbose_name='Máx. funcionários por CNPJ',
        help_text='Deixe em branco para ilimitado'
    )
    max_usuarios_bpo = models.IntegerField(
        null=True,
        blank=True,
        verbose_name='Máx. usuários do escritório',
        help_text='Operadores que podem acessar o painel BPO. Deixe em branco para ilimitado'
    )
    max_meses_historico = models.IntegerField(
        null=True,
        blank=True,
        verbose_name='Máx. meses de histórico',
        help_text='Deixe em branco para histórico ilimitado'
    )
    trial_dias = models.IntegerField(
        default=7,
        validators=[MinValueValidator(0)],
        verbose_name='Dias de trial',
        help_text='Dias de uso gratuito ao ativar conta BPO'
    )
    ativo = models.BooleanField(default=True, verbose_name='Ativo')
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Plano BPO'
        verbose_name_plural = 'Planos BPO'
        ordering = ['preco_por_cnpj']

    def __str__(self):
        return f"{self.nome} — R$ {self.preco_por_cnpj}/CNPJ/mês"


class ContaBPO(models.Model):
    """Conta do escritório BPO. Centraliza a cobrança de todas as empresas gerenciadas."""

    STATUS_CHOICES = [
        ('trial', 'Trial'),
        ('active', 'Ativo'),
        ('suspended', 'Suspenso'),
        ('canceled', 'Cancelado'),
    ]

    empresa_bpo = models.OneToOneField(
        Empresa,
        on_delete=models.PROTECT,
        related_name='conta_bpo',
        verbose_name='Empresa do escritório'
    )
    plano = models.ForeignKey(
        PlanoBPO,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='contas',
        verbose_name='Plano BPO'
    )
    dia_cobranca = models.IntegerField(
        default=5,
        validators=[MinValueValidator(1), MaxValueValidator(28)],
        verbose_name='Dia do mês para cobrança',
        help_text='Data de vencimento mensal (1 a 28)'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='trial',
        verbose_name='Status'
    )
    asaas_customer_id = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name='ID cliente Asaas'
    )

    # Overrides individuais por negociação
    override_preco_por_cnpj = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name='Preço especial por CNPJ (R$)',
        help_text='Se informado, substitui o preço do plano para este BPO'
    )
    override_max_usuarios_bpo = models.IntegerField(
        null=True,
        blank=True,
        verbose_name='Limite especial de usuários',
        help_text='Substitui o limite do plano para este BPO'
    )
    override_max_meses_historico = models.IntegerField(
        null=True,
        blank=True,
        verbose_name='Limite especial de histórico (meses)',
        help_text='Substitui o limite do plano para este BPO'
    )
    override_max_funcionarios_por_cnpj = models.IntegerField(
        null=True,
        blank=True,
        verbose_name='Limite especial de funcionários/CNPJ',
        help_text='Substitui o limite do plano para este BPO'
    )

    BILLING_TYPE_CHOICES = [
        ('BOLETO', 'Boleto'),
        ('PIX', 'PIX'),
        ('CREDIT_CARD', 'Cartão de Crédito'),
    ]
    billing_type = models.CharField(
        max_length=20,
        choices=BILLING_TYPE_CHOICES,
        default='BOLETO',
        verbose_name='Forma de pagamento',
        help_text='Método de pagamento usado nas cobranças mensais'
    )

    # Trial
    trial_ativo = models.BooleanField(default=True, verbose_name='Trial ativo')
    trial_expira = models.DateField(null=True, blank=True, verbose_name='Trial expira em')
    trial_used = models.BooleanField(default=False, verbose_name='Trial já utilizado')

    criado_em = models.DateTimeField(default=timezone.now)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Conta BPO'
        verbose_name_plural = 'Contas BPO'
        ordering = ['-criado_em']

    def __str__(self):
        return f"BPO: {self.empresa_bpo.nome} ({self.get_status_display()})"

    # --- Effective limits ---

    def get_effective_preco_por_cnpj(self) -> Decimal:
        if self.override_preco_por_cnpj is not None:
            return self.override_preco_por_cnpj
        if self.plano:
            return self.plano.preco_por_cnpj
        return Decimal('0.00')

    def get_effective_max_usuarios_bpo(self):
        if self.override_max_usuarios_bpo is not None:
            return self.override_max_usuarios_bpo
        if self.plano:
            return self.plano.max_usuarios_bpo
        return None

    def get_effective_max_meses_historico(self):
        if self.override_max_meses_historico is not None:
            return self.override_max_meses_historico
        if self.plano:
            return self.plano.max_meses_historico
        return None

    def get_effective_max_funcionarios_por_cnpj(self):
        if self.override_max_funcionarios_por_cnpj is not None:
            return self.override_max_funcionarios_por_cnpj
        if self.plano:
            return self.plano.max_funcionarios_por_cnpj
        return None

    # --- Utilities ---

    def get_cnpjs_ativos(self) -> int:
        return self.empresas_gerenciadas.filter(status='active').count()

    def proximo_vencimento(self) -> date:
        hoje = date.today()
        if hoje.day < self.dia_cobranca:
            return date(hoje.year, hoje.month, self.dia_cobranca)
        if hoje.month == 12:
            return date(hoje.year + 1, 1, self.dia_cobranca)
        return date(hoje.year, hoje.month + 1, self.dia_cobranca)

    def valor_proxima_fatura(self) -> Decimal:
        preco = self.get_effective_preco_por_cnpj()
        return (preco * self.get_cnpjs_ativos()).quantize(Decimal('0.01'))

    def calcular_rateio_novo_cnpj(self):
        """Retorna (valor, proximo_vencimento, dias_restantes) para novo CNPJ."""
        return calcular_rateio(self.get_effective_preco_por_cnpj(), self.dia_cobranca)

    def is_trial_ativo(self) -> bool:
        if not self.trial_ativo or not self.trial_expira:
            return False
        return date.today() <= self.trial_expira

    def dias_restantes_trial(self) -> int:
        if not self.is_trial_ativo():
            return 0
        return (self.trial_expira - date.today()).days


class EmpresaBPO(models.Model):
    """Vínculo entre uma empresa cliente e a conta BPO que a gerencia."""

    STATUS_CHOICES = [
        ('active', 'Ativa'),
        ('suspended', 'Suspensa'),
        ('canceled', 'Cancelada'),
    ]

    conta_bpo = models.ForeignKey(
        ContaBPO,
        on_delete=models.CASCADE,
        related_name='empresas_gerenciadas',
        verbose_name='Conta BPO'
    )
    empresa = models.OneToOneField(
        Empresa,
        on_delete=models.CASCADE,
        related_name='empresa_bpo',
        verbose_name='Empresa cliente'
    )
    data_ativacao = models.DateField(auto_now_add=True, verbose_name='Data de ativação')
    data_suspensao = models.DateField(
        null=True,
        blank=True,
        verbose_name='Data de suspensão',
        help_text='Preenchido automaticamente quando a empresa é suspensa'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='active',
        verbose_name='Status'
    )
    permite_acesso_cliente = models.BooleanField(
        default=False,
        verbose_name='Permitir acesso do cliente',
        help_text='Se marcado, usuários desta empresa poderão fazer login na plataforma'
    )
    rateio_cobrado = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='Rateio cobrado na ativação (R$)',
        help_text='Valor proporcional cobrado ao ativar este CNPJ'
    )
    asaas_payment_id_rateio = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name='ID pagamento rateio (Asaas)',
        help_text='ID do pagamento avulso de rateio na Asaas'
    )

    criado_em = models.DateTimeField(default=timezone.now)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Empresa gerenciada por BPO'
        verbose_name_plural = 'Empresas gerenciadas por BPO'
        ordering = ['-data_ativacao']

    def __str__(self):
        return f"{self.empresa.nome} ({self.conta_bpo.empresa_bpo.nome})"


class FaturaBPO(models.Model):
    """
    Registro de uma fatura mensal gerada pelo sistema BPO para um escritório.
    Criada pelo management command `cobrar_bpo_mensal` na data de vencimento.
    """

    STATUS_CHOICES = [
        ('pending', 'Pendente'),
        ('confirmed', 'Pago'),
        ('overdue', 'Vencido'),
        ('canceled', 'Cancelado'),
    ]

    conta_bpo = models.ForeignKey(
        ContaBPO,
        on_delete=models.CASCADE,
        related_name='faturas',
        verbose_name='Conta BPO',
    )
    mes_referencia = models.DateField(
        verbose_name='Mês de referência',
        help_text='Primeiro dia do mês de referência',
    )
    cnpjs_cobrados = models.IntegerField(verbose_name='CNPJs cobrados')
    valor = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Valor (R$)')
    asaas_payment_id = models.CharField(
        max_length=100, blank=True, null=True, verbose_name='ID pagamento Asaas'
    )
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name='Status'
    )

    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Fatura BPO'
        verbose_name_plural = 'Faturas BPO'
        ordering = ['-mes_referencia']
        unique_together = [('conta_bpo', 'mes_referencia')]

    def __str__(self):
        return (
            f"Fatura BPO {self.conta_bpo.empresa_bpo.nome} "
            f"— {self.mes_referencia.strftime('%m/%Y')} "
            f"— R$ {self.valor}"
        )
