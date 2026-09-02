"""Middleware para verificação e exibição de avisos de trial"""

from datetime import date
import logging
from django.shortcuts import redirect
from django.contrib import messages
from billing.models import BillingCustomer


logger = logging.getLogger(__name__)

# Caminhos que nunca devem ser redirecionados (billing, autenticação, assets)
_BYPASS_PATHS = ('/admin/', '/static/', '/media/', '/billing/', '/accounts/')


def _path_is_public(path):
    return any(path.startswith(p) for p in _BYPASS_PATHS)


class TrialWarningMiddleware:
    """
    Middleware que:
    1. Verifica trial/status de contas regulares (BillingCustomer)
    2. Verifica trial/status de contas BPO (ContaBPO)
    3. Bloqueia acesso a empresa gerenciada por BPO quando o escritório está suspenso
    4. Bloqueia acesso de clientes quando permite_acesso_cliente=False
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path.startswith('/admin/') or request.path.startswith('/static/') or request.path.startswith('/media/'):
            return self.get_response(request)

        if request.user.is_authenticated:
            try:
                response = self._verificar_acesso(request)
                if response:
                    return response
            except Exception:
                logger.exception('Erro no TrialWarningMiddleware')

        return self.get_response(request)

    def _verificar_acesso(self, request):
        empresa_id = getattr(request.user, 'empresa_id', None)
        if not empresa_id:
            return None

        # Tenta pegar o BillingCustomer da empresa principal do usuário
        billing_customer = BillingCustomer.objects.filter(empresa_id=empresa_id).first()

        if not billing_customer:
            return None

        # ── Caso 1: Empresa é gerenciada por BPO ──────────────────────────────
        conta_bpo = getattr(billing_customer, 'gerenciada_por_bpo', None)
        if conta_bpo:
            return self._verificar_empresa_gerenciada(request, billing_customer, conta_bpo)

        # ── Caso 2: Empresa é o próprio escritório BPO ────────────────────────
        try:
            conta_bpo_proprio = billing_customer.empresa.conta_bpo
            return self._verificar_conta_bpo(request, conta_bpo_proprio)
        except Exception:
            pass

        # ── Caso 3: Cliente regular ───────────────────────────────────────────
        return self._verificar_trial_regular(request, billing_customer)

    def _verificar_trial_regular(self, request, billing_customer):
        """Verifica trial para clientes regulares (não BPO)."""
        request.trial_customer = billing_customer

        if billing_customer.trial_active and billing_customer.trial_expires:
            if date.today() > billing_customer.trial_expires:
                billing_customer.trial_active = False
                billing_customer.status = 'pending'
                billing_customer.save(update_fields=['trial_active', 'status', 'updated_at'])

                if not _path_is_public(request.path):
                    messages.error(
                        request,
                        '❌ Seu trial de 7 dias expirou! Assine um plano para continuar.'
                    )
                    return redirect('billing:checkout-plano')
        return None

    def _verificar_conta_bpo(self, request, conta_bpo):
        """Verifica trial e status para operadores do escritório BPO."""
        if conta_bpo.trial_ativo and conta_bpo.trial_expira:
            if date.today() > conta_bpo.trial_expira:
                conta_bpo.trial_ativo = False
                conta_bpo.status = 'suspended'
                conta_bpo.save(update_fields=['trial_ativo', 'status', 'atualizado_em'])

                if not _path_is_public(request.path):
                    messages.error(
                        request,
                        '❌ Seu trial BPO expirou! Configure o pagamento para continuar usando a plataforma.'
                    )
                    return redirect('billing:bpo-checkout')

        if conta_bpo.status == 'suspended' and not _path_is_public(request.path):
            messages.error(
                request,
                '⚠️ Sua conta BPO está suspensa. Configure o pagamento ou entre em contato com o suporte.'
            )
            return redirect('billing:bpo-checkout')

        return None

    def _verificar_empresa_gerenciada(self, request, billing_customer, conta_bpo):
        """
        Verifica acesso para usuários de empresas gerenciadas por BPO.
        - Bloqueia se o BPO estiver suspenso/cancelado
        - Bloqueia se permite_acesso_cliente=False
        """
        if _path_is_public(request.path):
            return None

        # Verifica se o cliente tem permissão para acessar
        try:
            empresa_bpo = billing_customer.empresa.empresa_bpo
            if not empresa_bpo.permite_acesso_cliente:
                messages.error(
                    request,
                    '🔒 O acesso desta empresa está configurado apenas para o escritório BPO responsável.'
                )
                from django.contrib.auth import logout
                logout(request)
                return redirect('login')
        except Exception:
            pass

        # Verifica status do BPO responsável
        if conta_bpo.status in ('suspended', 'canceled'):
            messages.error(
                request,
                '⚠️ O escritório BPO responsável por esta empresa está com acesso suspenso.'
            )
            return redirect('login')

        return None

