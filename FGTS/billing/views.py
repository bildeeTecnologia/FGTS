import json
import os
from datetime import timedelta
from decimal import Decimal
from typing import Optional
import logging

import requests
from requests import RequestException
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseForbidden, HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import TemplateView

from empresas.models import Empresa
from fgtsweb.mixins import is_empresa_allowed
from .models import BillingCustomer, Subscription, Payment, PricingPlan, Plan
from .models_bpo import FaturaBPO, ContaBPO
from .services.asaas_client import AsaasClient

logger = logging.getLogger(__name__)


DEFAULT_PLAN_VALUE = Decimal('99.90')
DEFAULT_PERIODICITY = 'MONTHLY'
PLAN_PRICE_OVERRIDE = {
    'BASIC': Decimal('199.00'),          # Essencial
    'PROFESSIONAL': Decimal('699.00'),   # Profissional
    'ENTERPRISE': Decimal('0.00'),       # Sob consulta
}

# Mapeamento de status Asaas (UPPERCASE) -> status local (lowercase)
ASAAS_PAYMENT_STATUS_MAP = {
    'PENDING': 'pending',
    'RECEIVED': 'confirmed',
    'CONFIRMED': 'confirmed',
    'RECEIVED_IN_CASH': 'confirmed',
    'OVERDUE': 'overdue',
    'REFUNDED': 'canceled',
    'REFUND_REQUESTED': 'canceled',
    'CHARGEBACK_REQUESTED': 'canceled',
    'CHARGEBACK_DISPUTE': 'canceled',
    'AWAITING_CHARGEBACK_REVERSAL': 'canceled',
    'DUNNING_REQUESTED': 'overdue',
    'DUNNING_RECEIVED': 'confirmed',
    'AWAITING_RISK_ANALYSIS': 'pending',
}

# Status Asaas que indicam pagamento confirmado
ASAAS_CONFIRMED_STATUSES = {'RECEIVED', 'CONFIRMED', 'RECEIVED_IN_CASH', 'DUNNING_RECEIVED', 'CONFIRMED_OVERDUE'}
ASAAS_OVERDUE_STATUSES = {'OVERDUE', 'DUNNING_REQUESTED'}
ASAAS_CANCELED_STATUSES = {'CANCELLED', 'REFUNDED', 'REFUND_REQUESTED', 'CHARGEBACK_REQUESTED', 'CHARGEBACK_DISPUTE'}


class CheckoutPlanoView(TemplateView):
    """Página de checkout pública - sem login obrigatório"""
    template_name = 'billing/checkout_plano.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        plan_type = self.kwargs.get('plan_type')

        # Buscar plano selecionado (se houver)
        if plan_type:
            try:
                context['selected_plan'] = Plan.objects.get(plan_type=plan_type, active=True)
            except Plan.DoesNotExist:
                context['selected_plan'] = None

        # Listar todos os planos
        context['all_plans'] = Plan.objects.filter(active=True).order_by('plan_type')

        # Se o usuário está logado e tem override_price > 0, o Enterprise pode ir para o checkout
        user = self.request.user
        if user.is_authenticated:
            empresa = getattr(user, 'empresa', None)
            if not empresa and hasattr(user, 'empresas_permitidas'):
                empresa = user.empresas_permitidas.first()
            if empresa:
                try:
                    bc = empresa.billing_customer
                    if bc.override_price and bc.override_price > 0:
                        context['enterprise_override_price'] = bc.override_price
                        context['enterprise_empresa_id'] = empresa.pk
                except Exception:
                    pass

        return context

    def post(self, request, *args, **kwargs):
        """Processa seleção e redireciona"""
        plan_type = request.POST.get('plan_type')

        try:
            plan = Plan.objects.get(plan_type=plan_type, active=True)
        except Plan.DoesNotExist:
            messages.error(request, 'Plano inválido')
            return redirect('billing:checkout-plano')

        # Aplicar override de preço conforme tabela pública
        plan_price = PLAN_PRICE_OVERRIDE.get(plan.plan_type, plan.price_monthly)

        # Salvar na sessão
        request.session['selected_plan_type'] = plan_type
        request.session['selected_plan_price'] = str(plan_price)

        # Se logado, ir direto para criar empresa
        if request.user.is_authenticated:
            empresa = getattr(request.user, 'empresa', None)
            if not empresa and hasattr(request.user, 'empresas_permitidas'):
                empresa = request.user.empresas_permitidas.first()
            if empresa:
                return redirect('billing:billing-checkout-empresa', empresa.pk)
            return redirect('empresa-create')

        # Se não logado, ir para registro/login (com next setado)
        messages.info(request, f'Você selecionou o plano {plan.get_plan_type_display()}. Crie uma conta para continuar.')
        return redirect('register')


