from django.db import models
from django.utils import timezone
from empresas.models import Empresa
from django.core.validators import MinValueValidator


class Plan(models.Model):
    """Planos de assinatura: Básico, Profissional, Empresarial"""
    
    PLAN_TYPES = [
        ('BASIC', 'Básico'),
        ('PROFESSIONAL', 'Profissional'),
        ('ENTERPRISE', 'Empresarial'),
    ]
    
    SUPPORT_LEVELS = [
        ('EMAIL', 'E-mail'),
        ('PRIORITY', 'Prioritário'),
        ('24_7', '24/7'),
    ]
    
    plan_type = models.CharField(
        max_length=20,
        choices=PLAN_TYPES,
        unique=True,
        verbose_name='Tipo de Plano'
    )
    max_employees = models.IntegerField(
        null=True,
        blank=True,
        verbose_name='Máximo de Colaboradores',
        help_text='Deixe em branco para ilimitado'
    )
    
    # Features
    has_advanced_dashboard = models.BooleanField(
        default=False,
        verbose_name='Dashboard Avançado'
    )
    has_custom_reports = models.BooleanField(
        default=False,
        verbose_name='Relatórios Personalizados'
    )
    has_pdf_export = models.BooleanField(
        default=False,
        verbose_name='Exportar PDF/Excel'
    )
    has_api = models.BooleanField(
        default=False,
        verbose_name='API Access'
    )
    
    # Support
    support_level = models.CharField(
        max_length=20,
        choices=SUPPORT_LEVELS,
        default='EMAIL',
        verbose_name='Nível de Suporte'
    )
    
    # Pricing
    price_monthly = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name='Preço Mensal'
    )
    price_yearly = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name='Preço Anual'
    )

    # Limite de empresas por grupo (matriz + filiais); None = ilimitado
    max_companies = models.IntegerField(
        null=True,
        blank=True,
        verbose_name='Máximo de Empresas no Grupo',
        help_text='Deixe em branco para ilimitado'
    )

    # Limite de histórico em meses para lançamentos
    max_history_months = models.IntegerField(
        null=True,
        blank=True,
        verbose_name='Máximo de Meses de Histórico',
        help_text='Deixe em branco para histórico ilimitado'
    )
    
    # Meta
    active = models.BooleanField(default=True, verbose_name='Ativo')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['plan_type']
        verbose_name = 'Plano'
        verbose_name_plural = 'Planos'
    
    def __str__(self):
        return f"{self.get_plan_type_display()}"
    
    def can_add_employee(self, current_count):
        """Verifica se é possível adicionar mais um colaborador"""
        if self.max_employees is None:  # Ilimitado
            return True
        return current_count < self.max_employees
    
    def get_usage_percentage(self, current_count):
        """Retorna percentual de uso do plano"""
        if self.max_employees is None:
            return 0
        return (current_count / self.max_employees) * 100


class BillingCustomer(models.Model):
    STATUS_CHOICES = [
        ('active', 'Ativo'),
        ('inactive', 'Inativo'),
        ('pending', 'Pendente'),
        ('trial', 'Trial'),
        ('canceled', 'Cancelado'),
    ]

    empresa = models.OneToOneField(Empresa, on_delete=models.CASCADE, related_name='billing_customer')
    plan = models.ForeignKey(Plan, on_delete=models.SET_NULL, null=True, blank=True, related_name='customers', verbose_name='Plano')
    active_employees = models.IntegerField(default=0, verbose_name='Colaboradores Ativos')
    email_cobranca = models.EmailField(blank=True, null=True)
    asaas_customer_id = models.CharField(max_length=100, blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    # Preço especial negociado (ex.: Enterprise sob consulta)
    override_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='Valor mensal especial (R$)',
        help_text='Se informado, substitui o preço do plano para esta empresa na hora da cobrança.'
    )

    # Limites especiais (excecoes por empresa)
    override_max_employees = models.IntegerField(
        null=True,
        blank=True,
        verbose_name='Limite especial de colaboradores',
        help_text='Se informado, substitui o limite do plano para esta empresa.'
    )
    override_max_companies = models.IntegerField(
        null=True,
        blank=True,
        verbose_name='Limite especial de CNPJs no grupo',
        help_text='Se informado, substitui o limite do plano para o grupo desta empresa.'
    )
    override_max_history_months = models.IntegerField(
        null=True,
        blank=True,
        verbose_name='Limite especial de histórico (meses)',
        help_text='Se informado, substitui o limite de histórico do plano para esta empresa.'
    )
    
    # Indica que esta empresa é gerenciada por um BPO (não tem assinatura própria)
    gerenciada_por_bpo = models.ForeignKey(
        'ContaBPO',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='billing_customers',
        verbose_name='Gerenciada por BPO',
        help_text='Se preenchido, a cobrança desta empresa é responsabilidade do escritório BPO vinculado'
    )

    # Trial de 7 dias
    trial_active = models.BooleanField(default=True, verbose_name='Trial Ativo')
    trial_expires = models.DateField(null=True, blank=True, verbose_name='Trial Expira em')
    trial_used = models.BooleanField(default=False, verbose_name='Trial Já Utilizado')
    
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.empresa.nome} ({self.get_status_display()})"
    
    def can_add_employee(self, current_count=None):
        """Verifica se é possível adicionar outro colaborador no plano atual"""
        current_count = self.active_employees if current_count is None else current_count
        if self.override_max_employees is not None:
            return current_count < self.override_max_employees
        if not self.plan:
            return False
        return self.plan.can_add_employee(current_count)
    
    def get_usage_percentage(self):
        """Retorna percentual de uso do plano"""
        max_employees = self.get_effective_max_employees()
        if max_employees is None or max_employees == 0:
            return 0
        return (self.active_employees / max_employees) * 100
    
    def get_employees_remaining(self):
        """Retorna quantos colaboradores ainda podem ser adicionados"""
        max_employees = self.get_effective_max_employees()
        if max_employees is None:
            return None  # Ilimitado
        return max_employees - self.active_employees

    def get_effective_max_employees(self):
        """Retorna o limite efetivo de colaboradores (plano ou excecao)."""
        if self.override_max_employees is not None:
            return self.override_max_employees
        if not self.plan:
            return None
        return self.plan.max_employees

    def get_effective_max_companies(self):
        """Retorna o limite efetivo de CNPJs no grupo (plano ou excecao)."""
        if self.override_max_companies is not None:
            return self.override_max_companies
        if not self.plan:
            return None
        return self.plan.max_companies

    def get_effective_max_history_months(self):
        """Retorna o limite efetivo de histórico em meses (plano ou excecao)."""
        if self.override_max_history_months is not None:
            return self.override_max_history_months
        if not self.plan:
            return None
        return self.plan.max_history_months
    
    def is_trial_active(self):
        """Verifica se trial está ativo"""
        from datetime import date
        if not self.trial_active or not self.trial_expires:
            return False
        return date.today() <= self.trial_expires
    
    def days_remaining_trial(self):
        """Retorna quantidade de dias restantes no trial"""
        from datetime import date
        if not self.is_trial_active():
            return 0
        return (self.trial_expires - date.today()).days
    
    def trial_warning_message(self):
        """Retorna mensagem de aviso do trial"""
        days = self.days_remaining_trial()
        if days == 0:
            return "Seu trial expira HOJE! Assine agora para continuar usando o sistema."
        elif days == 1:
            return "Seu trial expira em 1 dia. Assine agora para não perder acesso!"
        elif days <= 3:
            return f"Seu trial expira em {days} dias. Aproveite para assinar!"
        else:
            return f"Você tem {days} dias de trial restantes"


