"""
Página no Django Admin para revisar e aplicar sugestões de ajuste de data_admissao
(quando a data cadastrada é posterior ao lançamento mais antigo já registrado).
"""
from django.contrib import admin
from django.template.response import TemplateResponse
from django.urls import path

from .models_admin_tools import AjusteDataAdmissao
from .services.ajuste_admissao import aplicar_ajustes_admissao, sugerir_ajustes_admissao


@admin.register(AjusteDataAdmissao)
class AjusteDataAdmissaoAdmin(admin.ModelAdmin):

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
                'aplicar/',
                self.admin_site.admin_view(self.aplicar_view),
                name='empresas_aplicar_ajuste_admissao',
            ),
        ]
        return custom + urls

    def changelist_view(self, request, extra_context=None):
        return self.aplicar_view(request)

    def aplicar_view(self, request):
        if request.method == 'POST':
            vinculo_ids = request.POST.getlist('vinculo_id')
            if vinculo_ids:
                total = aplicar_ajustes_admissao([int(v) for v in vinculo_ids])
                self.message_user(request, f'✔ {total} vínculo(s) com data_admissao ajustada.')
            else:
                self.message_user(request, 'Nenhum vínculo selecionado.', level='warning')

        sugestoes = sugerir_ajustes_admissao()
        aplicaveis = [s for s in sugestoes if s['aplicavel']]
        bloqueadas = [s for s in sugestoes if not s['aplicavel']]

        context = {
            **self.admin_site.each_context(request),
            'title': 'Ajuste de data de admissão pelo 1º lançamento',
            'opts': self.model._meta,
            'aplicaveis': aplicaveis,
            'bloqueadas': bloqueadas,
        }
        return TemplateResponse(
            request,
            'admin/empresas/ajuste_data_admissao.html',
            context,
        )
