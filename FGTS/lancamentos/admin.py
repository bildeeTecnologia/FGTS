from django.contrib import admin
from django.utils import timezone
from django.utils.html import format_html

from lancamentos.models import Lancamento
from lancamentos.models_relatorio import RelatorioTask


@admin.register(RelatorioTask)
class RelatorioTaskAdmin(admin.ModelAdmin):
    list_display = ('pk', 'empresa', 'usuario', 'status', 'total_lancamentos', 'criado_em', 'atualizado_em')
    list_filter = ('status',)
    readonly_fields = ('criado_em', 'atualizado_em', 'resultado_json', 'parametros_json', 'avisos_json')
    search_fields = ('empresa__nome', 'usuario__email')
    ordering = ('-criado_em',)


def _confirmar_cef(modeladmin, request, queryset):
    agora = timezone.now()
    atualizados = queryset.update(
        pago=True,
        fonte_confirmacao_pagamento='extrato_analitico',
        pago_em=agora,
    )
    modeladmin.message_user(
        request,
        f'{atualizados} lançamento(s) marcado(s) como confirmados pelo Extrato Analítico CEF.',
    )


_confirmar_cef.short_description = 'Confirmar como pago via Extrato CEF (fonte de verdade)'


def _desmarcar_pago(modeladmin, request, queryset):
    atualizados = queryset.update(
        pago=False,
        fonte_confirmacao_pagamento=None,
        pago_em=None,
        data_pagto=None,
        valor_pago=None,
    )
    modeladmin.message_user(request, f'{atualizados} lançamento(s) desmarcado(s).')


_desmarcar_pago.short_description = 'Desmarcar como pago (reverter)'


@admin.register(Lancamento)
class LancamentoAdmin(admin.ModelAdmin):
    list_display = (
        'empresa',
        'funcionario',
        'competencia',
        'parcela_13',
        'valor_fgts',
        'status_pago',
        'fonte_confirmacao_pagamento',
        'data_pagto',
    )
    list_filter = (
        'pago',
        'fonte_confirmacao_pagamento',
        'empresa',
        'parcela_13',
    )
    search_fields = (
        'empresa__nome',
        'funcionario__nome',
        'funcionario__pis',
        'competencia',
    )
    readonly_fields = ('criado_em', 'atualizado_em', 'pago_em')
    ordering = ('-competencia', 'empresa', 'funcionario')
    actions = [_confirmar_cef, _desmarcar_pago]

    @admin.display(description='Pago', boolean=True)
    def status_pago(self, obj):
        return obj.pago
