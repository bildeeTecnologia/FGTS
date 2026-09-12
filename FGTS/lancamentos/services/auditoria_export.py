"""
Exportação XLSX das telas de Auditoria de Lançamentos.
"""
from io import BytesIO

import openpyxl
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

_FILL_HEADER = PatternFill('solid', fgColor='003A78')
_FONT_HEADER = Font(bold=True, color='FFFFFF')

_STATUS_LABEL = {
    'ok': 'OK',
    'justificado': 'Justificado',
    'fora_do_plano': 'Fora do plano',
    'pendente': 'Pendente',
}


def _header_row(ws, cols, row=1):
    for c, title in enumerate(cols, 1):
        cell = ws.cell(row=row, column=c, value=title)
        cell.font = _FONT_HEADER
        cell.fill = _FILL_HEADER
        cell.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)


def _auto_width(ws, min_width=10, max_width=60):
    for col_cells in ws.columns:
        length = max(len(str(cell.value or '')) for cell in col_cells)
        ws.column_dimensions[get_column_letter(col_cells[0].column)].width = min(
            max(length + 2, min_width), max_width
        )


def gerar_xlsx_auditoria_lista(empresa, resumos) -> bytes:
    """XLSX com um vínculo por linha (contadores esperado/realizado/justificado/pendente)."""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = 'Auditoria'

    cols = [
        'Funcionário', 'Matrícula', 'Admissão', 'Demissão', 'Status',
        'Esperados', 'Realizados', 'Justificados', 'Fora do plano', 'Pendentes',
    ]
    _header_row(ws, cols)
    ws.freeze_panes = 'A2'

    for r, resumo in enumerate(resumos, 2):
        vinculo = resumo['vinculo']
        vals = [
            vinculo.funcionario.nome,
            vinculo.matricula or '',
            vinculo.data_admissao.strftime('%d/%m/%Y') if vinculo.data_admissao else '',
            vinculo.data_demissao.strftime('%d/%m/%Y') if vinculo.data_demissao else '',
            vinculo.get_status_display(),
            resumo['qtd_esperados'],
            resumo['qtd_realizados'],
            resumo['qtd_justificados'],
            resumo['qtd_fora_do_plano'],
            resumo['qtd_pendentes'],
        ]
        for c, val in enumerate(vals, 1):
            ws.cell(row=r, column=c, value=val)

    _auto_width(ws)
    buf = BytesIO()
    wb.save(buf)
    return buf.getvalue()


def _detalhe_item(item):
    if item['status'] == 'ok' and item['lancamento']:
        lanc = item['lancamento']
        return f"Lançamento #{lanc.id} ({'pago' if lanc.pago else 'não pago'})"
    if item['status'] == 'justificado' and item['justificativa']:
        just = item['justificativa']
        detalhe = just.get_motivo_display()
        if just.observacao:
            detalhe += f" — {just.observacao}"
        usuario = just.usuario.username if just.usuario else '—'
        detalhe += f" (por {usuario} em {just.criado_em.strftime('%d/%m/%Y')})"
        return detalhe
    if item['status'] == 'fora_do_plano':
        return 'Anterior ao início do histórico aceito pelo plano contratado'
    return 'Sem lançamento e sem justificativa'


def gerar_xlsx_auditoria_vinculo(vinculo, auditoria) -> bytes:
    """XLSX com a linha do tempo completa (uma competência por linha) de um vínculo."""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = 'Auditoria do Vínculo'

    ws.cell(row=1, column=1, value=f"{vinculo.funcionario.nome} — {vinculo.empresa.nome}").font = Font(bold=True, size=13)
    matricula_label = f"Matrícula {vinculo.matricula}" if vinculo.matricula else f"Vínculo {vinculo.pk}"
    ws.cell(row=2, column=1, value=matricula_label).font = Font(italic=True, color='555555')

    cols = ['Competência', 'Tipo', 'Status', 'Detalhe']
    _header_row(ws, cols, row=3)
    ws.freeze_panes = 'A4'

    for r, item in enumerate(auditoria['itens'], 4):
        if item['parcela_13'] == 1:
            tipo = '13º — 1ª parcela'
        elif item['parcela_13'] == 2:
            tipo = '13º — 2ª parcela'
        else:
            tipo = 'Normal'

        vals = [
            item['competencia'],
            tipo,
            _STATUS_LABEL.get(item['status'], item['status']),
            _detalhe_item(item),
        ]
        for c, val in enumerate(vals, 1):
            ws.cell(row=r, column=c, value=val)

    _auto_width(ws)
    buf = BytesIO()
    wb.save(buf)
    return buf.getvalue()
