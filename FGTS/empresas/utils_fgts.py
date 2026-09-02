from io import BytesIO
from datetime import datetime
import os
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.conf import settings
from .models_relatorio import RelatorioPremium
from .models import EmailLog

def gerar_pdf_fgts(memoria, email):
    def _format_currency(value):
        try:
            return f"{value:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
        except Exception:
            return str(value)

    def _format_date_br(value):
        if value is None:
            return ''
        if isinstance(value, datetime):
            return value.strftime('%d/%m/%Y')
        try:
            return datetime.strptime(str(value), '%Y-%m-%d').strftime('%d/%m/%Y')
        except Exception:
            return str(value)

    # Validação dos campos obrigatórios
    obrigatorios = [
        'competencia', 'data_pagamento', 'base_fgts', 'fgts_mes', 'indice',
        'deposito_fgts', 'correcao', 'jam'
    ]
    for campo in obrigatorios:
        if campo not in memoria:
            print(f"[ERRO PDF] Campo ausente em memoria: {campo}")
            raise ValueError(f"Campo obrigatório ausente: {campo}")

    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    margin_x = 30
    y = height - 40

    # Cabeçalho
    logo_path = getattr(settings, 'PDF_LOGO_PATH', None)
    if logo_path and os.path.exists(logo_path):
        p.drawImage(logo_path, margin_x, y - 20, width=110, height=30, preserveAspectRatio=True, mask='auto')

    p.setFont("Helvetica-Bold", 18)
    p.drawString(margin_x, y - 45, "Relatório FGTS Corrigido")

    p.setFont("Helvetica", 10)
    p.setFillColor(colors.grey)
    data_geracao = _format_date_br(datetime.now())
    relatorio_posicao = memoria.get('relatorio_posicao', 1)
    relatorio_total = memoria.get('relatorio_total', memoria.get('total_paginas', 1))
    p.drawRightString(width - margin_x, y - 30, f"Data de geração: {data_geracao}")
    p.drawRightString(width - margin_x, y - 45, f"Relatório {relatorio_posicao} de {relatorio_total}")
    p.setFillColor(colors.black)

    # Separador
    p.setStrokeColor(colors.lightgrey)
    p.setLineWidth(1)
    p.line(margin_x, y - 60, width - margin_x, y - 60)

    # Bloco de informações principais
    y = y - 85
    p.setFont("Helvetica", 11)
    p.drawString(margin_x, y, f"E-mail: {email}")
    y -= 18
    p.drawString(margin_x, y, f"Competência: {memoria['competencia']}")
    y -= 18
    p.drawString(margin_x, y, f"Data de Pagamento: {_format_date_br(memoria['data_pagamento'])}")

    # Separador
    y -= 14
    p.setStrokeColor(colors.lightgrey)
    p.line(margin_x, y, width - margin_x, y)

    # Tabela de resultados
    y -= 28
    table_x = margin_x
    table_width = width - (2 * margin_x)
    col_label = table_width * 0.58
    col_value = table_width * 0.42
    row_h = 22

    p.setFillColor(colors.HexColor('#F3F4F6'))
    p.rect(table_x, y - row_h, table_width, row_h, fill=1, stroke=0)
    p.setFillColor(colors.black)
    p.setFont("Helvetica-Bold", 11)
    p.drawString(table_x + 8, y - 16, "Item")
    p.drawRightString(table_x + table_width - 8, y - 16, "Valor")

    rows = [
        ("Base FGTS", _format_currency(memoria['base_fgts'])),
        ("FGTS do mês", _format_currency(memoria['fgts_mes'])),
        ("Índice FGTS", str(memoria['indice'])),
        ("Depósito Corrigido", _format_currency(memoria['deposito_fgts'])),
        ("Correção", _format_currency(memoria['correcao'])),
        ("JAM", _format_currency(memoria['jam'])),
    ]

    p.setFont("Helvetica", 11)
    y -= row_h
    for label, value in rows:
        p.setStrokeColor(colors.lightgrey)
        p.rect(table_x, y - row_h, table_width, row_h, fill=0, stroke=1)
        p.drawString(table_x + 8, y - 16, label)
        p.drawRightString(table_x + table_width - 8, y - 16, value)
        y -= row_h

    p.showPage()
    p.save()
    buffer.seek(0)
    return buffer

def _salvar_log_erro(email, mensagem, relatorio=None):
    try:
        EmailLog.objects.create(email=email, status='erro', mensagem=mensagem, relatorio=relatorio)
    except Exception:
        pass


def enviar_relatorio_fgts(email, memoria):
    """
    Envia o relatório FGTS por e-mail com a memória de cálculo no corpo HTML.
    Retorna (sucesso: bool, steps: list[dict]) para diagnóstico visual.
    Cada step: {'descricao': str, 'status': 'ok'|'erro'|'aviso', 'detalhe': str|None}
    """
    steps = []
    relatorio = None

    # Etapa 1: Montar corpo do e-mail (HTML)
    try:
        corpo = render_to_string('empresas/email_fgts.html', {
            'email': email,
            'memoria': memoria,
            'plataforma_url': getattr(settings, 'SITE_URL', ''),
        })
        steps.append({'descricao': 'Montar corpo do e-mail (HTML)', 'status': 'ok', 'detalhe': None})
    except Exception as e:
        steps.append({'descricao': 'Montar corpo do e-mail (HTML)', 'status': 'erro', 'detalhe': str(e)})
        _salvar_log_erro(email, str(e))
        return False, steps

    # Etapa 2: Criar mensagem de e-mail
    try:
        relatorio = RelatorioPremium.objects.filter(email=email).order_by('-data_geracao').first()
        msg = EmailMessage(
            'Seu FGTS corrigido com memória auditável está pronto',
            corpo,
            settings.DEFAULT_FROM_EMAIL,
            [email],
        )
        msg.content_subtype = 'html'
        steps.append({
            'descricao': f'Criar mensagem (de: {settings.DEFAULT_FROM_EMAIL} → para: {email})',
            'status': 'ok',
            'detalhe': None,
        })
    except Exception as e:
        steps.append({'descricao': 'Criar mensagem de e-mail', 'status': 'erro', 'detalhe': str(e)})
        _salvar_log_erro(email, str(e), relatorio)
        return False, steps

    # Etapa 3: Enviar via SMTP
    try:
        msg.send()
        steps.append({'descricao': 'Enviar e-mail via SMTP (Brevo)', 'status': 'ok', 'detalhe': None})
    except Exception as e:
        steps.append({'descricao': 'Enviar e-mail via SMTP (Brevo)', 'status': 'erro', 'detalhe': str(e)})
        _salvar_log_erro(email, str(e), relatorio)
        return False, steps

    # Etapa 4: Registrar log de auditoria
    try:
        EmailLog.objects.create(
            email=email, status='sucesso',
            mensagem='E-mail enviado com sucesso.', relatorio=relatorio,
        )
        steps.append({'descricao': 'Registrar log de auditoria', 'status': 'ok', 'detalhe': None})
    except Exception as e:
        steps.append({'descricao': 'Registrar log de auditoria', 'status': 'aviso', 'detalhe': str(e)})

    return True, steps
