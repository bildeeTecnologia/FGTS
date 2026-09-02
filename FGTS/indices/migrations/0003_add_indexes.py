# Generated migration to add database indexes for Indice and SupabaseIndice models

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('indices', '0002_supabaseindice'),
    ]

    operations = [
        # SupabaseIndice indexes (tabela indices_fgts no Supabase)
        # Índice composto mais crítico: competência + data_base (busca exata)
        migrations.AddIndex(
            model_name='supabaseindice',
            index=models.Index(fields=['competencia', 'data_base'], name='idx_supabase_indice_comp_data'),
        ),
        # Índice para competência sozinha (busca por mês)
        migrations.AddIndex(
            model_name='supabaseindice',
            index=models.Index(fields=['competencia'], name='idx_supabase_indice_competencia'),
        ),
        # Índice para data_base (ordenação por data)
        migrations.AddIndex(
            model_name='supabaseindice',
            index=models.Index(fields=['-data_base'], name='idx_supabase_indice_data_desc'),
        ),
        # Índice composto com tabela (para filtros por tabela 6 ou 7)
        migrations.AddIndex(
            model_name='supabaseindice',
            index=models.Index(fields=['tabela', 'competencia'], name='idx_supabase_indice_tabela_comp'),
        ),
        
        # Indice model indexes (tabela local indices_indice)
        migrations.AddIndex(
            model_name='indice',
            index=models.Index(fields=['competencia'], name='idx_indice_competencia'),
        ),
        migrations.AddIndex(
            model_name='indice',
            index=models.Index(fields=['data_indice'], name='idx_indice_data'),
        ),
        migrations.AddIndex(
            model_name='indice',
            index=models.Index(fields=['competencia', 'data_indice'], name='idx_indice_comp_data'),
        ),
    ]
