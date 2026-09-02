from datetime import date, timedelta, datetime
from dateutil.relativedelta import relativedelta
from decimal import Decimal, ROUND_HALF_UP
from typing import Iterable, Tuple

from configuracoes.models import Configuracao


def get_config_numeric(key: str, default: Decimal) -> Decimal:
    from django.core.cache import cache
    cache_key = f'config_{key}'
    cached = cache.get(cache_key)
    if cached is not None:
        return Decimal(str(cached))
    try:
        cfg = Configuracao.objects.get(chave=key)
        val = Decimal(str(cfg.valor))
    except Exception:
        val = default
    cache.set(cache_key, str(val), timeout=3600)
    return val


def get_config_str(key: str, default: str) -> str:
    from django.core.cache import cache
    cache_key = f'config_{key}'
    cached = cache.get(cache_key)
    if cached is not None:
        return str(cached)
    try:
        cfg = Configuracao.objects.get(chave=key)
        val = str(cfg.valor)
    except Exception:
        val = default
    cache.set(cache_key, val, timeout=3600)
    return val


def acumulado_indices(indices: Iterable[Tuple[date, Decimal]], competencia: date, pagamento: date) -> Decimal:
    """Busca o índice correspondente à combinação de competência + data de pagamento.
    O índice deve estar entre a data da competência e a data de pagamento.
    Se houver múltiplos, usa o mais recente (maior índice).
    Retorna o índice ou 1.0 se não encontrar (sem correção).
    """
    indices_list = list(indices)
    # Ordena por data DESC para pegar o maior índice disponível
    indices_list.sort(key=lambda x: x[0], reverse=True)
    
    for d, v in indices_list:
        # Busca índice que está entre a competência e a data de pagamento
        if competencia <= d <= pagamento:
            return v
    
    # Se não encontrar no intervalo, retorna o mais próximo da data de pagamento
    for d, v in indices_list:
        if d <= pagamento:
            return v
    
    # Se não encontrar nada, retorna 1.0 (sem correção)
    return Decimal('1.0')


def aplicar_jam(valor_fgts: Decimal, jam_coef: Decimal) -> Decimal:
    return (valor_fgts * jam_coef).quantize(Decimal('0.01'))


def _format_competencia_variants(comp_date: date) -> list[str]:
    """Retorna representações compatíveis de competência.

    Suporta MM/YYYY (legado) e YYYY-MM (dados Supabase).
    """
    return [comp_date.strftime('%m/%Y'), comp_date.strftime('%Y-%m')]


def buscar_coef_jam(competencia: date) -> Decimal | None:
    """Busca o coeficiente JAM para a competência (com cache de 24h).

    - Tenta formatos MM/YYYY e YYYY-MM.
    - Se houver múltiplos registros, usa o mais recente por data_pagamento.
    - Retorna None se não encontrar.
    """
    from django.core.cache import cache
    from coefjam.models import CoefJam

    cache_key = f'coef_jam_{competencia.strftime("%Y%m")}'
    cached = cache.get(cache_key)
    if cached is not None:
        return None if cached == '__none__' else Decimal(str(cached))

    comp_formats = _format_competencia_variants(competencia)
    coef = (
        CoefJam.objects
        .filter(competencia__in=comp_formats)
        .order_by('-data_pagamento')
        .first()
    )
    valor = Decimal(str(coef.valor)) if coef else None
    cache.set(cache_key, str(valor) if valor is not None else '__none__', timeout=86400)
    return valor


