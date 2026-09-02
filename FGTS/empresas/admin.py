from django.contrib import admin
from .admin_feature import *
from .admin_grupo import *
from .models import Empresa
from .models_relatorio import RelatorioPremium
from .models import EmailLog
from .models_leads import LeadEmailFlow
from .models_grupo import TipoVinculo


@admin.register(TipoVinculo)
class TipoVinculoAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'descricao', 'percentual_fgts', 'ativo')
    list_editable = ('ativo',)
    readonly_fields = ('id',)
    ordering = ('codigo',)

    def has_delete_permission(self, request, obj=None):
        if obj is not None and obj.vinculos.exists():
            return False
        return super().has_delete_permission(request, obj)


@admin.register(Empresa)
class EmpresaAdmin(admin.ModelAdmin):
	list_display = ('nome', 'cnpj', 'codigo_folha', 'cidade', 'uf', 'grupo', 'is_matriz_flag')
	search_fields = ('nome', 'cnpj')
	list_filter = ('grupo',)

	@admin.display(description='Matriz?')
	def is_matriz_flag(self, obj):
		return obj.is_matriz


# Admin para RelatorioPremium
@admin.register(RelatorioPremium)
class RelatorioPremiumAdmin(admin.ModelAdmin):
	list_display = ('email', 'data_geracao')
	search_fields = ('email',)
	list_filter = ('data_geracao',)


# Admin para EmailLog
@admin.register(EmailLog)
class EmailLogAdmin(admin.ModelAdmin):
	list_display = ('email', 'status', 'data_envio', 'relatorio')
	search_fields = ('email', 'mensagem')
	list_filter = ('status', 'data_envio')


@admin.register(LeadEmailFlow)
class LeadEmailFlowAdmin(admin.ModelAdmin):
	list_display = ('email', 'status', 'trigger_source', 'step', 'next_send_at', 'last_sent_at')
	search_fields = ('email',)
	list_filter = ('status', 'trigger_source')
