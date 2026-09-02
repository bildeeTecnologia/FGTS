"""
Comando para inicializar trials para clientes existentes
Execute com: python manage.py initialize_trials
"""

from django.core.management.base import BaseCommand
from datetime import date, timedelta
from billing.models import BillingCustomer


class Command(BaseCommand):
    help = 'Inicializa trial de 7 dias para todos os BillingCustomers existentes sem trial'

    def handle(self, *args, **options):
        updated = 0
        
        # Atualizar todos os BillingCustomers que não têm trial
        for customer in BillingCustomer.objects.filter(trial_expires__isnull=True):
            customer.trial_active = True
            customer.trial_expires = date.today() + timedelta(days=7)
            if customer.status == 'pending':
                customer.status = 'trial'
            customer.save()
            updated += 1
            self.stdout.write(
                self.style.SUCCESS(
                    f'✓ Trial ativado para {customer.empresa.nome} '
                    f'(vence em {customer.trial_expires.strftime("%d/%m/%Y")})'
                )
            )
        
        self.stdout.write(
            self.style.SUCCESS(f'\n✅ {updated} clientes atualizados com trial de 7 dias!')
        )
