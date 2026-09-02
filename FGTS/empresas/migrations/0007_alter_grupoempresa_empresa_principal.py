from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('empresas', '0006_grupoempresa_empresa_principal'),
    ]

    operations = [
        migrations.AlterField(
            model_name='grupoempresa',
            name='empresa_principal',
            field=models.OneToOneField(
                on_delete=django.db.models.deletion.PROTECT,
                blank=True,
                null=True,
                related_name='grupo_principal',
                to='empresas.empresa',
                verbose_name='Empresa principal do grupo',
                help_text='Define a empresa proprietária/raiz do grupo para escopo e isolamento.',
            ),
        ),
    ]
