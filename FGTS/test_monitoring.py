"""
Script para testar o sistema de monitoramento
"""
import django
import os
import time
from datetime import datetime

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fgtsweb.settings')
django.setup()

from monitoring.models import PerformanceLog
from monitoring.services import PerformanceAnalyzer
from django.contrib.auth import get_user_model

User = get_user_model()

print("=" * 60)
print("TESTE DO SISTEMA DE MONITORAMENTO")
print("=" * 60)

# 1. Criar alguns logs de teste
print("\n1. Criando logs de teste...")
user = User.objects.first()

for i in range(5):
    PerformanceLog.objects.create(
        operacao='relatorio_competencia',
        status='sucesso',
        usuario=user,
        empresa_id=1,
        duracao_segundos=3.5 + i * 0.5,
        entrada_dados={'teste': f'log_{i}'},
        saida_dados={'resultado': 'ok'},
    )

print(f"✅ Criados 5 logs de teste")

# 2. Testar resumo de 24h
print("\n2. Testando resumo das últimas 24h...")
resumo = PerformanceAnalyzer.resumo_ultima_24h()
print(f"   Total de operações: {resumo['total_operacoes']}")
print(f"   Taxa de sucesso: {resumo['taxa_sucesso']}")
print(f"   Tempo médio: {resumo['tempo_medio']:.2f}s")
print(f"   Tempo máximo: {resumo['tempo_maximo']:.2f}s")

# 3. Testar top operações lentas
print("\n3. Top operações lentas...")
lentas = PerformanceAnalyzer.top_operacoes_lentas(limite=3)
for log in lentas:
    print(f"   - {log.get_operacao_display()}: {log.duracao_segundos}s")

# 4. Testar operações por tipo
print("\n4. Operações por tipo...")
por_tipo = PerformanceAnalyzer.operacoes_por_tipo()
for op in por_tipo:
    print(f"   - {op['operacao']}: {op['total']} execuções, média {op['tempo_medio']:.2f}s")

# 5. Verificar gargalos
print("\n5. Gargalos identificados...")
gargalos = PerformanceAnalyzer.gargalos_identifıcados()
if gargalos:
    for g in gargalos:
        print(f"   ⚠️  {g['operacao']}: {g['tempo_medio']:.2f}s médio, {g['percentual_lento']:.1f}% lentas")
else:
    print("   ✅ Nenhum gargalo identificado")

print("\n" + "=" * 60)
print("TESTE CONCLUÍDO COM SUCESSO!")
print("=" * 60)
print("\n📊 Dashboard disponível em: http://127.0.0.1:8000/monitoring/dashboard/")
print("   (Apenas para superusuários)")