def calcular_jam_ate_pagamento(
    valor_fgts: Decimal,
    competencia: date,
    data_pagamento: date,
    coef_lookup=None,
) -> tuple[Decimal, list[tuple[date, Decimal, Decimal]], list[date]]:
    """Calcula JAM composto do mês seguinte à competência até o mês do pagamento.

    - Não aplica JAM no mês da competência.
    - Aplica coeficientes CoefJam mês a mês; se faltar coeficiente, assume 0 para o mês.
    - Arredondamento monetário: 2 casas, ROUND_HALF_UP.

    Returns:
        jam_total: soma dos juros do período.
        detalhes: lista de (competência, jam_mes, saldo_final_mes).
        meses_sem_coef: competências sem coeficiente cadastrado.
    """
    if valor_fgts is None:
        return Decimal('0.00'), [], []

    saldo = valor_fgts.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    jam_total = Decimal('0.00')
    detalhes: list[tuple[date, Decimal, Decimal]] = []
    meses_sem_coef: list[date] = []

    comp_cursor = competencia.replace(day=1) + relativedelta(months=1)
    pagamento_comp = data_pagamento.replace(day=1)

    while comp_cursor <= pagamento_comp:
        coef = coef_lookup(comp_cursor) if coef_lookup else buscar_coef_jam(comp_cursor)
        if coef is None:
            detalhes.append((comp_cursor, Decimal('0.00'), saldo))
            meses_sem_coef.append(comp_cursor)
            comp_cursor += relativedelta(months=1)
            continue

        jam_mes = (saldo * coef).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        jam_total += jam_mes
        saldo = (saldo + jam_mes).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        detalhes.append((comp_cursor, jam_mes, saldo))
        comp_cursor += relativedelta(months=1)

    return jam_total, detalhes, meses_sem_coef


def aplicar_plano_economico_legacy(valor_fgts: Decimal, competencia: date) -> tuple[Decimal, Decimal, Decimal, Decimal]:
    """Replica a lógica do VB6 (mdlCalculo.vb) para planos econômicos.

    Passos do legado:
    1) Multiplica por fatores de mar-jun/1994.
    2) Divide por conversões monetárias conforme faixa de competência.

    Args:
        valor_fgts: FGTS do mês (já 8% da base)
        competencia: data da competência (primeiro dia do mês)

    Returns:
        valor_ajustado, multiplicador_aplicado, divisor_aplicado, fator_liquido
    """
    ano = competencia.year
    mes = competencia.month

    multiplicadores = {
        (1994, 3): Decimal('948.93'),
        (1994, 4): Decimal('1389.94'),
        (1994, 5): Decimal('1946.13'),
        (1994, 6): Decimal('2750'),
    }

    multiplicador = multiplicadores.get((ano, mes), Decimal('1'))
    ajustado = valor_fgts * multiplicador

    divisor = Decimal('1')
    if 1967 < ano < 1986:
        divisor = Decimal('2750000000000')
    elif 1985 < ano < 1989:
        divisor = Decimal('2750000000')
    elif ano == 1988 and mes == 12:
        divisor = Decimal('2750000')
    elif 1988 < ano < 1993:
        divisor = Decimal('2750000')
    elif ano == 1993 and mes < 8:
        divisor = Decimal('2750000')
    elif ano == 1993 and mes > 7:
        divisor = Decimal('2750')
    elif ano == 1994 and mes < 7:
        divisor = Decimal('2750')

    if divisor != Decimal('1'):
        ajustado = ajustado / divisor

    fator_liquido = (multiplicador / divisor) if divisor != Decimal('0') else Decimal('1')

    return ajustado, multiplicador, divisor, fator_liquido


def calcular_jam_composto(acumulado_anterior: Decimal, valor_fgts: Decimal, jam_coef: Decimal) -> tuple[Decimal, Decimal]:
    """Replica o comportamento legado do JAM (cálculo composto).

    - Se não houver jam_coef, retorna jam=0 e acumula apenas o FGTS do mês.
    - Caso haja jam_coef, aplica sobre o acumulado anterior e soma o FGTS do mês.
    Retorna (valor_jam, novo_acumulado).
    """
    jam_coef = jam_coef or Decimal('0')
    if acumulado_anterior is None:
        # Primeiro mês do funcionário: JAM zerado, inicia o acumulador
        return Decimal('0.00'), valor_fgts
    jam_val = (acumulado_anterior * jam_coef).quantize(Decimal('0.01'))
    novo_acumulado = acumulado_anterior + jam_val + valor_fgts
    return jam_val, novo_acumulado


