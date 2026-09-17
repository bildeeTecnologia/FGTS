"""
Auditoria de lançamentos esperados x realizados por vínculo.

Regras de negócio detalhadas em:
empresas/templates/ajuda/manual.html#auditoria-lancamentos
(porta em Python das mesmas regras validadas em
scripts/auditoria_lancamentos_2026_09_10.sql)
"""
import re
from datetime import date

from dateutil.relativedelta import relativedelta
from django.core.cache import cache

from lancamentos.models import Lancamento
from lancamentos.models_lacuna import LacunaJustificativa

_COMP_BARRA_RE = re.compile(r'^(\d{2})/(\d{4})$')
_COMP_ISO_RE = re.compile(r'^(\d{4})-(\d{2})$')

# ~40 dias: apenas um teto de segurança. A invalidação de verdade é feita por signals
# (lancamentos/signals_auditoria.py) sempre que algo que afeta o resultado muda.
CACHE_TTL_SEGUNDOS = 60 * 60 * 24 * 40


def _cache_key_resumo(vinculo_id, hoje):
    return f'auditoria_vinculo_resumo:{vinculo_id}:{hoje.strftime("%Y%m")}'


def _parse_competencia(competencia_str):
    """Aceita 'MM/YYYY' ou 'YYYY-MM'; retorna (mes, ano) ou None se ilegível."""
    if not competencia_str:
        return None
    s = competencia_str.strip()
    m = _COMP_BARRA_RE.match(s)
    if m:
        mes, ano = int(m.group(1)), int(m.group(2))
        return (mes, ano) if 1 <= mes <= 12 else None
    m = _COMP_ISO_RE.match(s)
    if m:
        ano, mes = int(m.group(1)), int(m.group(2))
        return (mes, ano) if 1 <= mes <= 12 else None
    return None


def data_minima_historico_contratado(empresa, hoje=None):
    """Primeiro mês de histórico aceito pelo plano contratado da empresa (None = sem limite).

    Mesma regra de `Lancamento.clean()` (lancamentos/models.py): meses anteriores a este
    limite não podem ter lançamento criado, pois o plano contratado não cobre esse histórico.
    """
    hoje = hoje or date.today()
    try:
        max_history_months = empresa.billing_customer.get_effective_max_history_months()
    except Exception:
        return None
    if not max_history_months or max_history_months <= 0:
        return None
    current_month = hoje.replace(day=1)
    return current_month - relativedelta(months=max_history_months - 1)


def gerar_competencias_esperadas(vinculo, hoje=None):
    """Lista ordenada de competências esperadas para o vínculo (normais + 13º)."""
    hoje = hoje or date.today()
    mes_admissao = vinculo.data_admissao.replace(day=1)
    if vinculo.data_demissao:
        mes_cutoff = vinculo.data_demissao.replace(day=1)
    else:
        mes_cutoff = hoje.replace(day=1) - relativedelta(months=1)

    if mes_cutoff < mes_admissao:
        return []

    esperadas = []
    cursor = mes_admissao
    while cursor <= mes_cutoff:
        esperadas.append({
            'competencia': cursor.strftime('%m/%Y'),
            'parcela_13': None,
            'ordem': (cursor.year, cursor.month, 0),
        })
        cursor += relativedelta(months=1)

    empresa = vinculo.empresa
    funcionario = vinculo.funcionario
    paga_13_aniversario = getattr(empresa, 'paga_13_aniversario', False)
    data_nascimento = getattr(funcionario, 'data_nascimento', None)

    for ano in range(mes_admissao.year, mes_cutoff.year + 1):
        mes_parcela1 = 11
        if paga_13_aniversario and data_nascimento:
            mes_parcela1 = data_nascimento.month
        data_parcela1 = date(ano, mes_parcela1, 1)
        if mes_admissao <= data_parcela1 <= mes_cutoff:
            esperadas.append({
                'competencia': data_parcela1.strftime('%m/%Y'),
                'parcela_13': 1,
                'ordem': (ano, mes_parcela1, 1),
            })

        data_parcela2 = date(ano, 12, 1)
        if mes_admissao <= data_parcela2 <= mes_cutoff:
            esperadas.append({
                'competencia': data_parcela2.strftime('%m/%Y'),
                'parcela_13': 2,
                'ordem': (ano, 12, 2),
            })

    esperadas.sort(key=lambda item: item['ordem'])
    for item in esperadas:
        del item['ordem']
    return esperadas


