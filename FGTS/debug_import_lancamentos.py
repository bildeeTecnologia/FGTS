"""
Script para debugar importação de lançamentos
"""
import django
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fgtsweb.settings')
django.setup()

from lancamentos.models import Lancamento
from empresas.models import Empresa
from funcionarios.models import Funcionario

print("=" * 60)
print("DEBUG: IMPORTAÇÃO DE LANÇAMENTOS")
print("=" * 60)

# 1. Verificar empresas
print("\n1. EMPRESAS DISPONÍVEIS:")
empresas = Empresa.objects.all()
for emp in empresas[:5]:
    print(f"   - [{emp.codigo}] {emp.nome}")
print(f"   Total: {empresas.count()} empresas")

# 2. Verificar funcionários
print("\n2. FUNCIONÁRIOS CADASTRADOS:")
funcionarios = Funcionario.objects.all()
if funcionarios.exists():
    print(f"   Total: {funcionarios.count()} funcionários")
    for func in funcionarios[:5]:
        print(f"   - CPF {func.cpf}: {func.nome} (Empresa: {func.empresa.nome})")
else:
    print("   ⚠️ NENHUM FUNCIONÁRIO CADASTRADO!")

# 3. Verificar lançamentos existentes
print("\n3. LANÇAMENTOS EXISTENTES:")
lancamentos = Lancamento.objects.all()
if lancamentos.exists():
    print(f"   Total: {lancamentos.count()} lançamentos")
    for lanc in lancamentos[:5]:
        print(f"   - {lanc.funcionario.nome} | {lanc.competencia} | R$ {lanc.base_fgts}")
else:
    print("   ℹ️ Nenhum lançamento cadastrado ainda")

# 4. Verificar estrutura do modelo Lancamento
print("\n4. CAMPOS DO MODELO LANCAMENTO:")
from django.db import connection
with connection.cursor() as cursor:
    cursor.execute("""
        SELECT column_name, data_type, is_nullable
        FROM information_schema.columns 
        WHERE table_name = 'lancamentos_lancamento'
        ORDER BY ordinal_position;
    """)
    columns = cursor.fetchall()
    for col in columns:
        print(f"   - {col[0]}: {col[1]} (nullable: {col[2]})")

print("\n" + "=" * 60)
print("DEBUG CONCLUÍDO")
print("=" * 60)
