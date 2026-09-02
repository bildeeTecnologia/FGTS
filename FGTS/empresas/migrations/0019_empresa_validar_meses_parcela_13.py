from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('empresas', '0018_populate_vinculo_status'),
    ]

    operations = [
        migrations.AddField(
            model_name='empresa',
            name='validar_meses_parcela_13',
            field=models.BooleanField(
                default=True,
                verbose_name='Validar meses das parcelas do 13º?',
                help_text='Se marcado, a importação exige que as parcelas do 13º sejam nos meses esperados (novembro/dezembro ou aniversário/dezembro). Desmarque para empresas que pagam o 13º em meses diferentes.',
            ),
        ),
    ]
