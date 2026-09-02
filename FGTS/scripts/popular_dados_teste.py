"""
Script para criar dados de teste completos para validação de relatórios e cálculos FGTS.
"""
import os
import sys
import django
from datetime import date, timedelta
from decimal import Decimal

# Configurar Django
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fgtsweb.settings')
django.setup()

from empresas.models import Empresa
from funcionarios.models import Funcionario
from lancamentos.models import Lancamento
from coefjam.models import CoefJam
from billing.models import BillingCustomer

def criar_dados_teste():
    print("=== Criando dados de teste para relatorios ===\n")
    
    # 1. Buscar empresas
    emp_a = Empresa.objects.get(cnpj='11.111.111/0001-11')
    emp_b = Empresa.objects.get(cnpj='22.222.222/0001-22')
    print(f"[OK] Empresas: {emp_a.nome}, {emp_b.nome}")
    
    # 2. Criar funcionários para Empresa A
    func_a1, created = Funcionario.objects.get_or_create(
        cpf='111.111.111-11',
        defaults={
            'empresa': emp_a,
            'nome': 'João da Silva',
            'matricula': '001',
            'pis': '123.45678.90-1',
            'data_admissao': date(2020, 1, 15),
        }
    )
    if created:
        print(f"  ✓ Funcionário criado: {func_a1.nome} (Empresa A)")
    
    func_a2, created = Funcionario.objects.get_or_create(
        cpf='222.222.222-22',
        defaults={
            'empresa': emp_a,
            'nome': 'Maria Santos',
            'matricula': '002',
            'pis': '234.56789.01-2',
            'data_admissao': date(2019, 6, 1),
        }
    )
    if created:
        print(f"  ✓ Funcionário criado: {func_a2.nome} (Empresa A)")
    
    # 3. Criar funcionários para Empresa B
    func_b1, created = Funcionario.objects.get_or_create(
        cpf='333.333.333-33',
        defaults={
            'empresa': emp_b,
            'nome': 'Carlos Oliveira',
            'matricula': '001',
            'pis': '345.67890.12-3',
            'data_admissao': date(2021, 3, 10),
        }
    )
    if created:
        print(f"  ✓ Funcionário criado: {func_b1.nome} (Empresa B)")
    
    # 4. ÍNDICES FGTS
    # ⚠️ IMPORTANTE: Os índices devem vir da tabela indices_fgts no Supabase.
    # Este script NÃO cria índices locais. O sistema busca automaticamente da tabela correta.
    print("\n[INFO] Índices FGTS: utilizando tabela 'indices_fgts' do Supabase")
    print("       (não é necessário popular índices localmente)")
    
    # 5. Criar coeficientes JAM
    coef_jam_data = [
        # (competencia, data_pagamento, coeficiente)
        ('01/2023', date(2023, 2, 7), Decimal('0.0120')),
        ('02/2023', date(2023, 3, 7), Decimal('0.0118')),
        ('03/2023', date(2023, 4, 7), Decimal('0.0115')),
        ('04/2023', date(2023, 5, 7), Decimal('0.0112')),
        ('05/2023', date(2023, 6, 7), Decimal('0.0110')),
        ('06/2023', date(2023, 7, 7), Decimal('0.0108')),
        ('07/2023', date(2023, 8, 7), Decimal('0.0105')),
        ('08/2023', date(2023, 9, 7), Decimal('0.0102')),
        ('09/2023', date(2023, 10, 7), Decimal('0.0100')),
        ('10/2023', date(2023, 11, 7), Decimal('0.0098')),
        ('11/2023', date(2023, 12, 7), Decimal('0.0095')),
        ('12/2023', date(2024, 1, 7), Decimal('0.0092')),
        ('01/2024', date(2024, 2, 7), Decimal('0.0090')),
        ('02/2024', date(2024, 3, 7), Decimal('0.0088')),
        ('03/2024', date(2024, 4, 7), Decimal('0.0085')),
        ('04/2024', date(2024, 5, 7), Decimal('0.0082')),
        ('05/2024', date(2024, 6, 7), Decimal('0.0080')),
    ]
    
    for competencia, data_pag, coef in coef_jam_data:
        jam, created = CoefJam.objects.get_or_create(
            competencia=competencia,
            defaults={
                'data_pagamento': data_pag,
                'valor': coef
            }
        )
        if created:
            print(f"  ✓ CoefJam criado: {competencia} = {coef}")
    
    print(f"\n✓ Total de coeficientes JAM: {CoefJam.objects.count()}")
    
    # 6. Criar lançamentos FGTS
    lancamentos_data = [
        # Empresa A - Funcionário 1
        (emp_a, func_a1, '01/2023', Decimal('1200.00'), Decimal('96.00'), False, None, None),
        (emp_a, func_a1, '02/2023', Decimal('1200.00'), Decimal('96.00'), False, None, None),
        (emp_a, func_a1, '03/2023', Decimal('1200.00'), Decimal('96.00'), False, None, None),
        (emp_a, func_a1, '04/2023', Decimal('1350.00'), Decimal('108.00'), False, None, None),
        (emp_a, func_a1, '05/2023', Decimal('1350.00'), Decimal('108.00'), False, None, None),
        
        # Empresa A - Funcionário 2
        (emp_a, func_a2, '01/2023', Decimal('2500.00'), Decimal('200.00'), False, None, None),
        (emp_a, func_a2, '02/2023', Decimal('2500.00'), Decimal('200.00'), False, None, None),
        (emp_a, func_a2, '03/2023', Decimal('2500.00'), Decimal('200.00'), False, None, None),
        
        # Empresa B - Funcionário 1
        (emp_b, func_b1, '03/2024', Decimal('1800.00'), Decimal('144.00'), False, None, None),
        (emp_b, func_b1, '04/2024', Decimal('1800.00'), Decimal('144.00'), False, None, None),
        (emp_b, func_b1, '05/2024', Decimal('1800.00'), Decimal('144.00'), False, None, None),
    ]
    
    for empresa, funcionario, competencia, base_fgts, valor_fgts, pago, data_pag, valor_pago in lancamentos_data:
        lanc, created = Lancamento.objects.get_or_create(
            empresa=empresa,
            funcionario=funcionario,
            competencia=competencia,
            defaults={
                'base_fgts': base_fgts,
                'valor_fgts': valor_fgts,
                'pago': pago,
                'data_pagto': data_pag,
                'valor_pago': valor_pago,
            }
        )
        if created:
            print(f"  ✓ Lançamento criado: {funcionario.nome} - {competencia} = R$ {valor_fgts}")
    
    print(f"\n✓ Total de lançamentos: {Lancamento.objects.count()}")
    
    print("\n" + "="*60)
    print("✅ DADOS DE TESTE CRIADOS COM SUCESSO!")
    print("="*60)
    print("\n📊 RESUMO:")
    print(f"  • Empresas: {Empresa.objects.count()}")
    print(f"  • Funcionários: {Funcionario.objects.count()}")
    print(f"  • Lançamentos: {Lancamento.objects.count()}")
    print(f"  • Coeficientes JAM: {CoefJam.objects.count()}")
    print(f"  • Índices FGTS: utilizando tabela 'indices_fgts' do Supabase")
    
    print("\n🧪 COMO TESTAR:")
    print("  1. IMPORTANTE: Certifique-se que 'indices_fgts' no Supabase está populada")
    print("  2. Faça login com: user_a / teste123 (verá apenas Empresa A)")
    print("  3. Faça login com: gestor_multi / teste123 (verá ambas empresas)")
    print("  4. Acesse: http://127.0.0.1:8000/lancamentos/relatorio/")
    print("  5. Selecione empresa, competência (ex: 01/2023) e data pagamento (ex: 30/12/2025)")
    print("  6. Confira os valores calculados (corrigido, JAM, total)")
    print("\n📝 COMPETÊNCIAS DISPONÍVEIS PARA TESTE:")
    print("  Empresa A: 01/2023, 02/2023, 03/2023, 04/2023, 05/2023")
    print("  Empresa B: 03/2024, 04/2024, 05/2024")

if __name__ == '__main__':
    criar_dados_teste()
