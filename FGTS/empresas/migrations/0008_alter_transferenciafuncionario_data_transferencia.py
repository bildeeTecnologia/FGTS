from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('empresas', '0007_alter_grupoempresa_empresa_principal'),
    ]

    operations = [
        migrations.AlterField(
            model_name='transferenciafuncionario',
            name='data_transferencia',
            field=models.DateField(blank=True, null=True),
        ),
    ]
