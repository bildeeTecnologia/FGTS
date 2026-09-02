"""
Views do módulo BPO — Bureau de Processamento de Folha
"""

import calendar
import logging
import re
from datetime import date, timedelta
from decimal import Decimal
from uuid import uuid4

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.html import format_html

from billing.models import BillingCustomer
from billing.models_bpo import PlanoBPO, ContaBPO, EmpresaBPO, calcular_rateio
from billing.services.asaas_client import AsaasClient
from empresas.models import Empresa

logger = logging.getLogger(__name__)


def _get_conta_bpo(user):
    """Retorna a ContaBPO do usuário, ou None se não for um BPO."""
    empresa_id = getattr(user, 'empresa_id', None)
    if not empresa_id:
        return None
    return ContaBPO.objects.filter(empresa_bpo_id=empresa_id).first()


def _requer_bpo(view_func):
    """Decorator: exige que o usuário tenha um ContaBPO ativo ou em trial."""
    def wrapper(request, *args, **kwargs):
        conta_bpo = _get_conta_bpo(request.user)
        if not conta_bpo:
            messages.error(request, 'Sua conta não é do tipo BPO. Acesse os planos para contratar.')
            return redirect('billing:bpo-planos')
        if conta_bpo.status == 'canceled':
            messages.error(request, 'Sua conta BPO está cancelada. Entre em contato com o suporte.')
            return redirect('billing:bpo-dashboard')
        request.conta_bpo = conta_bpo
        return view_func(request, *args, **kwargs)
    return wrapper


# ─── Planos BPO ───────────────────────────────────────────────────────────────

@login_required
def bpo_planos(request):
    """Exibe os planos BPO disponíveis e permite ativação da conta BPO."""
    # Verifica se já tem conta BPO
    conta_bpo = _get_conta_bpo(request.user)
    if conta_bpo:
        return redirect('billing:bpo-dashboard')

    planos = PlanoBPO.objects.filter(ativo=True).order_by('preco_por_cnpj')
    return render(request, 'billing/bpo/planos.html', {'planos': planos})


@login_required
def bpo_ativar(request):
    """Ativa a conta BPO para a empresa do usuário."""
    if request.method != 'POST':
        return redirect('billing:bpo-planos')

    # Verifica se já tem conta BPO
    if _get_conta_bpo(request.user):
        return redirect('billing:bpo-dashboard')

    empresa = getattr(request.user, 'empresa', None)
    if not empresa:
        messages.error(request, 'Você precisa ter uma empresa cadastrada para ativar o plano BPO.')
        return redirect('billing:bpo-planos')

    plano_id = request.POST.get('plano_id')
    try:
        plano = PlanoBPO.objects.get(pk=plano_id, ativo=True)
    except PlanoBPO.DoesNotExist:
        messages.error(request, 'Plano inválido. Por favor, selecione um plano.')
        return redirect('billing:bpo-planos')

    # Cria a ContaBPO com trial
    hoje = date.today()
    trial_expira = hoje + timedelta(days=plano.trial_dias)

    with transaction.atomic():
        conta_bpo = ContaBPO.objects.create(
            empresa_bpo=empresa,
            plano=plano,
            status='trial',
            dia_cobranca=5,
            trial_ativo=True,
            trial_expira=trial_expira,
            trial_used=False,
        )

    messages.success(
        request,
        f'Conta BPO ativada! Você tem {plano.trial_dias} dias de trial para explorar a plataforma.'
    )
    return redirect('billing:bpo-dashboard')


# ─── Checkout pós-trial ───────────────────────────────────────────────────────

