from django.contrib import admin
from .models_grupo import GrupoEmpresa, FuncionarioVinculo, TransferenciaFuncionario

@admin.register(GrupoEmpresa)
class GrupoEmpresaAdmin(admin.ModelAdmin):
    list_display = ("nome", "cnpj_base", "empresa_principal", "data_criacao")
    search_fields = ("nome", "cnpj_base")
    autocomplete_fields = ("empresa_principal",)

@admin.register(FuncionarioVinculo)
class FuncionarioVinculoAdmin(admin.ModelAdmin):
    list_display = ('funcionario', 'empresa', 'tipo_vinculo_display', 'matricula', 'data_admissao', 'data_demissao', 'status', 'motivo_saida')
    search_fields = ('funcionario__nome', 'funcionario__cpf', 'empresa__nome', 'cargo', 'matricula')
    list_filter = ('empresa', 'status', 'tipo_vinculo', 'motivo_saida')
    raw_id_fields = ('funcionario', 'empresa')
    readonly_fields = ('id',)

    fieldsets = (
        (None, {
            'fields': ('id', 'funcionario', 'empresa', 'matricula', 'tipo_vinculo'),
        }),
        ('Período', {
            'fields': ('data_admissao', 'data_demissao', 'status', 'motivo_saida', 'data_transferencia'),
        }),
        ('Dados complementares', {
            'fields': ('cargo', 'salario', 'observacoes'),
            'classes': ('collapse',),
        }),
    )

    @admin.display(description='Tipo de vínculo')
    def tipo_vinculo_display(self, obj):
        if obj.tipo_vinculo:
            return obj.tipo_vinculo.descricao
        return 'CLT (padrão)'

@admin.register(TransferenciaFuncionario)
class TransferenciaFuncionarioAdmin(admin.ModelAdmin):
    list_display = ("funcionario", "empresa_origem", "empresa_destino", "data_transferencia", "usuario_responsavel")
    search_fields = ("funcionario__nome", "empresa_origem__nome", "empresa_destino__nome")
    list_filter = ("empresa_origem", "empresa_destino")
