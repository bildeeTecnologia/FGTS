"""
Management command para enviar a sequencia de emails de leads (calculadora).

Uso:
    python manage.py send_lead_emails
    python manage.py send_lead_emails --dry-run
"""

from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone

from empresas.models_leads import LeadEmailFlow
from empresas.services_leads import EMAIL_STEPS, compute_next_send_at, send_lead_email


class Command(BaseCommand):
    help = 'Envia emails da sequencia de leads (calculadora)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simula o envio sem realmente enviar emails'
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        now = timezone.now()

        self.stdout.write("\n" + "=" * 72)
        self.stdout.write(
            self.style.WARNING(
                f"{'[SIMULACAO] ' if dry_run else ''}ENVIO DE EMAILS - LEADS CALCULADORA"
            )
        )
        self.stdout.write("=" * 72)
        self.stdout.write(f"\nData: {now.strftime('%d/%m/%Y %H:%M')}\n")

        leads = LeadEmailFlow.objects.filter(
            status=LeadEmailFlow.STATUS_ACTIVE,
            next_send_at__lte=now,
        ).order_by('next_send_at')

        self.stdout.write(f"Leads elegiveis: {leads.count()}\n")

        for lead in leads:
            if lead.step >= len(EMAIL_STEPS):
                lead.status = LeadEmailFlow.STATUS_COMPLETED
                lead.next_send_at = None
                lead.save(update_fields=['status', 'next_send_at', 'updated_at'])
                continue

            self.stdout.write(f"- Enviando etapa {lead.step + 1}/4 para {lead.email}")

            if dry_run:
                self.stdout.write(self.style.WARNING("  [DRY RUN] Email nao enviado"))
                continue

            try:
                send_lead_email(lead, lead.step)
            except Exception as exc:  # noqa: BLE001
                lead.status = LeadEmailFlow.STATUS_ERROR
                lead.last_error = str(exc)
                lead.error_count += 1
                lead.next_send_at = now + timedelta(days=1)
                lead.save(update_fields=['status', 'last_error', 'error_count', 'next_send_at', 'updated_at'])
                self.stdout.write(self.style.ERROR(f"  ERRO: {exc}"))
                continue

            lead.last_sent_at = now
            lead.last_error = None
            lead.error_count = 0
            lead.step += 1

            if lead.step >= len(EMAIL_STEPS):
                lead.status = LeadEmailFlow.STATUS_COMPLETED
                lead.next_send_at = None
            else:
                triggered_at = lead.triggered_at or lead.created_at or now
                lead.next_send_at = compute_next_send_at(triggered_at, lead.step)

            lead.save(update_fields=[
                'status',
                'step',
                'last_sent_at',
                'next_send_at',
                'last_error',
                'error_count',
                'updated_at',
            ])

            self.stdout.write(self.style.SUCCESS("  OK"))
