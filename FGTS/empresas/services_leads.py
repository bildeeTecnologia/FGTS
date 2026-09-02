from datetime import timedelta
from django.conf import settings
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.utils import timezone

from .models_leads import LeadEmailFlow


EMAIL_STEPS = [
    {
        'step': 0,
        'day_offset': 0,   # Imediato - no uso do 3º crédito
        'subject': 'Seu relatorio esta pronto',
        'template': 'empresas/email_lead_d0.html',
    },
    {
        'step': 1,
        'day_offset': 1,   # 24h após o trigger
        'subject': 'Os 3 erros mais comuns no FGTS',
        'template': 'empresas/email_lead_d2.html',
    },
    {
        'step': 2,
        'day_offset': 4,   # 96h (4 dias) após o trigger
        'subject': 'Menos retrabalho, mais controle',
        'template': 'empresas/email_lead_d5.html',
    },
    {
        'step': 3,
        'day_offset': 6,   # 144h (6 dias) após o trigger
        'subject': 'Ultimo dia para validar sem custo',
        'template': 'empresas/email_lead_d7.html',
    },
]


def _base_url() -> str:
    base_url = (getattr(settings, 'SITE_URL', None) or '').strip().rstrip('/')
    return base_url or 'http://localhost:8000'


def get_cta_url() -> str:
    return f"{_base_url()}/"


def register_credit_trigger(email: str) -> LeadEmailFlow:
    now = timezone.now()
    lead, created = LeadEmailFlow.objects.get_or_create(
        email=email,
        defaults={
            'trigger_source': LeadEmailFlow.TRIGGER_CREDITS,
            'triggered_at': now,
            'status': LeadEmailFlow.STATUS_ACTIVE,
            'step': 0,
            'next_send_at': now,
        },
    )

    if created:
        return lead

    if lead.status in [LeadEmailFlow.STATUS_COMPLETED, LeadEmailFlow.STATUS_PAUSED]:
        return lead

    lead.trigger_source = LeadEmailFlow.TRIGGER_CREDITS
    if lead.status == LeadEmailFlow.STATUS_ERROR:
        lead.status = LeadEmailFlow.STATUS_ACTIVE
    if not lead.next_send_at:
        lead.next_send_at = now
    lead.save(update_fields=['trigger_source', 'status', 'next_send_at', 'updated_at'])
    return lead


def compute_next_send_at(triggered_at, next_step: int):
    for config in EMAIL_STEPS:
        if config['step'] == next_step:
            return triggered_at + timedelta(days=config['day_offset'])
    return None


def send_lead_email(lead: LeadEmailFlow, step: int) -> None:
    config = next((item for item in EMAIL_STEPS if item['step'] == step), None)
    if not config:
        raise ValueError('Etapa de email invalida.')

    body = render_to_string(config['template'], {
        'cta_url': get_cta_url(),
    })

    msg = EmailMessage(
        config['subject'],
        body,
        settings.DEFAULT_FROM_EMAIL,
        [lead.email],
    )
    msg.content_subtype = 'html'
    msg.send()
