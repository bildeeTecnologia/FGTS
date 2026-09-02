# Generated migration to add database indexes for CoefJam model

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('coefjam', '0001_initial'),
    ]

    operations = [
        # Índice crítico: competência (busca por mês/ano)
        migrations.AddIndex(
            model_name='coefjam',
            index=models.Index(fields=['competencia'], name='idx_coefjam_competencia'),
        ),
        # Índice composto: data_pagamento + competência (para ordenação e filtro)
        migrations.AddIndex(
            model_name='coefjam',
            index=models.Index(fields=['-data_pagamento', 'competencia'], name='idx_coefjam_data_comp'),
        ),
        # Índice para data_pagamento (ordenação decrescente, mais recentes primeiro)
        migrations.AddIndex(
            model_name='coefjam',
            index=models.Index(fields=['-data_pagamento'], name='idx_coefjam_data_desc'),
        ),
    ]
