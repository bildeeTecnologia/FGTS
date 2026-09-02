import logging

from .models import PricingPlan


logger = logging.getLogger(__name__)


def current_pricing(request):
    try:
        plan = PricingPlan.objects.filter(active=True).order_by('sort_order', '-updated_at').first()
    except Exception:
        # Nunca quebrar template (inclui Django Admin) por falha de billing
        logger.exception('Falha ao buscar PricingPlan ativo no context_processor')
        plan = None

    return {'current_plan': plan}


def conta_bpo_context(request):
    """
    Injeta `conta_bpo` em todos os templates.
    Usado no sidebar para exibir o link do Painel BPO apenas para escritórios BPO.
    """
    if not getattr(request, 'user', None) or not request.user.is_authenticated:
        return {'conta_bpo': None}

    try:
        from .models_bpo import ContaBPO
        empresa_id = getattr(request.user, 'empresa_id', None)
        if not empresa_id:
            return {'conta_bpo': None}
        conta_bpo = ContaBPO.objects.filter(empresa_bpo_id=empresa_id).first()
        return {'conta_bpo': conta_bpo}
    except Exception:
        logger.exception('Falha ao buscar ContaBPO no context_processor')
        return {'conta_bpo': None}
