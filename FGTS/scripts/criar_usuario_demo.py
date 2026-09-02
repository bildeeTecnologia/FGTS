"""
Script simples para criar usuário demo sem dependências externas.
Execute com: python scripts/criar_usuario_demo.py
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

from django.contrib.auth import get_user_model
from empresas.models import Empresa
from funcionarios.models import Funcionario
from lancamentos.models import Lancamento
from billing.models import BillingCustomer, Plan

Usuario = get_user_model()

print("\n" + "="*60)
print("🎯 CRIANDO LOGIN DEMO")
print("="*60 + "\n")

# 1. Criar usuário demo
print("1️⃣ Criando usuário demo...")
try:
    usuario = Usuario.objects.get(username='demo')
    print("   ⚠️  Usuário demo já existe!")
except Usuario.DoesNotExist:
    usuario = Usuario.objects.create_user(
        username='demo',
        email='demo@fgtsweb.com',
        password='demo123456',
        first_name='Cliente',
        last_name='Demo',
        is_active=True,
    )
    print("   ✅ Usuário criado!")

# 2. Criar empresa demo
print("\n2️⃣ Criando empresa demo...")
empresa = Empresa.objects.filter(cnpj='12.345.678/0001-99').first()

if not empresa:
    try:
        empresa = Empresa.objects.create(
            nome='Empresa Demo LTDA',
            cnpj='12.345.678/0001-99',
            nome_contato='João Silva',
            email='contato@empresademo.com.br',
            fone_contato='(11) 98765-4321',
            cep='01310-100',
            endereco='Avenida Paulista',
            numero='1000',
            bairro='Bela Vista',
            cidade='São Paulo',
            uf='SP',
        )
        print("   ✅ Empresa criada!")
    except Exception as e:
        print(f"   ❌ Erro: {e}")
        sys.exit(1)
else:
    print("   ⚠️  Empresa demo já existe!")

# Associar usuário à empresa
if usuario not in empresa.usuarios.all():
    empresa.usuarios.add(usuario)
    print("   ✅ Usuário associado à empresa")

# 3. Criar plano
print("\n3️⃣ Associando plano...")
plano = Plan.objects.filter(plan_type='PROFESSIONAL', active=True).first()
if not plano:
    plano = Plan.objects.filter(active=True).first()

if plano:
    billing, created = BillingCustomer.objects.get_or_create(
        empresa=empresa,
        defaults={
            'plan': plano,
            'email_cobranca': empresa.email,
            'status': 'active',
            'asaas_customer_id': 'demo-customer-id',
        }
    )
    if created or not billing.plan:
        if not billing.plan:
            billing.plan = plano
        billing.status = 'active'
        billing.save()
        print(f"   ✅ Plano {plano.get_plan_type_display()} associado")
else:
    print("   ⚠️  Nenhum plano disponível")

# 4. Criar funcionários
print("\n4️⃣ Criando funcionários demo...")
funcionarios_data = [
    {'nome': 'Maria Silva', 'cpf': '123.456.789-00'},
    {'nome': 'Carlos Santos', 'cpf': '234.567.890-11'},
    {'nome': 'Ana Oliveira', 'cpf': '345.678.901-22'},
    {'nome': 'Pedro Costa', 'cpf': '456.789.012-33'},
    {'nome': 'Fernanda Lima', 'cpf': '567.890.123-44'},
]

criados = 0
for info in funcionarios_data:
    func, created = Funcionario.objects.get_or_create(
        empresa=empresa,
        cpf=info['cpf'],
        defaults={
            'nome': info['nome'],
            'pis': f'10000000{info["cpf"][-4:]}',
            'data_admissao': date(2022, 1, 15),
        }
    )
    if created:
        criados += 1

if criados > 0:
    print(f"   ✅ {criados} colaboradores criados")
else:
    print(f"   ⚠️  Colaboradores já existem")

# 5. Criar lançamentos
print("\n5️⃣ Criando lançamentos demo...")
from datetime import timedelta
from random import randint

mes_atual = date.today()
lancamentos_criados = 0

# Salários bases realistas por funcionário
salarios_base = {
    'Maria Silva': Decimal('3853.00'),
    'Carlos Santos': Decimal('3099.00'),
    'Ana Oliveira': Decimal('4674.00'),
    'Pedro Costa': Decimal('2500.00'),
    'Fernanda Lima': Decimal('3200.00'),
}

for i in range(6):
    data_lancamento = mes_atual - timedelta(days=30 * i)
    competencia = data_lancamento.strftime('%m/%Y')
    
    for funcionario in Funcionario.objects.filter(empresa=empresa):
        try:
            # Buscar salário base do funcionário
            salario = salarios_base.get(funcionario.nome, Decimal('3500.00'))
            # FGTS = Salário × 8%
            fgts_valor = salario * Decimal('0.08')
            
            lancamento, created = Lancamento.objects.get_or_create(
                empresa=empresa,
                funcionario=funcionario,
                competencia=competencia,
                defaults={
                    'base_fgts': salario,  # Salário base
                    'valor_fgts': fgts_valor,  # 8% de FGTS
                    'data_pagto': None,
                    'pago': False,
                }
            )
            if created:
                lancamentos_criados += 1
        except Exception as e:
            print(f"   ⚠️  Erro ao criar lançamento: {e}")

if lancamentos_criados > 0:
    print(f"   ✅ {lancamentos_criados} lançamentos criados com cálculos corretos")
else:
    print(f"   ⚠️  Lançamentos já existem")

# Sucesso!
print("\n" + "="*60)
print("✅ DEMO CRIADO COM SUCESSO!")
print("="*60)
print("\n📝 Credenciais Demo:")
print("   Usuário: demo")
print("   Senha: demo123456")
print("\n🌐 Acesse: http://localhost:8000/login")
print("   ou: http://localhost:8000\n")