@login_required
def bpo_checkout(request):
    """
    Checkout pós-trial: registra o escritório no Asaas e ativa a conta BPO.
    A primeira fatura mensal será gerada pelo management command `cobrar_bpo_mensal`
    na data de vencimento configurada.
    """
    conta_bpo = _get_conta_bpo(request.user)
    if not conta_bpo:
        return redirect('billing:bpo-planos')
    if conta_bpo.status == 'active':
        return redirect('billing:bpo-dashboard')

    empresa = conta_bpo.empresa_bpo

    if request.method == 'GET':
        context = {
            'conta_bpo': conta_bpo,
            'cnpjs_ativos': conta_bpo.get_cnpjs_ativos(),
            'preco_por_cnpj': conta_bpo.get_effective_preco_por_cnpj(),
            'valor_mensal': conta_bpo.valor_proxima_fatura(),
            'proximo_vencimento': conta_bpo.proximo_vencimento(),
        }
        return render(request, 'billing/bpo/checkout.html', context)

    # POST — registra no Asaas e ativa
    billing_type = request.POST.get('billing_type', 'BOLETO')
    if billing_type not in ('BOLETO', 'PIX', 'CREDIT_CARD'):
        billing_type = 'BOLETO'

    try:
        client = AsaasClient()

        if not conta_bpo.asaas_customer_id:
            cnpj = re.sub(r'\D', '', getattr(empresa, 'cnpj', '') or '')
            fone = re.sub(r'\D', '', getattr(empresa, 'fone_contato', '') or '')
            payload = {
                'name': empresa.nome,
                'cpfCnpj': cnpj,
                'externalReference': f'bpo-{conta_bpo.pk}',
            }
            if fone:
                payload['phone'] = fone
            resp = client.create_customer(payload)
            customer_id = resp.get('id')
            if not customer_id:
                raise ValueError(f'Asaas não retornou customer ID: {resp}')

            # Salva de forma segura para evitar race condition
            updated = ContaBPO.objects.filter(
                pk=conta_bpo.pk, asaas_customer_id__isnull=True
            ).update(asaas_customer_id=customer_id, status='active', billing_type=billing_type)

            if not updated:
                # Outro request já salvou — apenas ativa
                ContaBPO.objects.filter(pk=conta_bpo.pk).update(
                    status='active', billing_type=billing_type
                )
        else:
            ContaBPO.objects.filter(pk=conta_bpo.pk).update(
                status='active', billing_type=billing_type
            )

    except Exception:
        logger.exception('Erro ao criar customer BPO no Asaas. ContaBPO pk=%s', conta_bpo.pk)
        messages.error(
            request,
            'Ocorreu um erro ao processar seu cadastro. Tente novamente ou entre em contato com o suporte.'
        )
        return redirect('billing:bpo-checkout')

    messages.success(request, '✅ Conta BPO ativada com sucesso! Sua primeira fatura será gerada no próximo vencimento.')
    return redirect('billing:bpo-dashboard')


# ─── Dashboard BPO ────────────────────────────────────────────────────────────

@login_required
@_requer_bpo
def bpo_dashboard(request):
    """Painel principal do escritório BPO."""
    conta_bpo = request.conta_bpo
    empresas_gerenciadas = (
        conta_bpo.empresas_gerenciadas
        .select_related('empresa')
        .order_by('status', 'empresa__nome')
    )

    cnpjs_ativos = conta_bpo.get_cnpjs_ativos()
    preco_efetivo = conta_bpo.get_effective_preco_por_cnpj()
    valor_proxima_fatura = conta_bpo.valor_proxima_fatura()
    proximo_vencimento = conta_bpo.proximo_vencimento()

    context = {
        'conta_bpo': conta_bpo,
        'empresas_gerenciadas': empresas_gerenciadas,
        'cnpjs_ativos': cnpjs_ativos,
        'preco_por_cnpj': preco_efetivo,
        'valor_proxima_fatura': valor_proxima_fatura,
        'proximo_vencimento': proximo_vencimento,
        'em_trial': conta_bpo.is_trial_ativo(),
        'dias_restantes_trial': conta_bpo.dias_restantes_trial(),
    }
    return render(request, 'billing/bpo/dashboard.html', context)


# ─── Adicionar Empresa ────────────────────────────────────────────────────────

