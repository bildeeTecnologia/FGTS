from django.db import migrations

def populate_status(apps, schema_editor):
    """Popula o status baseado em data_demissao e motivo_saida"""
    FuncionarioVinculo = apps.get_model('empresas', 'FuncionarioVinculo')

    # Status = "transferido" onde motivo_saida == "transferencia"
    FuncionarioVinculo.objects.filter(
        motivo_saida='transferencia'
    ).update(status='transferido')

    # Status = "demitido" onde motivo_saida == "demissao" (ou data_demissao sem motivo claro)
    FuncionarioVinculo.objects.filter(
        data_demissao__isnull=False
    ).exclude(
        motivo_saida='transferencia'
    ).update(status='demitido')

    # Vínculos sem data_demissao já têm default='ativo', nada a fazer

def reverse_populate(apps, schema_editor):
    """Reverte para estado anterior (todos 'ativo' como padrão)"""
    FuncionarioVinculo = apps.get_model('empresas', 'FuncionarioVinculo')
    FuncionarioVinculo.objects.all().update(status='ativo')

class Migration(migrations.Migration):

    dependencies = [
        ('empresas', '0017_funcionariovinculo_status'),
    ]

    operations = [
        migrations.RunPython(populate_status, reverse_populate),
    ]
