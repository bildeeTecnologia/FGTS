"""
JAM atualizado de TODAS as competências (pagas ou não) por pessoa/empresa.

Usa o mesmo motor do relatório de competências (`LancamentoRelatorioView._compute_for`):
`aplicar_plano_economico_legacy` -> `calcular_jam_ate_pagamento` (JAM composto mês a mês).
Diferença: não filtra `pago=False` nem exige vínculo ativo na competência — olha todo o
histórico lançado. A mesma pessoa pode ter um cadastro de funcionário por empresa, então o
casamento é feito por CPF (exceto o CPF-placeholder usado em cadastros de teste/legado).
"""
import re
from collections import OrderedDict
from datetime import date
from decimal import Decimal

from funcionarios.models import Funcionario
from indices.services.indice_service import IndiceFGTSService
from lancamentos.models import Lancamento
from lancamentos.services.calculo import (
    aplicar_plano_economico_legacy,
    buscar_coef_jam,
    calcular_jam_ate_pagamento,
)

CPF_PLACEHOLDER = '12345678909'
CAMPOS_BUSCA = [('nome', 'Nome'), ('cpf', 'CPF'), ('pis', 'PIS')]
ZERO = Decimal('0.00')


def _digitos(valor):
    return re.sub(r'\D', '', valor or '')


def _formatar_cpf(d):
    return f'{d[:3]}.{d[3:6]}.{d[6:9]}-{d[9:]}' if len(d) == 11 else d


def localizar_funcionarios(campo, termo):
    """IDs de funcionários que casam com o termo (nome parcial, CPF ou PIS), expandidos por CPF."""
    termo = (termo or '').strip()
    if campo == 'cpf':
        d = _digitos(termo)
        qs = Funcionario.objects.filter(cpf__in={d, _formatar_cpf(d), termo}) if d else Funcionario.objects.none()
    elif campo == 'pis':
        d = _digitos(termo)
        qs = Funcionario.objects.filter(pis__contains=d) if d else Funcionario.objects.none()
    else:
        qs = Funcionario.objects.filter(nome__icontains=termo) if termo else Funcionario.objects.none()

    ids = set(qs.values_list('pk', flat=True))
    cpfs = set()
    for c in Funcionario.objects.filter(pk__in=ids).values_list('cpf', flat=True):
        d = _digitos(c)
        if d and d != CPF_PLACEHOLDER:
            cpfs.update({d, _formatar_cpf(d), c})
    if cpfs:
        ids |= set(Funcionario.objects.filter(cpf__in=cpfs).values_list('pk', flat=True))
    return ids


def _parse_competencia(s):
    s = (s or '').strip()
    try:
        if '/' in s:
            m, a = s.split('/')
            return date(int(a), int(m), 1)
        a, m = s.split('-')
        return date(int(a), int(m), 1)
    except Exception:
        return None


def data_atualizacao_padrao():
    """Mesmo padrão do relatório de competências: última data-base de índices ou hoje."""
    return IndiceFGTSService.obter_ultima_data_base() or date.today()


def contar_lancamentos(funcionario_ids=None, empresa=None, empresas_permitidas=None):
    return _queryset(funcionario_ids, empresa, empresas_permitidas).count()


def _queryset(funcionario_ids, empresa, empresas_permitidas):
    qs = Lancamento.objects.all()
    if empresas_permitidas is not None:
        qs = qs.filter(empresa_id__in=empresas_permitidas)
    if empresa is not None:
        qs = qs.filter(empresa=empresa)
    if funcionario_ids is not None:
        qs = qs.filter(funcionario_id__in=funcionario_ids)
    return qs


