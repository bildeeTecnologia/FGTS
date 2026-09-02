from django.core.management.base import BaseCommand
from funcionarios.models import Funcionario
from empresas.models_grupo import FuncionarioVinculo
from empresas.models import Empresa
from django.db import transaction

class Command(BaseCommand):
    help = 'Migra funcionários antigos para a nova tabela de vínculos ativos.'

    def handle(self, *args, **options):
        with transaction.atomic():
            count = 0
            for funcionario in Funcionario.objects.all():
                # Se já tem qualquer vínculo, pula
                if funcionario.vinculos.exists():
                    continue
                # Se tem empresa_id preenchido, cria vínculo
                if hasattr(funcionario, 'empresa_id') and funcionario.empresa_id:
                    empresa = Empresa.objects.filter(id=funcionario.empresa_id).first()
                    if empresa:
                        FuncionarioVinculo.objects.create(
                            funcionario=funcionario,
                            empresa=empresa,
                            data_admissao=getattr(funcionario, 'data_admissao', None),
                            data_demissao=getattr(funcionario, 'data_demissao', None)
                        )
                        count += 1
            self.stdout.write(self.style.SUCCESS(f'{count} vínculos criados para funcionários sem vínculo.'))