def _get_current_plan():
    """Busca o plano ativo mais recente da tabela PricingPlan."""
    return PricingPlan.objects.filter(active=True).order_by('sort_order', '-updated_at').first()


def _ensure_billing_customer(empresa: Empresa, email_fallback: Optional[str] = None) -> BillingCustomer:
    """Garante registro de billing para a empresa, preenchendo email se vazio."""
    billing, _ = BillingCustomer.objects.get_or_create(
        empresa=empresa,
        defaults={'email_cobranca': email_fallback, 'status': 'pending'},
    )

    if not billing.email_cobranca and email_fallback:
        billing.email_cobranca = email_fallback
        billing.save(update_fields=['email_cobranca'])

    return billing


def _first_email(empresa: Empresa) -> Optional[str]:
    if getattr(empresa, 'email', None):
        return empresa.email
    # Evita usar email genérico incorreto
    return None


def _resolve_plan_choice(
    request,
    billing_customer: BillingCustomer,
    persist_choice: bool = False,
    clear_session: bool = False,
):
    """Determina plano/valor usando sessão, plano salvo ou PricingPlan.

    - Usa seleção da sessão se presente (landing checkout)
    - Caso contrário, usa plano já vinculado ao billing_customer
    - Em último caso, usa PricingPlan ativo ou defaults
    - persist_choice: salva plano no billing_customer quando possível
    - clear_session: remove seleção da sessão após uso
    """

    selected_plan_type = request.session.get('selected_plan_type')
    selected_plan_price = request.session.get('selected_plan_price')

    plan_obj = None
    amount = DEFAULT_PLAN_VALUE
    periodicity = DEFAULT_PERIODICITY
    plan_name = 'Plano FGTS Web'

    if selected_plan_type:
        try:
            plan_obj = Plan.objects.get(plan_type=selected_plan_type, active=True)
            amount = PLAN_PRICE_OVERRIDE.get(plan_obj.plan_type, plan_obj.price_monthly)
            periodicity = 'MONTHLY'
            plan_name = f"Plano {plan_obj.get_plan_type_display()}"
            if persist_choice and billing_customer.plan_id != plan_obj.id:
                billing_customer.plan = plan_obj
                billing_customer.save(update_fields=['plan'])
        except Plan.DoesNotExist:
            if selected_plan_price:
                try:
                    amount = Decimal(selected_plan_price)
                except Exception:
                    amount = DEFAULT_PLAN_VALUE
            periodicity = 'MONTHLY'
            type_label = dict(Plan.PLAN_TYPES).get(selected_plan_type, selected_plan_type)
            plan_name = f"Plano {type_label}"

    if not plan_obj and billing_customer.plan:
        plan_obj = billing_customer.plan
        amount = PLAN_PRICE_OVERRIDE.get(plan_obj.plan_type, plan_obj.price_monthly)
        periodicity = 'MONTHLY'
        plan_name = f"Plano {plan_obj.get_plan_type_display()}"

    if not plan_obj:
        pricing_plan = _get_current_plan()
        if pricing_plan:
            amount = pricing_plan.amount
            periodicity = pricing_plan.periodicity
            plan_name = pricing_plan.description or pricing_plan.name or plan_name

    if clear_session:
        request.session.pop('selected_plan_type', None)
        request.session.pop('selected_plan_price', None)

    # Valor negociado individualmente tem prioridade máxima sobre qualquer outro
    if billing_customer.override_price is not None:
        amount = billing_customer.override_price

    return plan_obj, amount, periodicity, plan_name


