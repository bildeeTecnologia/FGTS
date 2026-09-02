from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


def backfill_fonte_manual(apps, schema_editor):
    Lancamento = apps.get_model('lancamentos', 'Lancamento')
    Lancamento.objects.filter(pago=True, fonte_confirmacao_pagamento__isnull=True).update(
        fonte_confirmacao_pagamento='manual'
    )


class Migration(migrations.Migration):

    dependencies = [
        ('lancamentos', '0015_add_performance_indexes'),
        ('empresas', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='lancamento',
            name='fonte_confirmacao_pagamento',
            field=models.CharField(
                blank=True,
                choices=[
                    ('manual', 'Manual (não verificado)'),
                    ('extrato_analitico', 'Extrato Analítico CEF (confirmado)'),
                ],
                db_index=True,
                help_text='Como o pagamento foi confirmado: manualmente pelo usuário ou via Extrato Analítico da CEF.',
                max_length=20,
                null=True,
                verbose_name='Fonte de Confirmação',
            ),
        ),
        migrations.RunPython(backfill_fonte_manual, migrations.RunPython.noop),
        migrations.CreateModel(
            name='ImportacaoRE',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('arquivo', models.FileField(upload_to='importacoes/re/')),
                ('nome_arquivo', models.CharField(max_length=255)),
                ('tipo_fonte', models.CharField(
                    choices=[('re_texto', 'Arquivo .RE (texto)'), ('pdf', 'PDF visual SEFIP')],
                    max_length=20,
                )),
                ('status', models.CharField(
                    choices=[
                        ('preview', 'Aguardando confirmação'),
                        ('pending', 'Aguardando'),
                        ('processing', 'Processando'),
                        ('done', 'Concluído'),
                        ('error', 'Erro'),
                    ],
                    default='pending',
                    max_length=20,
                )),
                ('linhas_total', models.IntegerField(blank=True, null=True)),
                ('linhas_processadas', models.IntegerField(default=0)),
                ('resultado_json', models.JSONField(blank=True, null=True)),
                ('preview_resultado', models.JSONField(blank=True, null=True)),
                ('mensagem_erro', models.TextField(blank=True)),
                ('criado_em', models.DateTimeField(auto_now_add=True)),
                ('atualizado_em', models.DateTimeField(auto_now=True)),
                ('usuario', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='importacoes_re',
                    to=settings.AUTH_USER_MODEL,
                )),
                ('empresa', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    to='empresas.empresa',
                )),
            ],
            options={
                'verbose_name': 'Importação RE/SEFIP',
                'verbose_name_plural': 'Importações RE/SEFIP',
                'ordering': ['-criado_em'],
            },
        ),
        migrations.CreateModel(
            name='ImportacaoExtratoAnalitico',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('arquivo', models.FileField(upload_to='importacoes/extrato_analitico/')),
                ('nome_arquivo', models.CharField(max_length=255)),
                ('status', models.CharField(
                    choices=[
                        ('preview', 'Aguardando confirmação'),
                        ('pending', 'Aguardando'),
                        ('processing', 'Processando'),
                        ('done', 'Concluído'),
                        ('error', 'Erro'),
                    ],
                    default='pending',
                    max_length=20,
                )),
                ('linhas_total', models.IntegerField(blank=True, null=True)),
                ('linhas_processadas', models.IntegerField(default=0)),
                ('resultado_json', models.JSONField(blank=True, null=True)),
                ('preview_resultado', models.JSONField(blank=True, null=True)),
                ('mensagem_erro', models.TextField(blank=True)),
                ('criado_em', models.DateTimeField(auto_now_add=True)),
                ('atualizado_em', models.DateTimeField(auto_now=True)),
                ('usuario', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='importacoes_extrato',
                    to=settings.AUTH_USER_MODEL,
                )),
                ('empresa', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    to='empresas.empresa',
                )),
            ],
            options={
                'verbose_name': 'Importação Extrato Analítico',
                'verbose_name_plural': 'Importações Extrato Analítico',
                'ordering': ['-criado_em'],
            },
        ),
    ]
