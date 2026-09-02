from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('empresas', '0012_populate_codigo_folha_make_required'),
    ]

    operations = [
        migrations.AddField(
            model_name='empresafeature',
            name='gerar_sefip',
            field=models.BooleanField(default=False),
        ),
    ]