class PricingPlan(models.Model):
    PERIODICITY_CHOICES = [
        ('MONTHLY', 'Mensal'),
        ('YEARLY', 'Anual'),
    ]

    name = models.CharField(max_length=120, default='Plano FGTS Web')
    description = models.CharField(max_length=255, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    periodicity = models.CharField(max_length=10, choices=PERIODICITY_CHOICES, default='MONTHLY')
    active = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=1)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['sort_order', '-updated_at']

    def __str__(self):
        return f"{self.name} ({self.get_periodicity_display()})"


class Subscription(models.Model):
    PERIODICITY_CHOICES = [
        ('MONTHLY', 'Mensal'),
        ('YEARLY', 'Anual'),
    ]

    STATUS_CHOICES = [
        ('active', 'Ativa'),
        ('pending', 'Pendente'),
        ('overdue', 'Em atraso'),
        ('canceled', 'Cancelada'),
        ('suspended', 'Suspensa'),
    ]

    customer = models.ForeignKey(BillingCustomer, on_delete=models.CASCADE, related_name='subscriptions')
    asaas_subscription_id = models.CharField(max_length=100, blank=True, null=True)
    plan_name = models.CharField(max_length=120, default='Plano FGTS Web')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    periodicity = models.CharField(max_length=10, choices=PERIODICITY_CHOICES, default='MONTHLY')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    next_due_date = models.DateField(blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.plan_name} - {self.customer.empresa.nome}"


class Feedback(models.Model):
    """Modelo para armazenar feedbacks, elogios, reclamações e sugestões dos usuários"""
    
    TIPO_CHOICES = [
        ('sugestao', 'Sugestão'),
        ('elogio', 'Elogio'),
        ('reclamacao', 'Reclamação'),
        ('bug', 'Bug/Erro'),
        ('outro', 'Outro'),
    ]
    
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='feedbacks')
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, verbose_name='Tipo de Feedback')
    titulo = models.CharField(max_length=255, verbose_name='Título')
    mensagem = models.TextField(verbose_name='Mensagem')
    email_resposta = models.EmailField(blank=True, verbose_name='Email para Resposta')
    respondido = models.BooleanField(default=False, verbose_name='Respondido')
    resposta = models.TextField(blank=True, verbose_name='Resposta do Time')
    
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-criado_em']
        verbose_name = 'Feedback'
        verbose_name_plural = 'Feedbacks'
    
    def __str__(self):
        return f"[{self.get_tipo_display()}] {self.titulo} - {self.empresa.nome}"


class Payment(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pendente'),
        ('confirmed', 'Confirmado'),
        ('overdue', 'Em atraso'),
        ('canceled', 'Cancelado'),
    ]

    subscription = models.ForeignKey(Subscription, on_delete=models.CASCADE, related_name='payments')
    asaas_payment_id = models.CharField(max_length=100, blank=True, null=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    due_date = models.DateField()
    pay_date = models.DateField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    invoice_url = models.URLField(blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.subscription.customer.empresa.nome} - {self.amount} ({self.get_status_display()})"


# Importar models BPO para que o Django os descubra dentro do app billing
from .models_bpo import PlanoBPO, ContaBPO, EmpresaBPO, FaturaBPO, calcular_rateio  # noqa: E402, F401
