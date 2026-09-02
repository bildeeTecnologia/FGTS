from django.contrib import admin
from .models import Plan, BillingCustomer, Subscription, Payment, PricingPlan, Feedback
from .models_bpo import PlanoBPO, ContaBPO, EmpresaBPO, FaturaBPO


@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = ('get_plan_type_display', 'max_employees', 'max_history_months', 'support_level', 'price_monthly', 'active')
    list_filter = ('plan_type', 'support_level', 'active')
    search_fields = ('plan_type',)
    fieldsets = (
        ('Tipo de Plano', {
            'fields': ('plan_type', 'max_employees', 'max_history_months', 'active')
        }),
        ('Features', {
            'fields': (
                'has_advanced_dashboard',
                'has_custom_reports',
                'has_pdf_export',
                'has_api',
            )
        }),
        ('Suporte', {
            'fields': ('support_level',)
        }),
        ('Preços', {
            'fields': ('price_monthly', 'price_yearly')
        }),
    )
    readonly_fields = ('created_at', 'updated_at')
    
    def get_plan_type_display(self, obj):
        return obj.get_plan_type_display()
    get_plan_type_display.short_description = 'Plano'


@admin.register(BillingCustomer)
class BillingCustomerAdmin(admin.ModelAdmin):
    list_display = ('empresa', 'plan', 'override_price', 'active_employees', 'status', 'created_at', 'override_max_employees', 'override_max_companies', 'override_max_history_months')
    list_filter = ('plan', 'status')
    search_fields = ('empresa__nome', 'asaas_customer_id')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Empresa e Plano', {
            'fields': ('empresa', 'plan', 'active_employees')
        }),
        ('Cobrança', {
            'fields': ('email_cobranca', 'status', 'asaas_customer_id', 'override_price', 'gerenciada_por_bpo'),
            'description': 'Se "Valor mensal especial" estiver preenchido, ele prevalece sobre o preço do plano.',
        }),
        ('Exceções de Limite', {
            'fields': ('override_max_employees', 'override_max_companies', 'override_max_history_months')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('customer', 'plan_name', 'amount', 'periodicity', 'status', 'next_due_date', 'asaas_subscription_id')
    search_fields = ('customer__empresa__nome', 'asaas_subscription_id')


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('subscription', 'amount', 'due_date', 'status', 'asaas_payment_id')
    search_fields = ('subscription__customer__empresa__nome', 'asaas_payment_id')
    list_filter = ('status',)


@admin.register(PricingPlan)
class PricingPlanAdmin(admin.ModelAdmin):
    list_display = ('name', 'amount', 'periodicity', 'active', 'updated_at')
    list_filter = ('periodicity', 'active')
    search_fields = ('name',)
    ordering = ('sort_order', '-updated_at')


@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'get_tipo_display', 'empresa', 'criado_em', 'respondido')
    list_filter = ('tipo', 'respondido', 'criado_em')
    search_fields = ('titulo', 'mensagem', 'empresa__nome')
    readonly_fields = ('criado_em', 'atualizado_em')
    fieldsets = (
        ('Feedback', {
            'fields': ('empresa', 'tipo', 'titulo', 'mensagem', 'email_resposta')
        }),
        ('Status', {
            'fields': ('respondido', 'resposta')
        }),
        ('Timestamps', {
            'fields': ('criado_em', 'atualizado_em'),
            'classes': ('collapse',)
        }),
    )
    actions = ['marcar_respondido']
    
    def marcar_respondido(self, request, queryset):
        queryset.update(respondido=True)
        self.message_user(request, f'{queryset.count()} feedbacks marcados como respondidos.')
    marcar_respondido.short_description = 'Marcar como respondido'


# ─── BPO ──────────────────────────────────────────────────────────────────────

@admin.register(PlanoBPO)
class PlanoBPOAdmin(admin.ModelAdmin):
    list_display = ('nome', 'preco_por_cnpj', 'max_funcionarios_por_cnpj', 'max_usuarios_bpo', 'max_meses_historico', 'trial_dias', 'ativo')
    list_filter = ('ativo',)
    search_fields = ('nome',)
    fieldsets = (
        ('Plano', {'fields': ('nome', 'ativo')}),
        ('Preço', {'fields': ('preco_por_cnpj',)}),
        ('Limites', {
            'fields': ('max_funcionarios_por_cnpj', 'max_usuarios_bpo', 'max_meses_historico'),
            'description': 'Deixe em branco para ilimitado',
        }),
        ('Trial', {'fields': ('trial_dias',)}),
    )


class EmpresaBPOInline(admin.TabularInline):
    model = EmpresaBPO
    extra = 0
    fields = ('empresa', 'status', 'permite_acesso_cliente', 'data_ativacao', 'data_suspensao', 'rateio_cobrado')
    readonly_fields = ('data_ativacao', 'data_suspensao', 'rateio_cobrado')
    can_delete = False


class FaturasBPOInline(admin.TabularInline):
    model = FaturaBPO
    extra = 0
    fields = ('mes_referencia', 'cnpjs_cobrados', 'valor', 'status', 'asaas_payment_id')
    readonly_fields = ('mes_referencia', 'cnpjs_cobrados', 'valor', 'asaas_payment_id')
    can_delete = False
    ordering = ('-mes_referencia',)
    verbose_name_plural = 'Faturas mensais'


@admin.register(ContaBPO)
class ContaBPOAdmin(admin.ModelAdmin):
    list_display = ('empresa_bpo', 'plano', 'get_cnpjs_ativos', 'status', 'dia_cobranca', 'get_effective_preco_por_cnpj', 'criado_em')
    list_filter = ('status', 'plano')
    search_fields = ('empresa_bpo__nome', 'asaas_customer_id')
    readonly_fields = ('criado_em', 'atualizado_em')
    inlines = [EmpresaBPOInline, FaturasBPOInline]
    fieldsets = (
        ('Escritório BPO', {'fields': ('empresa_bpo', 'plano', 'status', 'dia_cobranca', 'billing_type')}),
        ('Cobrança Asaas', {'fields': ('asaas_customer_id',)}),
        ('Exceções de Limite', {
            'fields': ('override_preco_por_cnpj', 'override_max_usuarios_bpo', 'override_max_meses_historico', 'override_max_funcionarios_por_cnpj'),
            'description': 'Deixe em branco para usar os valores do plano. Preencha para negociações especiais.',
            'classes': ('collapse',),
        }),
        ('Trial', {'fields': ('trial_ativo', 'trial_expira', 'trial_used')}),
        ('Timestamps', {'fields': ('criado_em', 'atualizado_em'), 'classes': ('collapse',)}),
    )

    def get_cnpjs_ativos(self, obj):
        return obj.get_cnpjs_ativos()
    get_cnpjs_ativos.short_description = 'CNPJs ativos'

    def get_effective_preco_por_cnpj(self, obj):
        return f'R$ {obj.get_effective_preco_por_cnpj()}'
    get_effective_preco_por_cnpj.short_description = 'Preço/CNPJ efetivo'


@admin.register(EmpresaBPO)
class EmpresaBPOAdmin(admin.ModelAdmin):
    list_display = ('empresa', 'conta_bpo', 'status', 'permite_acesso_cliente', 'data_ativacao', 'data_suspensao', 'rateio_cobrado')
    list_filter = ('status', 'permite_acesso_cliente')
    search_fields = ('empresa__nome', 'empresa__cnpj', 'conta_bpo__empresa_bpo__nome')
    readonly_fields = ('data_ativacao', 'data_suspensao', 'rateio_cobrado', 'asaas_payment_id_rateio', 'criado_em', 'atualizado_em')
    fieldsets = (
        ('Vínculo', {'fields': ('conta_bpo', 'empresa', 'status', 'permite_acesso_cliente')}),
        ('Datas', {'fields': ('data_ativacao', 'data_suspensao')}),
        ('Cobrança na ativação', {'fields': ('rateio_cobrado', 'asaas_payment_id_rateio'), 'classes': ('collapse',)}),
        ('Timestamps', {'fields': ('criado_em', 'atualizado_em'), 'classes': ('collapse',)}),
    )


@admin.register(FaturaBPO)
class FaturaBPOAdmin(admin.ModelAdmin):
    list_display = ('conta_bpo', 'mes_referencia', 'cnpjs_cobrados', 'valor', 'status', 'criado_em')
    list_filter = ('status',)
    search_fields = ('conta_bpo__empresa_bpo__nome', 'asaas_payment_id')
    readonly_fields = ('criado_em', 'atualizado_em')
    ordering = ('-mes_referencia',)