def calcular_jam_total(data_pagamento, funcionario_ids=None, empresa=None, empresas_permitidas=None):
    """Calcula o JAM de cada lançamento e consolida por (pessoa, empresa do vínculo).

    Args:
        data_pagamento: data de atualização (JAM composto até o mês dela).
        funcionario_ids: restringe a esses funcionários (None = sem restrição).
        empresa: restringe a uma empresa (None = todas).
        empresas_permitidas: ids de empresa liberados ao usuário (None = irrestrito).

    Returns:
        dict com `grupos` (lista, cada um com `linhas` analíticas), `totais` e `meses_sem_coef`.
    """
    qs = _queryset(funcionario_ids, empresa, empresas_permitidas).select_related(
        'empresa', 'vinculo', 'vinculo__empresa', 'funcionario',
    )

    coef_cache = {}

    def coef(comp):
        chave = comp.replace(day=1)
        if chave not in coef_cache:
            coef_cache[chave] = buscar_coef_jam(chave)
        return coef_cache[chave]

    grupos = OrderedDict()
    meses_sem_coef = set()
    ignorados = 0
    # Valores de FGTS se repetem muito na mesma competência (mesmo salário): evita refazer o composto.
    jam_cache = {}

    for l in qs:
        comp = _parse_competencia(l.competencia)
        if comp is None:
            ignorados += 1
            continue
        ajustado, *_ = aplicar_plano_economico_legacy(l.valor_fgts, comp)
        chave_jam = (ajustado, comp)
        if chave_jam not in jam_cache:
            jam_cache[chave_jam] = calcular_jam_ate_pagamento(
                valor_fgts=ajustado, competencia=comp, data_pagamento=data_pagamento, coef_lookup=coef,
            )
        jam, _det, sem_coef = jam_cache[chave_jam]
        meses_sem_coef.update(sem_coef)

        emp = l.vinculo.empresa if l.vinculo_id else l.empresa
        cpf = l.funcionario.cpf
        pessoa_key = _digitos(cpf) if _digitos(cpf) not in ('', CPF_PLACEHOLDER) else f'func{l.funcionario_id}'
        chave = (pessoa_key, emp.pk)
        g = grupos.get(chave)
        if g is None:
            g = grupos[chave] = {
                'nome': l.funcionario.nome, 'cpf': cpf, 'pis': l.funcionario.pis,
                'empresa': emp.nome, 'cnpj': emp.cnpj, 'qtd': 0,
                'fgts': ZERO, 'jam': ZERO, 'jam_pago': ZERO, 'jam_aberto': ZERO, 'total': ZERO,
                'linhas': [],
            }
        total = (ajustado + jam).quantize(ZERO)
        g['qtd'] += 1
        g['fgts'] += l.valor_fgts
        g['jam'] += jam
        g['total'] += total
        g['jam_pago' if l.pago else 'jam_aberto'] += jam
        g['linhas'].append({
            'comp': comp,
            'parcela_13': l.parcela_13,
            'matricula': (l.vinculo.matricula if l.vinculo_id else '') or '',
            'base_fgts': l.base_fgts,
            'valor_fgts': l.valor_fgts,
            'pago': l.pago,
            'data_pagto': l.data_pagto,
            'valor_pago': l.valor_pago,
            'jam': jam,
            'total': total,
            'sem_coef': len(sem_coef),
        })

    lista = sorted(grupos.values(), key=lambda g: (g['nome'], g['empresa']))
    for g in lista:
        g['linhas'].sort(key=lambda r: (r['comp'], r['parcela_13'] or 0))

    totais = {
        'qtd': sum(g['qtd'] for g in lista),
        'fgts': sum((g['fgts'] for g in lista), ZERO),
        'jam_pago': sum((g['jam_pago'] for g in lista), ZERO),
        'jam_aberto': sum((g['jam_aberto'] for g in lista), ZERO),
        'jam': sum((g['jam'] for g in lista), ZERO),
        'total': sum((g['total'] for g in lista), ZERO),
        'pessoas': len({(g['cpf'] or g['nome']) for g in lista}),
    }
    return {
        'grupos': lista,
        'totais': totais,
        'meses_sem_coef': sorted(meses_sem_coef),
        'ignorados': ignorados,
        'data_pagamento': data_pagamento,
    }