def auditar_vinculo(vinculo, hoje=None, incluir_itens=True):
    """Retorna o comparativo esperado x realizado x justificado para um vínculo."""
    esperadas = gerar_competencias_esperadas(vinculo, hoje=hoje)
    data_minima = data_minima_historico_contratado(vinculo.empresa, hoje=hoje)

    # 13º: casamento por ANO + Nº DA PARCELA, ignorando o mês do lançamento real —
    # historicamente parcelas do 13º podem ter sido pagas fora de nov/dez/aniversário.
    realizados_normais = {}
    realizados_13 = {}
    for lanc in Lancamento.objects.filter(vinculo=vinculo).only('id', 'competencia', 'parcela_13', 'pago'):
        chave = _parse_competencia(lanc.competencia)
        if chave is None:
            continue
        mes, ano = chave
        if lanc.parcela_13:
            realizados_13[(ano, lanc.parcela_13)] = lanc
        else:
            realizados_normais[(ano, mes)] = lanc

    justificativas = {}
    for just in LacunaJustificativa.objects.filter(vinculo=vinculo).select_related('usuario'):
        chave = _parse_competencia(just.competencia)
        if chave is None:
            continue
        mes, ano = chave
        justificativas[(ano, mes, just.parcela_13)] = just

    itens = []
    qtd_realizados = 0
    qtd_justificados = 0
    qtd_pendentes = 0
    qtd_fora_do_plano = 0

    for esperado in esperadas:
        mes, ano = _parse_competencia(esperado['competencia'])
        if esperado['parcela_13']:
            lancamento = realizados_13.get((ano, esperado['parcela_13']))
        else:
            lancamento = realizados_normais.get((ano, mes))
        justificativa = justificativas.get((ano, mes, esperado['parcela_13']))

        if lancamento:
            status = 'ok'
            qtd_realizados += 1
        elif justificativa:
            status = 'justificado'
            qtd_justificados += 1
        elif data_minima and date(ano, mes, 1) < data_minima:
            # Competência fora do histórico aceito pelo plano contratado: não é possível
            # lançar (bloqueado por Lancamento.clean()) nem faz sentido cobrar justificativa.
            status = 'fora_do_plano'
            qtd_fora_do_plano += 1
        else:
            status = 'pendente'
            qtd_pendentes += 1

        if incluir_itens:
            itens.append({
                'competencia': esperado['competencia'],
                'parcela_13': esperado['parcela_13'],
                'status': status,
                'lancamento': lancamento,
                'justificativa': justificativa,
            })

    return {
        'vinculo': vinculo,
        'itens': itens,
        'qtd_esperados': len(esperadas),
        'qtd_realizados': qtd_realizados,
        'qtd_justificados': qtd_justificados,
        'qtd_pendentes': qtd_pendentes,
        'qtd_fora_do_plano': qtd_fora_do_plano,
        'data_minima_historico': data_minima,
    }


def resumir_auditoria_vinculo(vinculo, hoje=None):
    """Versão leve de `auditar_vinculo` (sem a lista item a item), com cache.

    O resultado só muda quando: um lançamento/justificativa do vínculo é criado,
    editado ou removido; o próprio vínculo, o funcionário ou a empresa são editados;
    ou o plano/billing da empresa muda. Todos esses pontos invalidam o cache via
    signals em `lancamentos/signals_auditoria.py`. A chave também roda por mês
    (AAAAMM) para acompanhar a virada do "mês atual" usada em `gerar_competencias_esperadas`.
    """
    hoje = hoje or date.today()
    chave = _cache_key_resumo(vinculo.pk, hoje)
    resumo = cache.get(chave)
    if resumo is not None:
        return resumo
    resumo = auditar_vinculo(vinculo, hoje=hoje, incluir_itens=False)
    cache.set(chave, resumo, CACHE_TTL_SEGUNDOS)
    return resumo


def invalidar_cache_vinculo(vinculo_id, hoje=None):
    """Limpa o cache de auditoria de um único vínculo (chamado pelos signals)."""
    cache.delete(_cache_key_resumo(vinculo_id, hoje or date.today()))


def invalidar_cache_vinculos_funcionario(funcionario_id):
    """Limpa o cache de todos os vínculos de um funcionário (ex.: data_nascimento mudou)."""
    from empresas.models_grupo import FuncionarioVinculo
    for vinculo_id in FuncionarioVinculo.objects.filter(funcionario_id=funcionario_id).values_list('pk', flat=True):
        invalidar_cache_vinculo(vinculo_id)


def invalidar_cache_vinculos_empresa(empresa_id):
    """Limpa o cache de todos os vínculos de uma empresa (ex.: plano/paga_13_aniversario mudou)."""
    from empresas.models_grupo import FuncionarioVinculo
    for vinculo_id in FuncionarioVinculo.objects.filter(empresa_id=empresa_id).values_list('pk', flat=True):
        invalidar_cache_vinculo(vinculo_id)


def invalidar_cache_tudo():
    """Limpa o cache de auditoria de TODOS os vínculos.

    Usado pelo botão manual "Recalcular auditoria" no Django Admin — necessário porque
    edições feitas direto no banco (fora do Django/Supabase SQL Editor) não passam pelos
    signals de `lancamentos/signals_auditoria.py` e por isso não invalidam o cache sozinhas.
    Retorna a quantidade de vínculos processados.
    """
    from empresas.models_grupo import FuncionarioVinculo
    ids = list(FuncionarioVinculo.objects.values_list('pk', flat=True))
    for vinculo_id in ids:
        invalidar_cache_vinculo(vinculo_id)
    return len(ids)
