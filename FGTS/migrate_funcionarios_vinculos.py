# Script para migrar funcionários antigos para a nova tabela de vínculos ativos
# Execute este script uma única vez após a refatoração dos vínculos

from funcionarios.models import Funcionario, FuncionarioVinculo
from empresas.models import Empresa
from django.db import transaction

# Migra todos os funcionários que têm empresa_id preenchido e não possuem vínculo ativo

def run():
    with transaction.atomic():
        count = 0
        for funcionario in Funcionario.objects.all():
            # Se já tem vínculo ativo, pula
            if funcionario.vinculos.filter(data_demissao__isnull=True).exists():
                continue
            # Se tem empresa_id preenchido, cria vínculo ativo
            if hasattr(funcionario, 'empresa_id') and funcionario.empresa_id:
                empresa = Empresa.objects.filter(id=funcionario.empresa_id).first()
                if empresa:
                    FuncionarioVinculo.objects.create(
                        funcionario=funcionario,
                        empresa=empresa,
                        data_admissao=funcionario.data_nascimento or None,  # Ajuste se necessário
                        data_demissao=None
                    )
                    count += 1
        print(f"{count} vínculos ativos criados.")

if __name__ == "__main__":
    run()
