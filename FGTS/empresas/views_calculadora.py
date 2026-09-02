from django.shortcuts import render, redirect
from django.urls import reverse
from django.contrib import messages
from django.utils import timezone
from .forms_calculadora import FGTSCalculadoraForm
from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime
from indices.services.indice_service import IndiceFGTSService
from coefjam.models import CoefJam
from .models_relatorio import RelatorioPremium
from .utils_fgts import enviar_relatorio_fgts
from .services_leads import register_credit_trigger

def buscar_indice_fgts(competencia, data_pagamento):
    # Busca o índice com filtro exato via serviço oficial (ORM + fallback REST)
    try:
        comp_date = datetime.strptime(competencia, '%m/%Y').date().replace(day=1)
    except Exception:
        return None
    return IndiceFGTSService.buscar_indice(competencia=comp_date, data_pagamento=data_pagamento)


def calcular_jam_acumulado(fgts_mes, competencia, data_pagamento):
    # Calcula JAM mês a mês do mês seguinte à competência até o mês do pagamento
    from dateutil.relativedelta import relativedelta
    saldo = fgts_mes
    jam_total = Decimal('0.00')
    meses = []
    try:
        comp_date = datetime.strptime(competencia, '%m/%Y').date().replace(day=1)
        pagto_date = data_pagamento.replace(day=1)
        cursor = comp_date + relativedelta(months=1)
        while cursor <= pagto_date:
            competencia_str = cursor.strftime('%Y-%m')
            jam_coef = CoefJam.objects.filter(competencia=competencia_str).order_by('-data_pagamento').first()
            if jam_coef:
                jam_mes = (saldo * Decimal(jam_coef.valor)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                jam_total += jam_mes
                saldo = (saldo + jam_mes).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                meses.append({'mes': competencia_str, 'coef': jam_coef.valor, 'jam_mes': jam_mes, 'saldo': saldo})
            else:
                meses.append({'mes': competencia_str, 'coef': None, 'jam_mes': Decimal('0.00'), 'saldo': saldo})
            cursor += relativedelta(months=1)
    except Exception:
        pass
    return jam_total, meses

def _serializar_memoria(memoria):
    """Converte meses_jam (com Decimals) para formato JSON-seguro para armazenar na sessão."""
    meses_safe = []
    for m in (memoria.get('meses_jam') or []):
        meses_safe.append({
            'mes': m['mes'],
            'coef': float(m['coef']) if m['coef'] is not None else None,
            'jam_mes': float(m['jam_mes']),
            'saldo': float(m['saldo']),
        })
    return {**memoria, 'meses_jam': meses_safe}


def calculadora_fgts_view(request):
    resultado = None
    memoria = None
    email = None
    premium_liberado = False
    mensagem = None
    steps_email = None

    if request.method == 'POST':
        email = request.POST.get('email')

        # ── Passo 2: envio de e-mail ──────────────────────────────────────────
        # Detectado pelo campo oculto _apenas_email; não re-valida o formulário.
        if request.POST.get('_apenas_email') == '1':
            memoria = request.session.get('calculadora_memoria')
            form = FGTSCalculadoraForm()

            if not memoria:
                mensagem = "Sessão expirada. Por favor, refaça o cálculo antes de solicitar o relatório."
            elif not email:
                mensagem = "Informe seu e-mail para liberar o relatório premium."
            else:
                relatorios_count = RelatorioPremium.objects.filter(email=email).count()
                if relatorios_count < 3:
                    is_third_credit = relatorios_count == 2
                    memoria_envio = {
                        **memoria,
                        'relatorio_posicao': relatorios_count + 1,
                        'relatorio_total': 3,
                    }
                    RelatorioPremium.objects.create(email=email, memoria=memoria_envio)
                    if is_third_credit:
                        register_credit_trigger(email)
                    sucesso, steps_email = enviar_relatorio_fgts(email, memoria_envio)
                    if sucesso:
                        # PRG: redireciona para GET limpo — evita re-submit no F5
                        request.session.pop('calculadora_memoria', None)
                        messages.success(
                            request,
                            f"Relatório enviado para {email}. "
                            f"Você pode gerar mais {2 - relatorios_count} relatório(s) gratuito(s)."
                        )
                        return redirect(reverse('calculadora-fgts'))
                    else:
                        mensagem = "Falha ao enviar o e-mail. Veja o diagnóstico abaixo."
                else:
                    mensagem = "Você atingiu o limite de 3 relatórios gratuitos. Para gerar mais, contrate um de nossos planos."

        # ── Passo 1: cálculo ──────────────────────────────────────────────────
        else:
            form = FGTSCalculadoraForm(request.POST)
            if form.is_valid():
                base_fgts = form.cleaned_data['base_fgts']
                competencia = form.cleaned_data['competencia']
                data_pagamento = form.cleaned_data['data_pagamento']

                fgts_mes = (base_fgts * Decimal('0.08')).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                indice = buscar_indice_fgts(competencia, data_pagamento)
                if indice is None:
                    mensagem = (
                        f"Índice FGTS não encontrado para a competência {competencia} "
                        f"na data de pagamento {data_pagamento.strftime('%d/%m/%Y')}. "
                        "Verifique se os dados estão corretos ou tente outra data de pagamento."
                    )
                    return render(request, 'empresas/calculadora_fgts.html', {
                        'form': form,
                        'resultado': None,
                        'memoria': None,
                        'email': email,
                        'premium_liberado': False,
                        'mensagem': mensagem,
                        'steps_email': None,
                        'hoje': timezone.now().date(),
                        'data_maxima': IndiceFGTSService.obter_ultima_data_base(),
                    })
                deposito_fgts = (base_fgts * indice).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                correcao = (deposito_fgts - fgts_mes).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                jam, meses_jam = calcular_jam_acumulado(fgts_mes, competencia, data_pagamento)
                total = (deposito_fgts + jam).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

                memoria = {
                    'base_fgts': float(base_fgts),
                    'fgts_mes': float(fgts_mes),
                    'indice': float(indice),
                    'deposito_fgts': float(deposito_fgts),
                    'correcao': float(correcao),
                    'jam': float(jam),
                    'total': float(total),
                    'competencia': competencia,
                    'data_pagamento': data_pagamento.strftime('%d/%m/%Y'),
                    'meses_jam': meses_jam,
                }

                # Guardar na sessão para uso no passo 2 (sem re-validar)
                request.session['calculadora_memoria'] = _serializar_memoria(memoria)
                mensagem = "Informe seu e-mail para liberar o relatório premium."

    else:
        form = FGTSCalculadoraForm()

    return render(request, 'empresas/calculadora_fgts.html', {
        'form': form,
        'resultado': resultado,
        'memoria': memoria,
        'email': email,
        'premium_liberado': premium_liberado,
        'mensagem': mensagem,
        'steps_email': steps_email,
        'hoje': timezone.now().date(),
        'data_maxima': IndiceFGTSService.obter_ultima_data_base(),
    })