@login_required
def checkout_empresa(request, empresa_id):
    empresa = get_object_or_404(Empresa, pk=empresa_id)

    # Escopo multi-tenant: usuário precisa ter permissão para esta empresa
    if not is_empresa_allowed(request.user, empresa.codigo):
        return HttpResponseBadRequest('Empresa não permitida para este usuário.')

    # Se GET, mostrar página de confirmação
    if request.method == 'GET':
        billing_customer = _ensure_billing_customer(empresa, email_fallback=_first_email(empresa))
        _, amount, periodicity, plan_name = _resolve_plan_choice(
            request,
            billing_customer,
            persist_choice=False,
            clear_session=False,
        )
        context = {
            'empresa': empresa,
            'billing_customer': billing_customer,
            'plan_name': plan_name,
            'amount': amount,
            'periodicity': periodicity,
        }
        return render(request, 'billing/checkout_empresa.html', context)

    # Se POST, processar pagamento
    if request.method != 'POST':
        return HttpResponseBadRequest('Método não suportado.')

    billing_customer = _ensure_billing_customer(empresa, email_fallback=_first_email(empresa))

    try:
        client = AsaasClient()

        # Cria cliente no Asaas se ainda não existir (com proteção contra race condition)
        if not billing_customer.asaas_customer_id:
            import re as _re
            cnpj_digits = _re.sub(r'\D', '', empresa.cnpj or '')
            fone_digits = _re.sub(r'\D', '', getattr(empresa, 'fone_contato', '') or '')
            customer_payload = {
                'name': empresa.nome,
                'cpfCnpj': cnpj_digits,
                'email': billing_customer.email_cobranca,
                'phone': fone_digits,
                'mobilePhone': fone_digits,
                'externalReference': str(empresa.pk),
            }
            created_customer = client.create_customer(customer_payload)
            asaas_cid = created_customer.get('id')
            if not asaas_cid:
                logger.error('Asaas não retornou ID de cliente. Resposta: %s', created_customer)
                raise ValueError('Asaas não retornou ID de cliente. Verifique os dados da empresa.')

            # Proteção contra race condition: usa update com filtro
            updated = BillingCustomer.objects.filter(
                pk=billing_customer.pk,
                asaas_customer_id__isnull=True,
            ).update(asaas_customer_id=asaas_cid, status='pending')

            if not updated:
                # Outro request já criou o customer -- recarrega do banco
                billing_customer.refresh_from_db()
            else:
                billing_customer.asaas_customer_id = asaas_cid
                billing_customer.status = 'pending'

        # Determinar plano e valor
        plan_obj, amount, periodicity, plan_name = _resolve_plan_choice(
            request,
            billing_customer,
            persist_choice=True,
            clear_session=True,
        )

        # Plano Enterprise (valor 0) não passa pelo checkout automático
        if amount <= 0:
            messages.info(request, 'O plano Enterprise é sob consulta. Entre em contato para contratar.')
            return HttpResponseRedirect(request.path)

        # Forma de pagamento escolhida pelo usuário (default: BOLETO)
        billing_type = request.POST.get('billing_type', 'BOLETO')
        if billing_type not in ('BOLETO', 'CREDIT_CARD', 'PIX'):
            billing_type = 'BOLETO'

        # Cria assinatura (o Asaas gera automaticamente o primeiro pagamento)
        due_date = timezone.now().date() + timedelta(days=3)
        subscription_payload = {
            'customer': billing_customer.asaas_customer_id,
            'billingType': billing_type,
            'value': float(amount),
            'cycle': periodicity,
            'description': plan_name,
            'nextDueDate': due_date.isoformat(),
        }
        subscription_resp = client.create_subscription(subscription_payload)
        subscription = Subscription.objects.create(
            customer=billing_customer,
            asaas_subscription_id=subscription_resp.get('id'),
            plan_name=plan_name,
            amount=amount,
            periodicity=periodicity,
            status='pending',
            next_due_date=due_date,
        )

        # Buscar o primeiro pagamento gerado automaticamente pela subscription
        first_payment_url = subscription_resp.get('invoiceUrl') or subscription_resp.get('bankSlipUrl') or ''
        first_payment_id = None

        # A API do Asaas retorna invoiceUrl na subscription; buscar payments se necessário
        try:
            payments_resp = client.list_payments(subscription_resp.get('id'))
            payments_data = payments_resp.get('data', [])
            if payments_data:
                first_payment = payments_data[0]
                first_payment_id = first_payment.get('id')
                first_payment_url = first_payment.get('invoiceUrl') or first_payment.get('bankSlipUrl') or first_payment_url
        except Exception:
            logger.warning('Não foi possível buscar payments da subscription %s', subscription_resp.get('id'))

        if first_payment_id:
            Payment.objects.create(
                subscription=subscription,
                asaas_payment_id=first_payment_id,
                amount=amount,
                due_date=due_date,
                status='pending',
                invoice_url=first_payment_url,
            )

        if first_payment_url:
            return HttpResponseRedirect(first_payment_url)

        return JsonResponse({'subscriptionId': subscription_resp.get('id')})

    except RequestException as exc:
        status = exc.response.status_code if getattr(exc, 'response', None) is not None else '?'
        detail = {}
        if getattr(exc, 'response', None) is not None:
            try:
                detail = exc.response.json()
            except Exception:
                detail = exc.response.text

        # Detecta customer inválido (ID antigo/ambiente errado) e limpa para nova tentativa
        errors = detail.get('errors', []) if isinstance(detail, dict) else []
        if any(e.get('code') == 'invalid_customer' for e in errors):
            BillingCustomer.objects.filter(pk=billing_customer.pk).update(asaas_customer_id=None)
            logger.warning('invalid_customer detectado para empresa %s — asaas_customer_id limpo.', empresa_id)
            messages.error(request, 'Dados de cobrança desatualizados. Por favor, tente novamente.')
        else:
            messages.error(request, f'Erro ao integrar com Asaas ({status}): {detail}')
            logger.exception('Erro na integração Asaas durante checkout_empresa')

        return HttpResponseRedirect(request.path)
    except Exception:
        logger.exception('Erro inesperado no checkout_empresa')
        messages.error(request, 'Erro inesperado ao processar pagamento. Tente novamente ou fale com o suporte.')
        return HttpResponseRedirect(request.path)


