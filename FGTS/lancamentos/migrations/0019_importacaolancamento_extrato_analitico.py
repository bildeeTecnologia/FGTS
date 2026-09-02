from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lancamentos', '0018_relatorio_task'),
    ]

    operations = [
        migrations.AddField(
            model_name='importacaolancamento',
            name='extrato_analitico',
            field=models.BooleanField(
                default=False,
                help_text='Todos os lançamentos pagos desta importação serão marcados como confirmados pelo Extrato Analítico da CEF.',
                verbose_name='Extrato Analítico',
            ),
        ),
    ]
