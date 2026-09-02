#!/usr/bin/env python
"""
Script de diagnóstico para JAM - Diagnóstico sem PSReadLine issues
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fgtsweb.settings')
django.setup()

from coefjam.models import CoefJam
from decimal import Decimal

print("="*80)
print("DIAGNÓSTICO JAM - Coeficientes Cadastrados")
print("="*80)

coefs = CoefJam.objects.all().order_by('competencia')
print(f"\nTotal de coeficientes: {coefs.count()}")
print()

if coefs.count() > 0:
    print("Primeiros 10 coeficientes:")
    for i, c in enumerate(coefs[:10], 1):
        print(f"{i:2}. competencia={c.competencia:8} | valor={str(c.valor):15} | data={c.data_pagamento}")
    print()

# Verificar as competências específicas que foram processadas
print("="*80)
print("Competências Processadas no Relatório (09/2025, 10/2025, 11/2025)")
print("="*80)

for mes_str in ['09/2025', '10/2025', '11/2025']:
    coef = CoefJam.objects.filter(competencia=mes_str).first()
    if coef:
        print(f"✓ {mes_str}: valor = {coef.valor} (tipo: {type(coef.valor).__name__})")
    else:
        print(f"✗ {mes_str}: NÃO ENCONTRADO NO BANCO")

print()
print("="*80)
print("ANÁLISE")
print("="*80)

# Verificar se valor está em escala correta
min_val = coefs.aggregate(models.Min('valor'))['valor__min'] if coefs.exists() else None
max_val = coefs.aggregate(models.Max('valor'))['valor__max'] if coefs.exists() else None

if min_val and max_val:
    print(f"Valor mínimo: {min_val}")
    print(f"Valor máximo: {max_val}")
    
    if float(min_val) > 0.1:
        print("\n⚠️  ALERTA: Valores parecem estar em escala ERRADA!")
        print("   Esperado: 0.00999 (valor < 1% = acumulado < 1 centavo por mês)")
        print(f"   Encontrado: {min_val} até {max_val}")
        print("\n   CAUSA PROVÁVEL: CoefJam foi importado com zeros faltando")
        print("   Ex: 0.00999 foi salvo como 0.999 ou similar")
    else:
        print("\n✓ Valores estão em escala correta (< 1%)")

print()

# Simulação do cálculo para diagnóstico
print("="*80)
print("SIMULAÇÃO: Cálculo JAM para 3 competências")
print("="*80)

# Assumir valor_fgts = 16 (8% de 200)
valor_fgts = Decimal('16.00')

# Buscar jam_coef para 09/2025
jam_coef_09 = CoefJam.objects.filter(competencia='09/2025').first()
jam_coef_09_val = jam_coef_09.valor if jam_coef_09 else Decimal('0')

# Simulação
acumulado = Decimal('0.00')
print(f"\nBase FGTS por mês: R$ 200,00 → valor_fgts = {valor_fgts}")
print(f"CoefJam (09/2025): {jam_coef_09_val}\n")

for mes in ['09', '10', '11']:
    competencia = f"{mes}/2025"
    if mes == '09':
        jam = Decimal('0.00')  # Primeira competência
        print(f"Mês {competencia} (PRIMEIRA): JAM = R$ 0,00")
    else:
        jam = (acumulado * jam_coef_09_val).quantize(Decimal('0.01'))
        print(f"Mês {competencia}: acumulado_anterior={acumulado} × coef={jam_coef_09_val} = JAM = R$ {jam}")
    
    acumulado = acumulado + jam + valor_fgts
    print(f"         → acumulado_novo = {acumulado}\n")

print("="*80)
print("TOTAL ACUMULADO (esperado ~R$ 50): R$", acumulado)
if acumulado > Decimal('1000'):
    print("⚠️  CRÍTICO: Acumulado está muito grande!")
print("="*80)
