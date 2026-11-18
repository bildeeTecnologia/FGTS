"""
Exportação XLSX da tela "JAM Total por Pessoa" (consolidado + analítico + premissas).
"""
from io import BytesIO

import openpyxl
from openpyxl.styles import Font

from .auditoria_export import _auto_width, _header_row

_BRL = '#,##0.00'
_BOLD = Font(bold=True)


def gerar_xlsx_jam_total(resultado, filtros_descricao) -> bytes:
    grupos = resultado['grupos']
    totais = resultado['totais']

    wb = openpyxl.Workbook()

    # --- Consolidado (por pessoa + empresa)
    ws = wb.active
    ws.title = 'Consolidado'
    _header_row(ws, [
        'Funcionário', 'CPF', 'PIS', 'Empresa (vínculo)', 'CNPJ', 'Qtd competências', 'Soma FGTS devido',
        'JAM em competências pagas', 'JAM em competências em aberto', 'JAM TOTAL', 'FGTS + JAM',
    ])
    ws.freeze_panes = 'A2'
    for g in grupos:
        ws.append([
            g['nome'], g['cpf'], g['pis'], g['empresa'], g['cnpj'], g['qtd'], g['fgts'],
            g['jam_pago'], g['jam_aberto'], g['jam'], g['total'],
        ])
    ws.append(['TOTAL GERAL', '', '', '', '', totais['qtd'], totais['fgts'],
               totais['jam_pago'], totais['jam_aberto'], totais['jam'], totais['total']])
    for c in ws[ws.max_row]:
        c.font = _BOLD
    for row in ws.iter_rows(min_row=2, min_col=7, max_col=11):
        for c in row:
            c.number_format = _BRL
    _auto_width(ws)

    # --- Analítico (competência por competência)
    wa = wb.create_sheet('Analítico')
    _header_row(wa, [
        'Funcionário', 'CPF', 'Empresa (vínculo)', 'CNPJ', 'Matrícula', 'Competência', '13º parcela',
        'Base FGTS', 'FGTS devido', 'Pago?', 'Data pagto', 'Valor pago', 'JAM atualizado', 'FGTS + JAM',
        'Meses sem coef. JAM',
    ])
    wa.freeze_panes = 'A2'
    for g in grupos:
        for r in g['linhas']:
            wa.append([
                g['nome'], g['cpf'], g['empresa'], g['cnpj'], r['matricula'], r['comp'].strftime('%m/%Y'),
                r['parcela_13'] or '', r['base_fgts'], r['valor_fgts'], 'Sim' if r['pago'] else 'Não',
                r['data_pagto'], r['valor_pago'], r['jam'], r['total'], r['sem_coef'],
            ])
    for row in wa.iter_rows(min_row=2):
        for c in row:
            if c.column in (8, 9, 12, 13, 14):
                c.number_format = _BRL
            elif c.column == 11:
                c.number_format = 'DD/MM/YYYY'
    wa.auto_filter.ref = wa.dimensions
    _auto_width(wa)

    # --- Premissas
    wp = wb.create_sheet('Premissas')
    meses = ', '.join(m.strftime('%m/%Y') for m in resultado['meses_sem_coef']) or 'nenhum'
    for linha in [
        ('Filtros', filtros_descricao),
        ('Data de atualização', resultado['data_pagamento'].strftime('%d/%m/%Y')),
        ('Motor', 'Mesmo do relatório de competências (plano econômico legado + JAM composto mês a mês)'),
        ('JAM', 'Do mês seguinte à competência até o mês da data de atualização; sem JAM no mês da competência'),
        ('Escopo', 'Todas as competências lançadas (pagas e em aberto), de todos os vínculos; casamento por CPF'),
        ('Competências sem coeficiente JAM (consideradas 0)', meses),
        ('Lançamentos ignorados (competência ilegível)', resultado['ignorados']),
    ]:
        wp.append(linha)
    for c in wp['A']:
        c.font = _BOLD
    wp.column_dimensions['A'].width = 48
    wp.column_dimensions['B'].width = 110

    buffer = BytesIO()
    wb.save(buffer)
    return buffer.getvalue()