def _handle_bpo_webhook(asaas_payment_id, asaas_status):
    """Atualiza FaturaBPO e ContaBPO a partir de um evento de pagamento Asaas."""
    fatura = FaturaBPO.objects.select_related('conta_bpo').filter(
        asaas_payment_id=asaas_payment_id
    ).first()
    if not fatura:
        return HttpResponse('Pagamento não encontrado', status=200)

    local_status = ASAAS_PAYMENT_STATUS_MAP.get(asaas_status, fatura.status)
    fatura.status = local_status
    fatura.save(update_fields=['status', 'atualizado_em'])

    conta_bpo = fatura.conta_bpo
    if asaas_status in ASAAS_CONFIRMED_STATUSES:
        if conta_bpo.status != 'active':
            conta_bpo.status = 'active'
            conta_bpo.save(update_fields=['status', 'atualizado_em'])
    elif asaas_status in ASAAS_CANCELED_STATUSES:
        conta_bpo.status = 'suspended'
        conta_bpo.save(update_fields=['status', 'atualizado_em'])

    return HttpResponse('OK')


def _verify_webhook_token(request) -> bool:
    """Verifica token do webhook Asaas via header ou query param."""
    expected = os.getenv('ASAAS_WEBHOOK_TOKEN', '').strip()
    if not expected:
        logger.error('ASAAS_WEBHOOK_TOKEN não configurado -- webhook rejeitado por segurança!')
        return False
    token = request.headers.get('asaas-access-token', '') or request.GET.get('token', '')
    return token == expected


