"""
Envia previews dos templates de email para avaliação.

Uso:
  python manage.py enviar_previews_email seu@email.com

Observação:
- Este comando envia emails *de preview* e não depende de fluxos reais (cadastro, trial etc.).
- Atualmente o projeto possui 1 template HTML: confirmação de cadastro.
"""

from dataclasses import dataclass

from django.core.management.base import BaseCommand
from django.conf import settings

from emails.services import EmailService


@dataclass
class _PreviewUser:
    username: str
    first_name: str = ""
    last_name: str = ""

    def get_full_name(self) -> str:
        full_name = f"{self.first_name} {self.last_name}".strip()
        return full_name


class Command(BaseCommand):
    help = "Envia previews de templates de email (HTML)"

    def add_arguments(self, parser):
        parser.add_argument(
            "destinatario",
            type=str,
            help="Email do destinatário para receber os previews",
        )

    def handle(self, *args, **options):
        destinatario = options["destinatario"]

        base_url = (getattr(settings, "SITE_URL", None) or "").strip().rstrip("/")
        if not base_url:
            base_url = "http://localhost:8000"

        previews = [
            {
                "name": "confirm_email",
                "subject": "[PREVIEW] Confirmação de cadastro - FGTS Web",
                "template": "emails/confirm_email.html",
                "context": {
                    "user": _PreviewUser(username="usuario.teste", first_name="Usuário", last_name="Teste"),
                    "confirmation_link": f"{base_url}/usuario/confirmar-email/UID/TOKEN/",
                },
            }
        ]

        self.stdout.write(self.style.WARNING("\n📨 Enviando previews de templates..."))
        self.stdout.write(f"  Destinatário: {destinatario}")
        self.stdout.write(f"  SITE_URL: {base_url}")

        sent = 0
        for item in previews:
            self.stdout.write(self.style.WARNING(f"\n→ Template: {item['name']}") )
            ok = EmailService.enviar_email_html(
                assunto=item["subject"],
                template_html=item["template"],
                contexto=item["context"],
                destinatarios=[destinatario],
            )
            if ok:
                sent += 1
                self.stdout.write(self.style.SUCCESS("  ✅ Enviado"))
            else:
                self.stdout.write(self.style.ERROR("  ❌ Falha ao enviar"))

        self.stdout.write(self.style.SUCCESS(f"\n✅ Concluído. Total enviados: {sent}/{len(previews)}\n"))
