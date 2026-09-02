from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('funcionarios', '0004_alter_funcionario_id'),
    ]

    operations = [
        migrations.AlterField(
            model_name='funcionario',
            name='cpf',
            field=models.CharField(max_length=14, verbose_name='CPF'),
        ),
        # Removido migrations.RunSQL incompatível com SQLite
    ]