def calcular_jam_periodo(valor_fgts: Decimal, competencia_start: date, data_pagamento: date, data_admissao: date) -> Decimal:
    """Calcula JAM para UMA competência específica.
    
    IMPORTANTE: Esta função calcula o JAM de forma SIMPLIFICADA para uma única competência.
    O cálculo correto do JAM requer o acumulado de TODAS as competências anteriores,
    o que deve ser feito no nível da view que processa múltiplas competências.
    
    Regra oficial: 
    - A competência de admissão (mês de admissão) = JAM zerado (nenhum acúmulo anterior)
    - Competências posteriores à admissão = JAM com acúmulo desde a admissão
    
    Fórmula JAM (por competência):
    - JAM = Acumulado_Anterior × Coeficiente_JAM_do_Mês_Anterior
    - Acumulado_Novo = Acumulado_Anterior + JAM + Valor_FGTS_do_Mês
    
    Args:
        valor_fgts: Valor FGTS da competência
        competencia_start: Competência específica (primeiro dia)
        data_pagamento: Data final (data de pagamento)
        data_admissao: Data de admissão do funcionário
    
    Returns:
        JAM calculado para essa competência (SIMPLIFICADO - retorna 0 por padrão)
    """
    from coefjam.models import CoefJam
    
    # Se a competência é a de admissão, retorna JAM zerado
    competencia_admissao = date(data_admissao.year, data_admissao.month, 1)
    if competencia_start == competencia_admissao:
        return Decimal('0.00')
    
    # Se a competência é anterior à admissão, não há FGTS (retorna 0)
    if competencia_start < competencia_admissao:
        return Decimal('0.00')
    
    # IMPORTANTE: O cálculo correto do JAM requer estado acumulado de todas as competências
    # anteriores. Como esta função é chamada de forma isolada, retornamos 0 por padrão.
    # O cálculo correto deve ser feito na view RelatorioCompetenciaView que processa
    # todas as competências em ordem cronológica.
    
    return Decimal('0.00')


def calcular_fgts_atualizado(valor_fgts: Decimal,
                              competencia: date,
                              pagamento: date,
                              indice: Decimal,
                              jam_coef: Decimal,
                              valor_jam_override: Decimal | None = None,
                              aplicar_plano_economico: bool = True,
                              fator_plano_info: tuple[Decimal, Decimal, Decimal] | None = None,
                              valor_fgts_base: Decimal | None = None,
                              aliquota: Decimal = Decimal('0.08'),
                              **kwargs) -> dict:
    """Cálculo FGTS simplificado:
    O índice representa o fator aplicado sobre a base FGTS para obter o depósito correto.
    O índice da tabela foi construído para alíquota de 8% (CLT). Para outras alíquotas,
    o índice é reescalado: indice_efetivo = indice_tabela × (aliquota / 0.08).

    - Valor Depósito FGTS = Base FGTS × Índice Efetivo
    - Correção (valor_corrigido) = Valor Depósito FGTS − Valor FGTS do mês
    - JAM = Calculado separadamente
    - Total = Correção + JAM
    """
    fator_mult = Decimal('1')
    fator_div = Decimal('1')
    fator_liquido = Decimal('1')
    valor_fgts_original = valor_fgts
    base_para_correcao = valor_fgts_base if valor_fgts_base is not None else valor_fgts
    if aplicar_plano_economico:
        valor_fgts, fator_mult, fator_div, fator_liquido = aplicar_plano_economico_legacy(valor_fgts, competencia)
    elif fator_plano_info:
        fator_mult, fator_div, fator_liquido = fator_plano_info

    # Garantir casas decimais de moeda após ajustes
    valor_fgts = valor_fgts.quantize(Decimal('0.01'))

    # Usa o índice específico para competência + data_pagamento
    # Se não houver índice, usa 1.0 (sem correção)
    indice_final = indice if indice is not None else Decimal('1.0')

    # Escala o índice pela alíquota real (o índice da tabela foi construído para 8%)
    indice_efetivo = (indice_final * aliquota / Decimal('0.08')).quantize(Decimal('0.000000001'))

    # Depósito correto para a competência (Base × Índice Efetivo)
    valor_deposito_fgts = (base_para_correcao * indice_efetivo).quantize(Decimal('0.01'))

    # Correção = valor que faltou para atingir o depósito correto
    valor_corrigido = (valor_deposito_fgts - valor_fgts).quantize(Decimal('0.01'))

    # Se vier um JAM pré-calculado (modo composto), usa-o; caso contrário, calcula simples
    if valor_jam_override is not None:
        valor_jam = valor_jam_override.quantize(Decimal('0.01'))
    else:
        valor_jam = aplicar_jam(valor_fgts, jam_coef)
    
    # Total = Depósito corrigido + JAM
    total = (valor_deposito_fgts + valor_jam).quantize(Decimal('0.01'))
    
    return {
        'indice': indice_final,
        'valor_fgts': valor_fgts,
        'valor_fgts_base': valor_fgts_base if valor_fgts_base is not None else valor_fgts_original,
        'valor_deposito_fgts': valor_deposito_fgts,
        'fator_plano_economico_multiplicador': fator_mult,
        'fator_plano_economico_divisor': fator_div,
        'fator_plano_economico': fator_liquido,
        'valor_corrigido': valor_corrigido,  # Correção (Depósito - FGTS do mês)
        'valor_jam': valor_jam,
        'total': total,  # Depósito corrigido + JAM
    }


