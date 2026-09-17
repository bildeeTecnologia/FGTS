"""
Página no Django Admin para recalcular manualmente o cache da Auditoria de Lançamentos.

Necessária porque edições feitas direto no banco (ex.: Supabase SQL Editor) não passam
pelos signals em `lancamentos/signals_auditoria.py` e por isso não invalidam o cache sozinhas.
"""
from django.contrib import admin
from django.template.response import TemplateResponse
from django.urls import path

from .models_admin_tools import RecalcularAuditoria
from .services.auditoria_vinculo import invalidar_cache_tudo


@admin.register(RecalcularAuditoria)
class RecalcularAuditoriaAdmin(admin.ModelAdmin):

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path(
                'recalcular/',
                self.admin_site.admin_view(self.recalcular_view),
                name='lancamentos_recalcular_auditoria',
            ),
        ]
        return custom + urls

    def changelist_view(self, request, extra_context=None):
        return self.recalcular_view(request)

    def recalcular_view(self, request):
        if request.method == 'POST' and request.POST.get('confirmar') == 'sim':
            total = invalidar_cache_tudo()
            self.message_user(
                request,
                f'✔ Cache de auditoria recalculado para {total} vínculo(s).',
            )

        context = {
            **self.admin_site.each_context(request),
            'title': 'Recalcular auditoria de lançamentos',
            'opts': self.model._meta,
        }
        return TemplateResponse(
            request,
            'admin/lancamentos/recalcular_auditoria.html',
            context,
        )