@login_required
@_requer_bpo
def bpo_adicionar_empresa(request):
    """
    GET: exibe formulário com preview de rateio.
    POST: ativa o CNPJ, cobra rateio no Asaas (se aplicável), cria EmpresaBPO.
    """
    conta_bpo = request.conta_bpo

    if request.method == 'GET':
        valor_rateio, proximo_venc, dias_restantes = conta_bpo.calcular_rateio_novo_cnpj()
        dias_no_ciclo = calendar.monthrange(date.today().year, date.today().month)[1]
        context = {
            'conta_bpo': conta_bpo,
            'valor_rateio': valor_rateio,
            'proximo_vencimento': proximo_venc,
            'dias_restantes': dias_restantes,
            'dias_no_ciclo': dias_no_ciclo,
            'preco_por_cnpj': conta_bpo.get_effective_preco_por_cnpj(),
            'cnpjs_ativos': conta_bpo.get_cnpjs_ativos(),
            'em_trial': conta_bpo.is_trial_ativo(),
        }
        return render(request, 'billing/bpo/adicionar_empresa.html', context)

    # POST — processa adição
    cnpj = request.POST.get('cnpj', '').strip()
    nome = request.POST.get('nome', '').strip()
    permite_acesso = request.POST.get('permite_acesso_cliente') == 'on'

    if not cnpj or not nome:
        messages.error(request, 'CNPJ e nome da empresa são obrigatórios.')
        return redirect('billing:bpo-adicionar-empresa')

    # Verifica se CNPJ já está em uso
    if Empresa.objects.filter(cnpj=cnpj).exists():
        empresa_existente = Empresa.objects.get(cnpj=cnpj)
        # Se já está gerenciada por este BPO, informa
        if hasattr(empresa_existente, 'empresa_bpo') and empresa_existente.empresa_bpo.conta_bpo == conta_bpo:
            messages.warning(request, f'O CNPJ {cnpj} já está cadastrado em sua conta BPO.')
            return redirect('billing:bpo-dashboard')
        messages.error(request, f'O CNPJ {cnpj} já está cadastrado na plataforma e não pode ser vinculado.')
        return redirect('billing:bpo-adicionar-empresa')

    with transaction.atomic():
        # Cria a Empresa
        codigo_folha = f"CF{uuid4().hex[:8].upper()}"
        while Empresa.objects.filter(codigo_folha=codigo_folha).exists():
            codigo_folha = f"CF{uuid4().hex[:8].upper()}"

        empresa = Empresa.objects.create(
            nome=nome,
            cnpj=cnpj,
            codigo_folha=codigo_folha,
        )

        # Calcula rateio
        valor_rateio, proximo_venc, dias_restantes = conta_bpo.calcular_rateio_novo_cnpj()
        em_trial = conta_bpo.is_trial_ativo()

        # Cobra rateio no Asaas se não estiver em trial e tiver customer_id
        asaas_payment_id = None
        if not em_trial and conta_bpo.asaas_customer_id and valor_rateio > Decimal('0.00'):
            billing_type = request.POST.get('billing_type', 'BOLETO')
            try:
                client = AsaasClient()
                payment_payload = {
                    'customer': conta_bpo.asaas_customer_id,
                    'billingType': billing_type,
                    'value': float(valor_rateio),
                    'dueDate': date.today().isoformat(),
                    'description': f'FGTS Web BPO — Ativação de CNPJ: {nome} ({cnpj})',
                }
                resp = client.create_payment(payment_payload)
                asaas_payment_id = resp.get('id')
            except Exception:
                logger.exception('Erro ao criar cobrança de rateio BPO no Asaas. Empresa: %s', cnpj)

        # Cria EmpresaBPO
        empresa_bpo = EmpresaBPO.objects.create(
            conta_bpo=conta_bpo,
            empresa=empresa,
            status='active',
            permite_acesso_cliente=permite_acesso,
            rateio_cobrado=valor_rateio if not em_trial else Decimal('0.00'),
            asaas_payment_id_rateio=asaas_payment_id,
        )

        # Cria BillingCustomer (para compatibilidade com o restante do sistema)
        BillingCustomer.objects.create(
            empresa=empresa,
            status='active',
            gerenciada_por_bpo=conta_bpo,
            trial_active=False,
        )

        # Adiciona empresa às empresas_permitidas do usuário BPO
        request.user.empresas_permitidas.add(empresa)
        if not request.user.is_multi_empresa:
            request.user.is_multi_empresa = True
            request.user.save(update_fields=['is_multi_empresa'])

    if em_trial:
        msg = format_html('✅ Empresa <strong>{}</strong> adicionada com sucesso ao seu plano BPO (sem cobrança durante o trial).', nome)
    elif asaas_payment_id:
        msg = format_html('✅ Empresa <strong>{}</strong> adicionada. Cobrança de rateio de R$ {} gerada — verifique seu e-mail.', nome, valor_rateio)
    else:
        msg = format_html('✅ Empresa <strong>{}</strong> adicionada ao seu plano BPO.', nome)

    messages.success(request, msg)
    return redirect('billing:bpo-dashboard')


# ─── Remover / Suspender Empresa ─────────────────────────────────────────────

