from decimal import Decimal
from django.db import migrations, models
import django.db.models.deletion


def seed_tipos_vinculo(apps, schema_editor):
    TipoVinculo = apps.get_model('empresas', 'TipoVinculo')
    TipoVinculo.objects.bulk_create([
        TipoVinculo(codigo='CLT', descricao='CLT', percentual_fgts=Decimal('8.00'), ativo=True),
        TipoVinculo(codigo='APRENDIZ', descricao='Aprendiz', percentual_fgts=Decimal('2.00'), ativo=True),
    ])


def remove_tipos_vinculo(apps, schema_editor):
    TipoVinculo = apps.get_model('empresas', 'TipoVinculo')
    TipoVinculo.objects.filter(codigo__in=['CLT', 'APRENDIZ']).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('empresas', '0023_add_relatorio_posicao_fgts_feature'),
    ]

    operations = [
        migrations.CreateModel(
            name='TipoVinculo',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('codigo', models.CharField(max_length=20, unique=True, verbose_name='Código')),
                ('descricao', models.CharField(max_length=100, verbose_name='Descrição')),
                ('percentual_fgts', models.DecimalField(
                    decimal_places=2, max_digits=5,
                    verbose_name='Percentual FGTS (%)',
                    help_text='Ex: 8.00 para CLT, 2.00 para Aprendiz',
                )),
                ('ativo', models.BooleanField(default=True, verbose_name='Ativo')),
            ],
            options={
                'verbose_name': 'Tipo de vínculo',
                'verbose_name_plural': 'Tipos de vínculo',
                'ordering': ['codigo'],
            },
        ),
        migrations.RunPython(seed_tipos_vinculo, remove_tipos_vinculo),
        migrations.AddField(
            model_name='funcionariovinculo',
            name='tipo_vinculo',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='vinculos',
                to='empresas.tipovinculo',
                verbose_name='Tipo de vínculo',
                help_text='Nulo = CLT (8%). Altere apenas para corrigir cadastros incorretos; para efetivação de aprendiz crie um novo vínculo.',
            ),
        ),
    ]
