"""
Views da tela de Auditoria de Lançamentos (esperado x realizado x justificado).

Ver documentação de uso em: empresas/templates/ajuda/manual.html#auditoria-lancamentos
"""
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator
from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View

from empresas.models import Empresa
from empresas.models_grupo import FuncionarioVinculo
from fgtsweb.mixins import get_allowed_empresa_ids, is_empresa_allowed

from .forms_lacuna import JustificativaLacunaForm
from .models_lacuna import LacunaJustificativa
from .services.auditoria_export import gerar_xlsx_auditoria_lista, gerar_xlsx_auditoria_vinculo
from .services.auditoria_vinculo import (
    auditar_vinculo, data_minima_historico_contratado, resumir_auditoria_vinculo,
)


def _resumos_empresa(empresa, status_filtro=''):
    """Lista de resumos de auditoria (um por vínculo) para a empresa, já ordenada por pendências."""
    vinculos_qs = FuncionarioVinculo.objects.filter(empresa=empresa).select_related(
        'funcionario', 'empresa'
    ).order_by('funcionario__nome', 'data_admissao')

    if status_filtro:
        vinculos_qs = vinculos_qs.filter(status=status_filtro)

    resumos = [resumir_auditoria_vinculo(vinculo) for vinculo in vinculos_qs]
    resumos.sort(key=lambda r: r['qtd_pendentes'], reverse=True)
    return resumos


class AuditoriaLancamentosListView(LoginRequiredMixin, View):
    """Lista vínculos de uma empresa com contadores esperado/realizado/justificado/pendente."""
    template_name = 'lancamentos/auditoria_list.html'

    def get(self, request):
        allowed_ids = get_allowed_empresa_ids(request.user)
        if allowed_ids is None:
            empresas = Empresa.objects.all().order_by('nome')
        else:
            empresas = Empresa.objects.filter(codigo__in=allowed_ids).order_by('nome')

        empresa_id = request.GET.get('empresa', '').strip()
        empresa = None
        if empresa_id:
            empresa = get_object_or_404(Empresa, pk=empresa_id)
            if not is_empresa_allowed(request.user, empresa.codigo):
                return HttpResponseForbidden('Empresa não permitida para este usuário.')
        elif empresas.count() == 1:
            empresa = empresas.first()

        apenas_pendentes = request.GET.get('apenas_pendentes') == '1'
        status_filtro = request.GET.get('status', '').strip()

        contexto = {
            'empresas': empresas,
            'empresa_filtro': str(empresa.pk) if empresa else empresa_id,
            'empresa': empresa,
            'apenas_pendentes': apenas_pendentes,
            'status_filtro': status_filtro,
            'status_choices': FuncionarioVinculo.STATUS_CHOICES,
            'page_obj': None,
            'total_vinculos': 0,
            'total_pendencias': 0,
            'total_fora_do_plano': 0,
            'data_minima_historico': None,
        }

        if empresa is None:
            return render(request, self.template_name, contexto)

        contexto['data_minima_historico'] = data_minima_historico_contratado(empresa)

        resumos_completos = _resumos_empresa(empresa, status_filtro)
        resumos = [
            r for r in resumos_completos
            if not apenas_pendentes or r['qtd_pendentes'] > 0
        ]

        paginator = Paginator(resumos, 20)
        page_obj = paginator.get_page(request.GET.get('page', 1))

        contexto['page_obj'] = page_obj
        contexto['total_vinculos'] = len(resumos)
        contexto['total_pendencias'] = sum(r['qtd_pendentes'] for r in resumos)
        contexto['total_fora_do_plano'] = sum(r['qtd_fora_do_plano'] for r in resumos)
        return render(request, self.template_name, contexto)


class AuditoriaExportListXlsxView(LoginRequiredMixin, View):
    """Exporta a lista de vínculos auditados (com os mesmos filtros da tela) em XLSX."""

    def get(self, request):
        empresa_id = request.GET.get('empresa', '').strip()
        if not empresa_id:
            return HttpResponse('Selecione uma empresa antes de exportar.', status=400)

        empresa = get_object_or_404(Empresa, pk=empresa_id)
        if not is_empresa_allowed(request.user, empresa.codigo):
            return HttpResponseForbidden('Empresa não permitida para este usuário.')

        status_filtro = request.GET.get('status', '').strip()
        apenas_pendentes = request.GET.get('apenas_pendentes') == '1'

        resumos = _resumos_empresa(empresa, status_filtro)
        if apenas_pendentes:
            resumos = [r for r in resumos if r['qtd_pendentes'] > 0]

        xlsx_bytes = gerar_xlsx_auditoria_lista(empresa, resumos)
        response = HttpResponse(
            xlsx_bytes,
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        )
        response['Content-Disposition'] = f'attachment; filename="auditoria_lancamentos_{empresa.pk}.xlsx"'
        return response


