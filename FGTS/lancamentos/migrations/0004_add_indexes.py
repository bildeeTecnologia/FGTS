# Generated migration to add database indexes for performance optimization

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lancamentos', '0003_lancamento_pago_em_alter_lancamento_data_pagto_and_more'),
    ]

    operations = [
        # Índices críticos para queries frequentes
        migrations.AddIndex(
            model_name='lancamento',
            index=models.Index(fields=['empresa_id', 'competencia', 'pago'], name='idx_lancamento_empresa_comp_pago'),
        ),
        migrations.AddIndex(
            model_name='lancamento',
            index=models.Index(fields=['empresa_id', 'pago'], name='idx_lancamento_empresa_pago'),
        ),
        migrations.AddIndex(
            model_name='lancamento',
            index=models.Index(fields=['competencia', 'pago'], name='idx_lancamento_competencia_pago'),
        ),
        migrations.AddIndex(
            model_name='lancamento',
            index=models.Index(fields=['funcionario_id', 'competencia'], name='idx_lancamento_func_competencia'),
        ),
        migrations.AddIndex(
            model_name='lancamento',
            index=models.Index(fields=['funcionario_id', 'criado_em'], name='idx_lancamento_func_criado'),
        ),
        migrations.AddIndex(
            model_name='lancamento',
            index=models.Index(fields=['empresa_id', 'funcionario_id'], name='idx_lancamento_empresa_func'),
        ),
        # Índice simples para competência (campo de busca frequente)
        migrations.AddIndex(
            model_name='lancamento',
            index=models.Index(fields=['competencia'], name='idx_lancamento_competencia'),
        ),
        # Índice para status de pagamento (filtro comum)
        migrations.AddIndex(
            model_name='lancamento',
            index=models.Index(fields=['pago'], name='idx_lancamento_pago'),
        ),
    ]
