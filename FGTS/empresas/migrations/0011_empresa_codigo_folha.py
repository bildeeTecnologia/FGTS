from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('empresas', '0010_alter_empresafeature_id_alter_funcionariovinculo_id_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='empresa',
            name='codigo_folha',
            field=models.CharField(blank=True, max_length=30, verbose_name='Codigo Folha'),
        ),
    ]
