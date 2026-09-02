from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('billing', '0008_billingcustomer_override_limits'),
    ]

    operations = [
        migrations.AddField(
            model_name='plan',
            name='max_history_months',
            field=models.IntegerField(
                blank=True,
                null=True,
                help_text='Deixe em branco para histórico ilimitado',
                verbose_name='Máximo de Meses de Histórico',
            ),
        ),
        migrations.AddField(
            model_name='billingcustomer',
            name='override_max_history_months',
            field=models.IntegerField(
                blank=True,
                null=True,
                help_text='Se informado, substitui o limite de histórico do plano para esta empresa.',
                verbose_name='Limite especial de histórico (meses)',
            ),
        ),
    ]
