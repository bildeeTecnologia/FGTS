"""
Script para criar dados de teste completos:
- Usuário admin
- Empresa com assinatura ativa
- Funcionário
- Lançamentos FGTS
"""
import os
import sys
import django
from datetime import date
from decimal import Decimal

# Configurar Django
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fgtsweb.settings')
django.setup()

from usuarios.models import Usuario
from empresas.models import Empresa
from funcionarios.models import Funcionario
from lancamentos.models import Lancamento
from billing.models import BillingCustomer, PricingPlan

def criar_dados():
    print("=== Criando dados de teste ===\n")
    
    # 1. Criar usuário admin
    username = "admin"
    email = "admin@fgts.com"
    password = "admin123"
    
    usuario, created = Usuario.objects.get_or_create(
        username=username,
        defaults={
            'email': email,
            'is_staff': True,
            'is_superuser': True,
        }
    )
    if created:
        usuario.set_password(password)
        usuario.save()
        print(f"✓ Usuário criado: {username} / {password}")
    else:
        print(f"✓ Usuário já existe: {username}")
    
    # 2. Criar empresa
    empresa, created = Empresa.objects.get_or_create(
        cnpj='12.345.678/0001-90',
        defaults={
            'nome': 'Empresa Teste LTDA',
            'endereco': 'Rua Teste, 123',
            'cidade': 'São Paulo',
            'uf': 'SP',
            'cep': '01234-567',
            'fone_contato': '(11) 1234-5678',
            'email': 'contato@empresateste.com.br',
        }
    )
    if created:
        print(f"✓ Empresa criada: {empresa.nome} (código: {empresa.codigo})")
    else:
        print(f"✓ Empresa já existe: {empresa.nome}")
    
    # 3. Criar assinatura ativa
    billing, created = BillingCustomer.objects.get_or_create(
        empresa=empresa,
        defaults={
            'asaas_customer_id': 'test_customer_123',
            'status': 'active',
        }
    )
    if created:
        print(f"✓ Assinatura ativa criada para {empresa.nome}")
    else:
        billing.status = 'active'
        billing.save()
        print(f"✓ Assinatura ativada para {empresa.nome}")
    
    # 4. Criar funcionário
    funcionario, created = Funcionario.objects.get_or_create(
        cpf='123.456.789-00',
        defaults={
            'empresa': empresa,
            'nome': 'João da Silva',
            'pis': '123.45678.90-1',
            'matricula': 'F001',
            'data_nascimento': date(1990, 1, 15),
            'data_admissao': date(2020, 1, 1),
        }
    )
    if created:
        print(f"✓ Funcionário criado: {funcionario.nome} (CPF: {funcionario.cpf})")
    else:
        print(f"✓ Funcionário já existe: {funcionario.nome}")
    
    # 5. Criar lançamentos FGTS para diferentes competências
    competencias = [
        ('01/2024', Decimal('280.00')),  # 8% de 3500
        ('02/2024', Decimal('280.00')),
        ('03/2024', Decimal('280.00')),
        ('04/2024', Decimal('280.00')),
        ('05/2024', Decimal('280.00')),
    ]
    
    for comp_str, valor in competencias:
        lanc, created = Lancamento.objects.get_or_create(
            empresa=empresa,
            funcionario=funcionario,
            competencia=comp_str,
            defaults={
                'base_fgts': Decimal('3500.00'),
                'valor_fgts': valor,
                'pago': False,
            }
        )
        if created:
            print(f"✓ Lançamento criado: {comp_str} - R$ {valor}")
        else:
            print(f"✓ Lançamento já existe: {comp_str}")
    
    # 6. Criar plano de preços (se não existir)
    plan, created = PricingPlan.objects.get_or_create(
        active=True,
        defaults={
            'name': 'Plano Mensal',
            'amount': Decimal('99.90'),
            'description': 'Acesso completo ao sistema FGTS',
            'periodicity': 'monthly',
        }
    )
    if created:
        print(f"✓ Plano de preços criado: {plan.name}")
    else:
        print(f"✓ Plano de preços já existe: {plan.name}")
    
    print("\n=== Dados de teste criados com sucesso! ===")
    print(f"\nPara testar o relatório:")
    print(f"1. Acesse: http://127.0.0.1:8000/login/")
    print(f"2. Login: {username} / {password}")
    print(f"3. Vá para: http://127.0.0.1:8000/lancamentos/relatorio/")
    print(f"4. Selecione:")
    print(f"   - Empresa: {empresa.nome}")
    print(f"   - Competência: 01/2024 (ou múltiplas)")
    print(f"   - Data de Pagamento: 27/12/2025 (hoje)")
    print(f"5. Clique em 'Gerar Relatório'")
    print(f"\nO sistema buscará índices do Supabase para calcular correção!")

if __name__ == '__main__':
    criar_dados()
