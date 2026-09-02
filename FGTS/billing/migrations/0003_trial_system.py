# Generated migration for trial system

from django.db import migrations, models
from datetime import timedelta
from django.utils import timezone


def create_trial_for_existing(apps, schema_editor):
    """Cria trial para clientes existentes"""
    BillingCustomer = apps.get_model('billing', 'BillingCustomer')
    for customer in BillingCustomer.objects.filter(trial_expires__isnull=True):
        customer.trial_active = True
        customer.trial_expires = timezone.now().date() + timedelta(days=7)
        customer.status = 'trial'
        customer.save()


class Migration(migrations.Migration):

    dependencies = [
        ('billing', '0002_pricingplan'),
    ]

    operations = [
        migrations.AddField(
            model_name='billingcustomer',
            name='trial_active',
            field=models.BooleanField(default=True, verbose_name='Trial Ativo'),
        ),
        migrations.AddField(
            model_name='billingcustomer',
            name='trial_expires',
            field=models.DateField(blank=True, null=True, verbose_name='Trial Expira em'),
        ),
        migrations.AddField(
            model_name='billingcustomer',
            name='trial_used',
            field=models.BooleanField(default=False, verbose_name='Trial Já Utilizado'),
        ),
        migrations.AlterField(
            model_name='billingcustomer',
            name='status',
            field=models.CharField(choices=[('active', 'Ativo'), ('inactive', 'Inativo'), ('pending', 'Pendente'), ('trial', 'Trial'), ('canceled', 'Cancelado')], default='pending', max_length=20),
        ),
        migrations.RunPython(create_trial_for_existing),
    ]
