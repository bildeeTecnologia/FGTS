# Generated manually: add empresa_principal ownership to GrupoEmpresa
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('empresas', '0005_grupoempresa_empresafeature_funcionariovinculo_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='grupoempresa',
            name='empresa_principal',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                to='empresas.empresa',
                null=True,
                blank=True,
                unique=True,
                related_name='grupo_principal',
                verbose_name='Empresa principal do grupo',
                help_text='Define a empresa proprietária/raiz do grupo para escopo e isolamento.',
            ),
        ),
    ]
