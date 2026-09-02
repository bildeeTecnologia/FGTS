# Generated manually: add max_companies to Plan
from django.db import migrations, models
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('billing', '0003_trial_system'),
    ]

    operations = [
        migrations.AddField(
            model_name='plan',
            name='max_companies',
            field=models.IntegerField(
                null=True,
                blank=True,
                verbose_name='Máximo de Empresas no Grupo',
                help_text='Deixe em branco para ilimitado'
            ),
        ),
    ]
