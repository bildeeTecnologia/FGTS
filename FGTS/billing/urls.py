from django.urls import path
from .views import CheckoutPlanoView, checkout_empresa, asaas_webhook, FeedbackCreateView, FeedbackListView
from .views_bpo import (
    bpo_planos, bpo_ativar, bpo_checkout, bpo_dashboard, bpo_adicionar_empresa,
    bpo_remover_empresa, bpo_reativar_empresa, bpo_toggle_acesso, bpo_preview_rateio,
)

app_name = 'billing'

urlpatterns = [
    # Checkout público - selecionar plano (pricing page)
    path('pricing/', CheckoutPlanoView.as_view(), name='pricing'),
    path('checkout/', CheckoutPlanoView.as_view(), name='checkout-plano'),
    path('checkout/<str:plan_type>/', CheckoutPlanoView.as_view(), name='checkout-plano-tipo'),

    # Checkout para empresa (requer login)
    path('checkout-empresa/<int:empresa_id>/', checkout_empresa, name='billing-checkout-empresa'),

    # Feedback
    path('feedback/', FeedbackCreateView.as_view(), name='feedback-criar'),
    path('feedback/admin/', FeedbackListView.as_view(), name='feedback-admin'),

    # Webhook do Asaas
    path('webhook/', asaas_webhook, name='billing-webhook'),

    # ── BPO ──────────────────────────────────────────────────────────────────
    path('bpo/', bpo_dashboard, name='bpo-dashboard'),
    path('bpo/planos/', bpo_planos, name='bpo-planos'),
    path('bpo/ativar/', bpo_ativar, name='bpo-ativar'),
    path('bpo/checkout/', bpo_checkout, name='bpo-checkout'),
    path('bpo/empresas/adicionar/', bpo_adicionar_empresa, name='bpo-adicionar-empresa'),
    path('bpo/empresas/<int:empresa_bpo_id>/remover/', bpo_remover_empresa, name='bpo-remover-empresa'),
    path('bpo/empresas/<int:empresa_bpo_id>/reativar/', bpo_reativar_empresa, name='bpo-reativar-empresa'),
    path('bpo/empresas/<int:empresa_bpo_id>/acesso/', bpo_toggle_acesso, name='bpo-toggle-acesso'),
    path('bpo/api/preview-rateio/', bpo_preview_rateio, name='bpo-preview-rateio'),
]
