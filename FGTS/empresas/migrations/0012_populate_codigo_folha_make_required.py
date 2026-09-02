from uuid import uuid4

from django.db import migrations, models


def _generate_codigo_folha(EmpresaModel):
    while True:
        codigo = f"CF{uuid4().hex[:8].upper()}"
        if not EmpresaModel.objects.filter(codigo_folha=codigo).exists():
            return codigo


def populate_codigo_folha(apps, schema_editor):
    Empresa = apps.get_model('empresas', 'Empresa')
    for empresa in Empresa.objects.filter(codigo_folha__isnull=True) | Empresa.objects.filter(codigo_folha=''):
        empresa.codigo_folha = _generate_codigo_folha(Empresa)
        empresa.save(update_fields=['codigo_folha'])


class Migration(migrations.Migration):

    dependencies = [
        ('empresas', '0011_empresa_codigo_folha'),
    ]

    operations = [
        migrations.RunPython(populate_codigo_folha, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='empresa',
            name='codigo_folha',
            field=models.CharField(max_length=30, verbose_name='Codigo Folha'),
        ),
    ]
