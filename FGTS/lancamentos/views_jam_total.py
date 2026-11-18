"""
Tela "JAM Total por Pessoa": JAM atualizado de todas as competências (pagas ou não),
com consulta por nome, CPF, PIS, empresa ou todas, e exportação XLSX.
"""
from datetime import date

from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator
from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404, render
from django.views import View

from empresas.models import Empresa
from fgtsweb.mixins import get_allowed_empresa_ids, is_empresa_allowed

from .services.jam_total import (
    CAMPOS_BUSCA, contar_lancamentos, calcular_jam_total, data_atualizacao_padrao, localizar_funcionarios,
)
from .services.jam_total_export import gerar_xlsx_jam_total

# Teto de segurança (gunicorn: timeout 120s). A base inteira hoje tem ~28 mil lançamentos (~20s).
MAX_LANCAMENTOS = 60000


def _empresas_visiveis(user):
    allowed = get_allowed_empresa_ids(user)
    if allowed is None:
        return Empresa.objects.all().order_by('nome'), None
    return Empresa.objects.filter(codigo__in=allowed).order_by('nome'), allowed


def _executar_consulta(request):
    """Lê os filtros do GET e calcula. Retorna (resultado|None, erro|None, filtros)."""
    empresas, allowed = _empresas_visiveis(request.user)
    campo = request.GET.get('campo', 'nome')
    if campo not in dict(CAMPOS_BUSCA):
        campo = 'nome'
    termo = request.GET.get('q', '').strip()
    empresa_id = request.GET.get('empresa', '').strip()
    data_raw = request.GET.get('data', '').strip()

    filtros = {
        'campo': campo, 'q': termo, 'empresa_id': empresa_id,
        'data': data_raw, 'empresa': None,
    }

    try:
        data_pagamento = date.fromisoformat(data_raw) if data_raw else data_atualizacao_padrao()
    except ValueError:
        return None, 'Data de atualização inválida.', filtros
    filtros['data'] = data_pagamento.isoformat()
    filtros['data_pagamento'] = data_pagamento

    empresa = None
    if empresa_id:
        empresa = get_object_or_404(Empresa, pk=empresa_id)
        if not is_empresa_allowed(request.user, empresa.codigo):
            return None, 'Empresa não permitida para este usuário.', filtros
        filtros['empresa'] = empresa

    funcionario_ids = None
    if termo:
        funcionario_ids = localizar_funcionarios(campo, termo)
        if not funcionario_ids:
            return None, f'Nenhum funcionário encontrado para "{termo}" ({dict(CAMPOS_BUSCA)[campo]}).', filtros

    total = contar_lancamentos(funcionario_ids, empresa, allowed)
    if total > MAX_LANCAMENTOS:
        return None, f'A consulta abrange {total} lançamentos (limite {MAX_LANCAMENTOS}). Refine por empresa ou pessoa.', filtros

    resultado = calcular_jam_total(data_pagamento, funcionario_ids, empresa, allowed)
    return resultado, None, filtros


def _descricao_filtros(filtros):
    partes = [f'Empresa: {filtros["empresa"].nome if filtros["empresa"] else "todas"}']
    if filtros['q']:
        partes.append(f'{dict(CAMPOS_BUSCA)[filtros["campo"]]}: {filtros["q"]}')
    else:
        partes.append('Pessoas: todas')
    return ' | '.join(partes)


class JamTotalPessoaView(LoginRequiredMixin, View):
    template_name = 'lancamentos/jam_total_pessoa.html'

    def get(self, request):
        empresas, _ = _empresas_visiveis(request.user)
        contexto = {
            'empresas': empresas,
            'campos_busca': CAMPOS_BUSCA,
            'consultou': request.GET.get('consultar') == '1',
            'filtros': {
                'campo': request.GET.get('campo', 'nome'), 'q': request.GET.get('q', '').strip(),
                'empresa_id': request.GET.get('empresa', '').strip(),
                'data': request.GET.get('data', '').strip() or data_atualizacao_padrao().isoformat(),
            },
            'resultado': None, 'page_obj': None, 'erro': None,
        }
        if contexto['consultou']:
            resultado, erro, filtros = _executar_consulta(request)
            contexto['erro'] = erro
            contexto['filtros'] = filtros
            if resultado:
                contexto['resultado'] = resultado
                contexto['page_obj'] = Paginator(resultado['grupos'], 25).get_page(request.GET.get('page', 1))
        return render(request, self.template_name, contexto)


class JamTotalPessoaExportXlsxView(LoginRequiredMixin, View):
    """Exporta o mesmo resultado da tela (consolidado + analítico) em XLSX."""

    def get(self, request):
        resultado, erro, filtros = _executar_consulta(request)
        if erro:
            status = 403 if 'não permitida' in erro else 400
            return (HttpResponseForbidden if status == 403 else HttpResponse)(erro, status=status)
        if not resultado['grupos']:
            return HttpResponse('Nenhum lançamento encontrado para exportar.', status=400)

        xlsx_bytes = gerar_xlsx_jam_total(resultado, _descricao_filtros(filtros))
        response = HttpResponse(
            xlsx_bytes,
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        )
        response['Content-Disposition'] = (
            f'attachment; filename="jam_total_{filtros["data_pagamento"].strftime("%Y%m%d")}.xlsx"'
        )
        return response
