from django.contrib import admin
from django.utils.html import format_html

from .admin_diagnostico import DiagnosticoOrfaosAdmin  # noqa: F401
from .models import Funcionario


def _excluir_orfaos_seguros(modeladmin, request, queryset):
    """
    Exclui somente funcionários sem vínculo E sem lançamentos.
    Recusa individualmente qualquer registro que tenha lançamentos,
    para proteger dados de clientes.
    """
    from lancamentos.models import Lancamento
    from empresas.models_grupo import FuncionarioVinculo

    bloqueados = []
    para_deletar = []

    for func in queryset:
        tem_vinculo = FuncionarioVinculo.objects.filter(funcionario=func).exists()
        tem_lancamento = Lancamento.objects.filter(funcionario=func).exists()

        if tem_vinculo or tem_lancamento:
            motivo = []
            if tem_vinculo:
                motivo.append('tem vínculo')
            if tem_lancamento:
                motivo.append('tem lançamentos')
            bloqueados.append(f'{func.nome} (id={func.pk}) — {", ".join(motivo)}')
        else:
            para_deletar.append(func)

    if bloqueados:
        modeladmin.message_user(
            request,
            format_html(
                '⛔ {} registro(s) <strong>não foram excluídos</strong> pois possuem dados vinculados:<br>{}',
                len(bloqueados),
                format_html('<br>'.join(bloqueados)),
            ),
            level='ERROR',
        )

    if para_deletar:
        ids = [f.pk for f in para_deletar]
        Funcionario.objects.filter(pk__in=ids).delete()
        modeladmin.message_user(
            request,
            f'✔ {len(para_deletar)} funcionário(s) excluído(s) com segurança.',
        )


_excluir_orfaos_seguros.short_description = '🗑 Excluir órfãos seguros (sem vínculo e sem lançamentos)'


@admin.register(Funcionario)
class FuncionarioAdmin(admin.ModelAdmin):
    list_display = ('id', 'nome', 'cpf', 'pis', 'empresa_atual', 'status_display')
    search_fields = ('nome', 'cpf', 'pis')
    ordering = ('nome',)
    readonly_fields = ('id',)
    actions = [_excluir_orfaos_seguros]

    fieldsets = (
        (None, {
            'fields': ('id', 'nome', 'cpf', 'pis'),
        }),
        ('Dados complementares', {
            'fields': ('cbo', 'carteira_profissional', 'serie_carteira', 'data_nascimento', 'observacao'),
            'classes': ('collapse',),
        }),
    )

    @admin.display(description='Empresa atual')
    def empresa_atual(self, obj):
        e = obj.empresa
        return e.nome if e else '—'

    @admin.display(description='Status')
    def status_display(self, obj):
        v = obj.vinculo_atual()
        if not v:
            return format_html('<span style="color:#e74c3c;font-weight:bold;">Sem vínculo</span>')
        if v.data_demissao:
            return format_html('<span style="color:#f39c12;">Demitido</span>')
        return format_html('<span style="color:#2ecc71;font-weight:bold;">Ativo</span>')

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