@csrf_exempt
def asaas_webhook(request):
    if request.method != 'POST':
        return HttpResponseBadRequest('Método não suportado')

    # Verificar autenticação do webhook
    if not _verify_webhook_token(request):
        logger.warning('Webhook Asaas recebido com token inválido de %s', request.META.get('REMOTE_ADDR'))
        return HttpResponseForbidden('Token inválido')

    try:
        data = json.loads(request.body.decode('utf-8'))
    except Exception:
        return HttpResponseBadRequest('JSON inválido')

    event = data.get('event') if isinstance(data, dict) else None
    payment_data = data.get('payment') if isinstance(data, dict) else None

    if not event or not payment_data:
        return HttpResponseBadRequest('Payload incompleto')

    asaas_payment_id = payment_data.get('id')
    asaas_status = payment_data.get('status')  # Status em UPPERCASE do Asaas
    paid_at = payment_data.get('paymentDate')

    try:
        payment = Payment.objects.select_related('subscription__customer').get(asaas_payment_id=asaas_payment_id)
    except Payment.DoesNotExist:
        return _handle_bpo_webhook(asaas_payment_id, asaas_status)

    # Mapear status Asaas (UPPERCASE) -> status local (lowercase)
    local_status = ASAAS_PAYMENT_STATUS_MAP.get(asaas_status)
    if local_status:
        payment.status = local_status
    else:
        logger.warning('Status Asaas desconhecido: %s (payment %s)', asaas_status, asaas_payment_id)

    if paid_at:
        try:
            payment.pay_date = timezone.datetime.fromisoformat(paid_at).date()
        except Exception:
            pass
    payment.save()

    # Atualizar status da subscription
    subscription = payment.subscription
    if asaas_status in ASAAS_CONFIRMED_STATUSES:
        subscription.status = 'active'
        subscription.save(update_fields=['status'])
    elif asaas_status in ASAAS_OVERDUE_STATUSES:
        subscription.status = 'overdue'
        subscription.save(update_fields=['status'])
    elif asaas_status in ASAAS_CANCELED_STATUSES:
        subscription.status = 'canceled'
        subscription.save(update_fields=['status'])

    # Atualizar status do billing customer
    billing_customer = subscription.customer
    if subscription.status == 'active':
        billing_customer.status = 'active'
    elif subscription.status in ['overdue', 'canceled']:
        billing_customer.status = 'pending'
    billing_customer.save(update_fields=['status'])

    return HttpResponse('OK')

# ===== FEEDBACK =====
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import CreateView, ListView
from .models import Feedback
from .forms import FeedbackForm
from fgtsweb.mixins import EmpresaScopeMixin


class FeedbackCreateView(LoginRequiredMixin, EmpresaScopeMixin, CreateView):
    """Criar novo feedback/sugestão/reclamação"""
    model = Feedback
    form_class = FeedbackForm
    template_name = 'billing/feedback_form.html'

    def form_valid(self, form):
        # Descobrir a empresa do usuário (multi-tenant seguro)
        # 1) empresa principal do usuário
        empresa_user = getattr(self.request.user, 'empresa', None)
        # 2) primeira empresa permitida (caso multiempresa)
        empresa_permitida = (
            self.request.user.empresas_permitidas.all().first()
            if hasattr(self.request.user, 'empresas_permitidas') else None
        )

        empresa = empresa_user or empresa_permitida

        if not empresa:
            messages.error(self.request, 'Você não tem empresa associada.')
            return redirect('dashboard')

        # Garantir escopo permitido
        if not is_empresa_allowed(self.request.user, empresa.codigo):
            messages.error(self.request, 'Empresa não permitida para este usuário.')
            return redirect('dashboard')

        form.instance.empresa = empresa

        response = super().form_valid(form)
        messages.success(self.request, 'Feedback enviado com sucesso! Obrigado pelas sugestões.')
        return response

    def get_success_url(self):
        return reverse('dashboard')


class FeedbackListView(LoginRequiredMixin, ListView):
    """Listar feedbacks do usuário (admin)"""
    model = Feedback
    template_name = 'billing/feedback_list.html'
    context_object_name = 'feedbacks'
    paginate_by = 20

    def get_queryset(self):
        if self.request.user.is_staff:
            return Feedback.objects.all()
        return Feedback.objects.none()