class AuditoriaVinculoDetailView(LoginRequiredMixin, View):
    """Timeline completa das competências esperadas de um vínculo."""
    template_name = 'lancamentos/auditoria_vinculo_detail.html'

    def get(self, request, vinculo_id):
        vinculo = get_object_or_404(
            FuncionarioVinculo.objects.select_related('funcionario', 'empresa', 'tipo_vinculo'),
            pk=vinculo_id,
        )
        if not is_empresa_allowed(request.user, vinculo.empresa_id):
            return HttpResponseForbidden('Vínculo não pertence a uma empresa permitida para este usuário.')

        auditoria = auditar_vinculo(vinculo)
        contexto = {
            'vinculo': vinculo,
            'auditoria': auditoria,
            'form_justificativa': JustificativaLacunaForm(),
        }
        return render(request, self.template_name, contexto)


class AuditoriaExportVinculoXlsxView(LoginRequiredMixin, View):
    """Exporta a linha do tempo completa de competências de um vínculo em XLSX."""

    def get(self, request, vinculo_id):
        vinculo = get_object_or_404(
            FuncionarioVinculo.objects.select_related('funcionario', 'empresa'),
            pk=vinculo_id,
        )
        if not is_empresa_allowed(request.user, vinculo.empresa_id):
            return HttpResponseForbidden('Vínculo não pertence a uma empresa permitida para este usuário.')

        auditoria = auditar_vinculo(vinculo)
        xlsx_bytes = gerar_xlsx_auditoria_vinculo(vinculo, auditoria)
        response = HttpResponse(
            xlsx_bytes,
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        )
        response['Content-Disposition'] = f'attachment; filename="auditoria_vinculo_{vinculo.pk}.xlsx"'
        return response


class LacunaJustificarView(LoginRequiredMixin, View):
    """Cria/atualiza justificativas em lote para as competências selecionadas de um vínculo."""

    def post(self, request, vinculo_id):
        vinculo = get_object_or_404(FuncionarioVinculo, pk=vinculo_id)
        if not is_empresa_allowed(request.user, vinculo.empresa_id):
            return HttpResponseForbidden('Vínculo não pertence a uma empresa permitida para este usuário.')

        itens_selecionados = request.POST.getlist('itens')
        if not itens_selecionados:
            messages.error(request, '❌ Selecione ao menos uma competência para justificar.')
            return redirect('auditoria-vinculo-detail', vinculo_id=vinculo.pk)

        form = JustificativaLacunaForm(request.POST)
        if not form.is_valid():
            for erros in form.errors.values():
                for erro in erros:
                    messages.error(request, f'❌ {erro}')
            return redirect('auditoria-vinculo-detail', vinculo_id=vinculo.pk)

        motivo = form.cleaned_data['motivo']
        observacao = form.cleaned_data['observacao']

        criadas = 0
        atualizadas = 0
        for item in itens_selecionados:
            competencia, _, parcela_raw = item.partition('|')
            parcela_13 = int(parcela_raw) if parcela_raw else None
            _, created = LacunaJustificativa.objects.update_or_create(
                vinculo=vinculo,
                competencia=competencia,
                parcela_13=parcela_13,
                defaults={
                    'motivo': motivo,
                    'observacao': observacao,
                    'usuario': request.user,
                },
            )
            if created:
                criadas += 1
            else:
                atualizadas += 1

        messages.success(
            request,
            f'✅ {criadas + atualizadas} competência(s) justificada(s) '
            f'({criadas} nova(s), {atualizadas} atualizada(s)).'
        )
        return redirect('auditoria-vinculo-detail', vinculo_id=vinculo.pk)


class LacunaRemoverView(LoginRequiredMixin, View):
    """Remove uma justificativa, devolvendo a lacuna ao status 'Pendente'."""

    def post(self, request, pk):
        justificativa = get_object_or_404(
            LacunaJustificativa.objects.select_related('vinculo'), pk=pk
        )
        if not is_empresa_allowed(request.user, justificativa.vinculo.empresa_id):
            return HttpResponseForbidden('Justificativa não pertence a uma empresa permitida para este usuário.')

        vinculo_id = justificativa.vinculo_id
        justificativa.delete()
        messages.success(request, '🗑️ Justificativa removida. A lacuna voltou para "Pendente".')
        return redirect('auditoria-vinculo-detail', vinculo_id=vinculo_id)
