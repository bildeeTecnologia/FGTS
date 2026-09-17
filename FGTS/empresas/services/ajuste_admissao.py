"""
Sugestão/correção de data_admissao de vínculos cuja data cadastrada é posterior à
competência do lançamento mais antigo já registrado (comum em transferências legadas
onde a data de admissão original foi mantida por engano).
"""
import re
from datetime import date

from django.db import transaction

from empresas.models_grupo import FuncionarioVinculo
from lancamentos.models import Lancamento

_COMP_RE = re.compile(r'^(\d{2})/(\d{4})$')


def _competencia_to_date(comp_str):
    if not comp_str:
        return None
    m = _COMP_RE.match(comp_str.strip())
    if not m:
        return None
    mes, ano = int(m.group(1)), int(m.group(2))
    if not (1 <= mes <= 12):
        return None
    return date(ano, mes, 1)


def sugerir_ajustes_admissao(empresa=None):
    """Lista vínculos cuja data_admissao é posterior à competência mais antiga lançada.

    Retorna uma lista de dicts: vinculo, data_atual, data_sugerida, aplicavel (bool),
    motivo_bloqueio (preenchido quando aplicavel=False, ex.: sobreposição com vínculo anterior).
    """
    vinculos_qs = FuncionarioVinculo.objects.select_related('funcionario', 'empresa').order_by(
        'funcionario__nome', 'data_admissao'
    )
    if empresa is not None:
        vinculos_qs = vinculos_qs.filter(empresa=empresa)
    vinculos = list(vinculos_qs)
    vinculo_ids = [v.pk for v in vinculos]

    primeira_competencia_por_vinculo = {}
    for vinculo_id, comp_str in Lancamento.objects.filter(
        vinculo_id__in=vinculo_ids
    ).values_list('vinculo_id', 'competencia'):
        comp_date = _competencia_to_date(comp_str)
        if comp_date is None:
            continue
        atual = primeira_competencia_por_vinculo.get(vinculo_id)
        if atual is None or comp_date < atual:
            primeira_competencia_por_vinculo[vinculo_id] = comp_date

    sugestoes = []
    for vinculo in vinculos:
        primeira_competencia = primeira_competencia_por_vinculo.get(vinculo.pk)
        if primeira_competencia is None:
            continue

        data_admissao_atual = vinculo.data_admissao.replace(day=1)
        if primeira_competencia >= data_admissao_atual:
            continue

        vinculo_anterior = FuncionarioVinculo.objects.filter(
            funcionario_id=vinculo.funcionario_id,
            empresa_id=vinculo.empresa_id,
            data_admissao__lt=vinculo.data_admissao,
        ).order_by('-data_admissao').first()

        aplicavel = True
        motivo_bloqueio = ''
        if vinculo_anterior and vinculo_anterior.data_demissao and vinculo_anterior.data_demissao >= primeira_competencia:
            aplicavel = False
            motivo_bloqueio = (
                f'Sobreporia o vínculo anterior #{vinculo_anterior.pk} '
                f'(encerrado em {vinculo_anterior.data_demissao.strftime("%d/%m/%Y")}).'
            )

        sugestoes.append({
            'vinculo': vinculo,
            'data_atual': vinculo.data_admissao,
            'data_sugerida': primeira_competencia,
            'aplicavel': aplicavel,
            'motivo_bloqueio': motivo_bloqueio,
        })

    return sugestoes


def aplicar_ajustes_admissao(vinculo_ids):
    """Aplica a data_admissao sugerida para os vínculos informados (ignora não aplicáveis).

    Retorna a quantidade de vínculos efetivamente atualizados.
    """
    vinculo_ids = set(vinculo_ids)
    sugestoes_por_vinculo = {
        s['vinculo'].pk: s for s in sugerir_ajustes_admissao() if s['aplicavel']
    }

    aplicados = 0
    with transaction.atomic():
        for vinculo_id in vinculo_ids:
            sugestao = sugestoes_por_vinculo.get(vinculo_id)
            if not sugestao:
                continue
            vinculo = sugestao['vinculo']
            vinculo.data_admissao = sugestao['data_sugerida']
            vinculo.save(update_fields=['data_admissao'])
            aplicados += 1
    return aplicados
