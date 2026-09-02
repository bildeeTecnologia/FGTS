# Generated migration for adding paga_13_aniversario field

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('empresas', '0002_alter_empresa_options_remove_empresa_id_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='empresa',
            name='paga_13_aniversario',
            field=models.BooleanField(default=False, help_text='Se marcado, a 1ª parcela do 13º será paga no mês de aniversário do colaborador (ao invés de novembro). A 2ª parcela continua sendo paga em dezembro.', verbose_name='Paga 1ª parcela do 13º no mês de aniversário?'),
        ),
    ]