def gerar_memoria_calculo(funcionario_nome: str, funcionario_cpf: str, data_admissao: date,
                         valor_fgts: Decimal, competencia_str: str, data_pagamento: date,
                         indice: Decimal, valor_jam: Decimal, valor_corrigido: Decimal,
                         total: Decimal, data_admissao_mes: str,
                         salario_colaborador: Decimal | None = None,
                         valor_deposito_fgts: Decimal | None = None,
                         fator_plano_economico: Decimal = Decimal('1'),
                         fator_plano_mult: Decimal = Decimal('1'),
                         fator_plano_div: Decimal = Decimal('1'),
                         aliquota: Decimal = Decimal('0.08')) -> str:
    """Gera memória de cálculo detalhada em formato texto.
    
    Args:
        funcionario_nome: Nome do funcionário
        funcionario_cpf: CPF do funcionário
        data_admissao: Data completa de admissão
        valor_fgts: Valor FGTS do mês
        competencia_str: Competência analisada (MM/YYYY)
        data_pagamento: Data de pagamento
        indice: Índice FGTS utilizado
        valor_jam: Valor JAM calculado
        valor_corrigido: Valor corrigido (FGTS × Índice)
        total: Total final
        data_admissao_mes: Competência de admissão (MM/YYYY)
    
    Returns:
        String com a memória de cálculo formatada
    """
    
    memoria = []
    memoria.append("=" * 80)
    memoria.append("MEMÓRIA DE CÁLCULO - FGTS COM JAM")
    memoria.append("=" * 80)
    memoria.append("")
    
    # Seção 1: Identificação
    memoria.append("1. IDENTIFICAÇÃO")
    memoria.append("-" * 80)
    memoria.append(f"   Funcionário: {funcionario_nome}")
    memoria.append(f"   CPF: {funcionario_cpf}")
    memoria.append(f"   Data de Admissão: {data_admissao.strftime('%d/%m/%Y')} (Competência: {data_admissao_mes})")
    memoria.append(f"   Competência Analisada: {competencia_str}")
    memoria.append(f"   Data de Pagamento: {data_pagamento.strftime('%d/%m/%Y')}")
    memoria.append("")
    
    # Seção 2: Dados Base
    memoria.append("2. DADOS BASE")
    memoria.append("-" * 80)
    if salario_colaborador is not None:
        memoria.append(f"   Base FGTS: R$ {salario_colaborador:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
        pct_display = int(aliquota * 100) if aliquota * 100 == int(aliquota * 100) else f"{aliquota * 100:.2f}".rstrip('0').rstrip('.')
        fgts_teorico = (salario_colaborador * aliquota).quantize(Decimal('0.01'))
        memoria.append(f"   FGTS do mês ({pct_display}% sobre salário): R$ {fgts_teorico:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
    memoria.append(f"   Valor FGTS (após ajustes): R$ {valor_fgts:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
    if fator_plano_economico and fator_plano_economico != Decimal('1'):
        fgts_sem_fator = (valor_fgts / fator_plano_economico).quantize(Decimal('0.01'))
        memoria.append(f"   Ajuste plano econômico legado:")
        memoria.append(f"     - Multiplicador: ×{fator_plano_mult}")
        memoria.append(f"     - Divisor: ÷{fator_plano_div}")
        memoria.append(f"     - Fator líquido: ×{fator_plano_economico}")
        memoria.append(f"   FGTS antes do ajuste: R$ {fgts_sem_fator:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
    memoria.append("")
    
    # Seção 3: Cálculo do FGTS Corrigido
    memoria.append("3. CÁLCULO DO FGTS CORRIGIDO")
    memoria.append("-" * 80)
    base_correcao = salario_colaborador if salario_colaborador is not None else valor_fgts
    # Índice efetivo = índice tabela × (alíquota / 0.08); para CLT (8%) permanece igual
    indice_efetivo = (indice * aliquota / Decimal('0.08')).quantize(Decimal('0.000000001'))
    deposito_fgts_display = valor_deposito_fgts if valor_deposito_fgts is not None else (base_correcao * indice_efetivo).quantize(Decimal('0.01'))
    pct_display_sec3 = int(aliquota * 100) if aliquota * 100 == int(aliquota * 100) else f"{aliquota * 100:.2f}".rstrip('0').rstrip('.')
    memoria.append(f"   Índice FGTS (Tabela): {indice}")
    if aliquota != Decimal('0.08'):
        memoria.append(f"   Ajuste por alíquota ({pct_display_sec3}%): {indice} × ({pct_display_sec3}% ÷ 8%) = {indice_efetivo}")
        memoria.append(f"   Índice Efetivo: {indice_efetivo}")
    memoria.append(f"   Cálculo do depósito: R$ {base_correcao:,.2f} × {indice_efetivo} = R$ {deposito_fgts_display:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
    memoria.append(f"   Correção = Depósito − FGTS do mês = R$ {deposito_fgts_display:,.2f} − R$ {valor_fgts:,.2f} = R$ {valor_corrigido:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
    memoria.append("")
    
    # Seção 4: Cálculo do JAM (Juros da Mora)
    memoria.append("4. CÁLCULO DO JAM (JUROS DA MORA)")
    memoria.append("-" * 80)

    # Período correto: do mês seguinte à competência até o mês da data de pagamento
    comp_dt = None
    try:
        comp_dt = datetime.strptime(competencia_str, '%m/%Y').date()
    except Exception:
        comp_dt = None

    if comp_dt is None:
        # Fallback caso formato inesperado; não interrompe geração
        comp_dt = date(data_pagamento.year, data_pagamento.month, 1)

    inicio_jam = (comp_dt.replace(day=1) + relativedelta(months=1))
    fim_jam = data_pagamento.replace(day=1)

    if inicio_jam > fim_jam:
        memoria.append(f"   Pagamento no mesmo mês da competência ({competencia_str}). JAM = R$ 0,00")
    else:
        periodo_txt = f"{inicio_jam.strftime('%m/%Y')} até {fim_jam.strftime('%m/%Y')}"
        memoria.append(f"   Regra: JAM acumulado do período ({periodo_txt})")
        memoria.append(f"   O JAM é calculado mês a mês com acúmulo de juros sobre o saldo anterior")
        memoria.append(f"   JAM Total do Período = R$ {valor_jam:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))

    memoria.append("")
    
    # Seção 5: Resultado Final
    memoria.append("5. RESULTADO FINAL")
    memoria.append("-" * 80)
    valor_corrigido_fgts = valor_deposito_fgts if valor_deposito_fgts is not None else (base_correcao * indice).quantize(Decimal('0.01'))
    memoria.append(f"   Valor FGTS Corrigido: R$ {valor_corrigido_fgts:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
    memoria.append(f"   JAM (Juros da Mora):  R$ {valor_jam:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
    memoria.append(f"   " + "-" * 76)
    memoria.append(f"   TOTAL:                 R$ {total:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
    memoria.append("")
    
    # Rodapé
    memoria.append("=" * 80)
    memoria.append("Data de Geração: " + date.today().strftime("%d/%m/%Y às %H:%M:%S"))
    memoria.append("Sistema: Bildee FGTS Web - Cálculo Automático")
    memoria.append("=" * 80)
    
    return "\n".join(memoria)

