from django.conf import settings
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils import timezone
from django.contrib.auth.tokens import default_token_generator
from django.shortcuts import redirect
from emails.services import EmailService
from .models import Usuario


def build_confirmation_link(user, request=None) -> str:
    """Gera link absoluto para confirmação de email."""
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    path = reverse('confirm-email', kwargs={'uidb64': uid, 'token': token})
    if request:
        return request.build_absolute_uri(path)
    base_url = (getattr(settings, 'SITE_URL', None) or '').strip().rstrip('/')
    if not base_url:
        if settings.ALLOWED_HOSTS:
            host = (settings.ALLOWED_HOSTS[0] or '').strip()
            if host and host != '*':
                base_url = host.rstrip('/')
    if base_url and not (base_url.startswith('http://') or base_url.startswith('https://')):
        base_url = f"https://{base_url}"
    if not base_url:
        base_url = 'http://localhost:8000'
    return f"{base_url}{path}"


def send_email_confirmation(user: Usuario, request=None) -> bool:
    """Envia email de confirmação de cadastro."""
    if not user.email:
        return False
    link = build_confirmation_link(user, request)
    context = {
        'user': user,
        'confirmation_link': link,
    }
    subject = 'Confirme seu cadastro - FGTS Web'
    return EmailService.enviar_email_html(
        assunto=subject,
        template_html='emails/confirm_email.html',
        contexto=context,
        destinatarios=[user.email],
    )


def confirm_user_email(uidb64: str, token: str):
    """Valida token e confirma o email do usuário.

    Returns:
        (success: bool, user: Usuario | None)
    """
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = Usuario.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, Usuario.DoesNotExist):
        return False, None

    if default_token_generator.check_token(user, token):
        if not user.email_confirmed:
            user.email_confirmed = True
            user.email_confirmed_at = timezone.now()
            user.save(update_fields=['email_confirmed', 'email_confirmed_at'])
        return True, user
    return False, None
