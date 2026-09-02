"""
Script para limpar lançamentos órfãos e verificar integridade
"""
import django
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fgtsweb.settings')
django.setup()

from lancamentos.models import Lancamento
from django.db.models import Q

print("=" * 60)
print("LIMPEZA DE LANÇAMENTOS ÓRFÃOS")
print("=" * 60)

# Verificar lançamentos órfãos
print("\n1. Verificando lançamentos órfãos...")
total_lancamentos = Lancamento.objects.count()
print(f"   Total de lançamentos: {total_lancamentos}")

# Buscar lançamentos sem funcionário válido
orfaos = []
for lanc in Lancamento.objects.all():
    try:
        # Tentar acessar funcionario
        _ = lanc.funcionario.nome
    except:
        orfaos.append(lanc.id)

print(f"   Lançamentos órfãos encontrados: {len(orfaos)}")

if orfaos:
    print("\n2. Deletando lançamentos órfãos...")
    Lancamento.objects.filter(id__in=orfaos).delete()
    print(f"   ✅ {len(orfaos)} lançamentos órfãos removidos!")
else:
    print("\n   ✅ Nenhum lançamento órfão encontrado!")

# Verificar lançamentos sem empresa válida
print("\n3. Verificando lançamentos sem empresa...")
orfaos_empresa = []
for lanc in Lancamento.objects.all():
    try:
        _ = lanc.empresa.nome
    except:
        orfaos_empresa.append(lanc.id)

if orfaos_empresa:
    print(f"   Lançamentos sem empresa: {len(orfaos_empresa)}")
    Lancamento.objects.filter(id__in=orfaos_empresa).delete()
    print(f"   ✅ {len(orfaos_empresa)} lançamentos sem empresa removidos!")
else:
    print("   ✅ Todos os lançamentos têm empresa válida!")

print("\n" + "=" * 60)
print("LIMPEZA CONCLUÍDA!")
print("=" * 60)

# Resumo final
print("\n📊 RESUMO FINAL:")
print(f"   Lançamentos após limpeza: {Lancamento.objects.count()}")
print(f"   Lançamentos removidos: {total_lancamentos - Lancamento.objects.count()}")
