from django.db import models
from datetime import date
from empresas.models import Empresa
from empresas.models_grupo import FuncionarioVinculo
from django.core.exceptions import ValidationError


class Funcionario(models.Model):
    nome = models.CharField(max_length=255, verbose_name='Nome')
    pis = models.CharField(max_length=15, blank=True, verbose_name='PIS')
    cpf = models.CharField(max_length=14, verbose_name='CPF')
    cbo = models.CharField(max_length=10, blank=True, verbose_name='CBO')
    carteira_profissional = models.CharField(max_length=20, blank=True, verbose_name='Carteira Profissional')
    serie_carteira = models.CharField(max_length=10, blank=True, verbose_name='Série Carteira')
    data_nascimento = models.DateField(null=True, blank=True, verbose_name='Data Nascimento')
    observacao = models.TextField(blank=True, verbose_name='Observação')

    def vinculo_atual(self):
        # Retorna o vínculo mais recente, mesmo que esteja demitido
        return self.vinculos.order_by('-data_admissao').first()

    def historico_vinculos(self):
        return self.vinculos.order_by('-data_admissao')

    @property
    def empresa(self):
        v = self.vinculo_atual()
        return v.empresa if v else None

    @empresa.setter
    def empresa(self, value):
        # Compatibilidade com código legado que define empresa diretamente
        self._empresa_override = value

    @property
    def data_admissao(self):
        v = self.vinculo_atual()
        return v.data_admissao if v else None

    @data_admissao.setter
    def data_admissao(self, value):
        # Compatibilidade com código legado que define data_admissao diretamente
        self._data_admissao_override = value

    @property
    def data_demissao(self):
        v = self.vinculo_atual()
        return v.data_demissao if v else None

    @property
    def status(self):
        v = self.vinculo_atual()
        if v and v.data_demissao:
            return 'demitido'
        return 'ativo'

    def __str__(self):
        return self.nome
    
    def clean(self):
        """Valida se o funcionário pode ser criado dentro do plano da empresa"""
        super().clean()
        # Usar empresa informada no formulário (override) ou vínculo atual
        empresa_ctx = getattr(self, '_empresa_override', None)
        if not empresa_ctx:
            if not self.pk:
                return  # ainda sem vínculo e sem contexto de empresa
            empresa_ctx = self.empresa

        try:
            billing_customer = empresa_ctx.billing_customer
        except Exception:
            return  # Sem billing configurado, não bloqueia criação

        if billing_customer.status == 'trial':
            return  # Trial é ilimitado

        if not billing_customer.plan and billing_customer.override_max_employees is None:
            raise ValidationError(
                'Empresa não possui plano configurado. '
                'Contacte o administrador.'
            )

        # Contar vínculos ativos na empresa (sem depender de FK removido)
        active_count = FuncionarioVinculo.objects.filter(
            empresa=empresa_ctx,
            data_demissao__isnull=True
        ).count()

        if not billing_customer.can_add_employee(active_count):
            plan_name = billing_customer.plan.get_plan_type_display() if billing_customer.plan else 'Especial'
            max_employees = billing_customer.get_effective_max_employees()
            raise ValidationError(
                f'Seu plano {plan_name} permite no máximo '
                f'{max_employees} colaboradores ativos. '
                f'Você já possui {active_count}. '
                f'Faça upgrade para adicionar mais.'
            )

    def save(self, *args, **kwargs):
        # Salva o funcionário e cria vínculo se overrides foram definidos
        super().save(*args, **kwargs)
        empresa_override = getattr(self, '_empresa_override', None)
        data_adm_override = getattr(self, '_data_admissao_override', None)
        data_dem_override = getattr(self, '_data_demissao_override', None)
        if empresa_override and not self.vinculos.exists():
            FuncionarioVinculo.objects.create(
                funcionario=self,
                empresa=empresa_override,
                data_admissao=data_adm_override or date.today(),
                data_demissao=data_dem_override,
            )
    
    class Meta:
        verbose_name = 'Funcionário'
        verbose_name_plural = 'Funcionários'
        # Permite múltiplos vínculos de um mesmo CPF (mesma empresa ou não)
        # Exemplo: um funcionário pode ser horista e advogado simultaneamente


class DiagnosticoOrfaos(models.Model):
    """Modelo âncora para a página de diagnóstico no admin. Não cria tabela."""

    class Meta:
        managed = False
        verbose_name = 'Diagnóstico de Órfãos'
        verbose_name_plural = 'Diagnóstico de Dados Órfãos'
        app_label = 'funcionarios'