@login_required
@_requer_bpo
def bpo_remover_empresa(request, empresa_bpo_id):
    """Suspende uma empresa gerenciada (não cobra no próximo ciclo)."""
    if request.method != 'POST':
        return redirect('billing:bpo-dashboard')

    conta_bpo = request.conta_bpo
    empresa_bpo = get_object_or_404(EmpresaBPO, pk=empresa_bpo_id, conta_bpo=conta_bpo)

    with transaction.atomic():
        empresa_bpo.status = 'suspended'
        empresa_bpo.data_suspensao = date.today()
        empresa_bpo.save(update_fields=['status', 'data_suspensao', 'atualizado_em'])

        # Atualiza BillingCustomer
        try:
            bc = empresa_bpo.empresa.billing_customer
            bc.status = 'inactive'
            bc.save(update_fields=['status', 'updated_at'])
        except Exception:
            pass

        # Remove das empresas_permitidas do usuário BPO
        request.user.empresas_permitidas.remove(empresa_bpo.empresa)

    messages.success(
        request,
        format_html(
            'Empresa <strong>{}</strong> suspensa. Não será cobrada no próximo ciclo.',
            empresa_bpo.empresa.nome,
        )
    )
    return redirect('billing:bpo-dashboard')


# ─── Toggle acesso do cliente ─────────────────────────────────────────────────

@login_required
@_requer_bpo
def bpo_toggle_acesso(request, empresa_bpo_id):
    """Alterna se a empresa cliente pode fazer login na plataforma."""
    if request.method != 'POST':
        return redirect('billing:bpo-dashboard')

    conta_bpo = request.conta_bpo
    empresa_bpo = get_object_or_404(EmpresaBPO, pk=empresa_bpo_id, conta_bpo=conta_bpo)

    empresa_bpo.permite_acesso_cliente = not empresa_bpo.permite_acesso_cliente
    empresa_bpo.save(update_fields=['permite_acesso_cliente', 'atualizado_em'])

    estado = 'ativado' if empresa_bpo.permite_acesso_cliente else 'desativado'
    messages.success(
        request,
        format_html('Acesso do cliente à empresa <strong>{}</strong> {}.', empresa_bpo.empresa.nome, estado)
    )
    return redirect('billing:bpo-dashboard')


# ─── Reativar Empresa ─────────────────────────────────────────────────────────

@login_required
@_requer_bpo
def bpo_reativar_empresa(request, empresa_bpo_id):
    """Reativa uma empresa gerenciada que estava suspensa."""
    if request.method != 'POST':
        return redirect('billing:bpo-dashboard')

    conta_bpo = request.conta_bpo
    empresa_bpo = get_object_or_404(EmpresaBPO, pk=empresa_bpo_id, conta_bpo=conta_bpo, status='suspended')

    with transaction.atomic():
        empresa_bpo.status = 'active'
        empresa_bpo.data_suspensao = None
        empresa_bpo.save(update_fields=['status', 'data_suspensao', 'atualizado_em'])

        # Reativa o BillingCustomer
        try:
            bc = empresa_bpo.empresa.billing_customer
            bc.status = 'active'
            bc.save(update_fields=['status', 'updated_at'])
        except Exception:
            pass

        # Readiciona às empresas_permitidas do usuário BPO
        request.user.empresas_permitidas.add(empresa_bpo.empresa)
        if not request.user.is_multi_empresa:
            request.user.is_multi_empresa = True
            request.user.save(update_fields=['is_multi_empresa'])

    messages.success(
        request,
        format_html('Empresa <strong>{}</strong> reativada com sucesso.', empresa_bpo.empresa.nome),
    )
    return redirect('billing:bpo-dashboard')


# ─── API de preview de rateio (AJAX) ─────────────────────────────────────────

@login_required
def bpo_preview_rateio(request):
    """Retorna JSON com o valor do rateio para o BPO atual."""
    conta_bpo = _get_conta_bpo(request.user)
    if not conta_bpo:
        return JsonResponse({'erro': 'Conta BPO não encontrada'}, status=404)

    valor_rateio, proximo_venc, dias_restantes = conta_bpo.calcular_rateio_novo_cnpj()
    dias_no_ciclo = calendar.monthrange(date.today().year, date.today().month)[1]

    return JsonResponse({
        'valor_rateio': str(valor_rateio),
        'proximo_vencimento': proximo_venc.strftime('%d/%m/%Y'),
        'dias_restantes': dias_restantes,
        'dias_no_ciclo': dias_no_ciclo,
        'preco_por_cnpj': str(conta_bpo.get_effective_preco_por_cnpj()),
        'cnpjs_ativos': conta_bpo.get_cnpjs_ativos(),
        'valor_proxima_fatura': str(
            conta_bpo.get_effective_preco_por_cnpj() * (conta_bpo.get_cnpjs_ativos() + 1)
        ),
        'em_trial': conta_bpo.is_trial_ativo(),
    })
