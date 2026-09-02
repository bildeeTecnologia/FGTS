from datetime import date
from typing import Optional, Tuple

from billing.models import BillingCustomer
from empresas.models import Empresa

# Mapa de feature -> atributo do plano
FEATURE_PLAN_ATTR = {
    'advanced_dashboard': 'has_advanced_dashboard',
    'custom_reports': 'has_custom_reports',
    'pdf_export': 'has_pdf_export',
    'api': 'has_api',
}


def _resolve_empresa(user=None, empresa: Optional[Empresa] = None) -> Optional[Empresa]:
    if empresa:
        return empresa
    if user is None:
        return None
    if getattr(user, 'empresa', None):
        return user.empresa
    try:
        # Se o usuário tem uma única empresa permitida, usar como fallback
        if getattr(user, 'empresas_permitidas', None):
            empresas = list(user.empresas_permitidas.all()[:1])
            return empresas[0] if empresas else None
    except Exception:
        return None
    return None


def _trial_valid(bc: BillingCustomer) -> bool:
    if not bc.trial_active:
        return False
    if not bc.trial_expires:
        return False  # Sem data de expiração = trial inválido
    if date.today() > bc.trial_expires:
        return False
    return True


def can_use_feature(
    feature: str,
    user=None,
    empresa: Optional[Empresa] = None,
) -> Tuple[bool, Optional[str]]:
    """Determina se a empresa/usuário pode usar a feature solicitada.

    Regras:
    - superuser/staff sempre permitido
    - Trial: acesso total enquanto vigente (não aplica limite de funcionários aqui)
    - Plano ativo: precisa ter o atributo correspondente
    - Status pendente/inactive/canceled/expired: bloqueia
    """
    if user and (getattr(user, 'is_superuser', False) or getattr(user, 'is_staff', False)):
        return True, None

    empresa_resolvida = _resolve_empresa(user=user, empresa=empresa)
    if not empresa_resolvida:
        return False, 'Não foi possível identificar a empresa para validar o plano.'

    try:
        bc = BillingCustomer.objects.filter(empresa=empresa_resolvida).first()
    except Exception:
        bc = None

    if not bc:
        return False, 'Nenhum plano contratado para esta empresa.'

    # Trial full access, respeitando validade (limite de funcionários deve ser verificado na criação de colaboradores)
    if _trial_valid(bc):
        return True, None

    # Trial expirado
    if bc.trial_active and bc.trial_expires and date.today() > bc.trial_expires:
        return False, 'Trial expirado. Assine um plano para continuar.'

    # Plano ativo
    if bc.status == 'active' and bc.plan:
        plan_attr = FEATURE_PLAN_ATTR.get(feature)
        if not plan_attr:
            return False, 'Feature não mapeada no plano.'
        if getattr(bc.plan, plan_attr, False):
            return True, None
        return False, 'Seu plano atual não inclui esta funcionalidade.'

    # Outros status
    return False, 'Plano inativo ou pendente. Assine ou regularize para usar esta funcionalidade.'


def feature_block_context(feature: str, user=None, empresa: Optional[Empresa] = None):
    allowed, reason = can_use_feature(feature=feature, user=user, empresa=empresa)
    return {
        'feature_blocked': not allowed,
        'feature_block_reason': reason,
    }
