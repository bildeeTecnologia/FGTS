"""
Verificar status de billing da Empresa A
"""
import django
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fgtsweb.settings')
django.setup()

from empresas.models import Empresa
from billing.models import BillingCustomer

print("=" * 60)
print("VERIFICANDO EMPRESA A")
print("=" * 60)

try:
    empresa_a = Empresa.objects.get(nome__icontains='Empresa A')
    print(f"\n✅ Empresa encontrada:")
    print(f"   Código: {empresa_a.codigo}")
    print(f"   Nome: {empresa_a.nome}")
    print(f"   CNPJ: {empresa_a.cnpj}")
    
    # Verificar billing
    try:
        billing = BillingCustomer.objects.get(empresa=empresa_a)
        print(f"\n📊 Billing Customer:")
        print(f"   Status: {billing.status} ({billing.get_status_display()})")
        print(f"   Plano: {billing.plan.name if billing.plan else 'Nenhum'}")
        if billing.status == 'trial':
            print(f"   Trial Início: {billing.trial_start_date}")
            print(f"   Trial Fim: {billing.trial_end_date}")
            print(f"   Dias Restantes: {billing.trial_days_remaining}")
    except BillingCustomer.DoesNotExist:
        print(f"\n❌ PROBLEMA: Empresa A NÃO possui BillingCustomer cadastrado!")
        print(f"   Isso causa o erro que você está vendo.")
        
        # Verificar todas as empresas com billing
        print(f"\n📋 Empresas com billing configurado:")
        for bc in BillingCustomer.objects.all()[:10]:
            print(f"   - {bc.empresa.nome}: {bc.status}")
            
except Empresa.DoesNotExist:
    print("\n❌ Empresa A não encontrada!")
    print("\nEmpresas disponíveis:")
    for emp in Empresa.objects.all()[:10]:
        print(f"   - [{emp.codigo}] {emp.nome}")

print("\n" + "=" * 60)
