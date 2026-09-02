"""
Criar BillingCustomer em trial para Empresa A
"""
import django
import os
from datetime import timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fgtsweb.settings')
django.setup()

from django.utils import timezone
from empresas.models import Empresa
from billing.models import BillingCustomer, Plan

print("=" * 60)
print("CRIANDO BILLING PARA EMPRESA A")
print("=" * 60)

try:
    empresa_a = Empresa.objects.get(nome__icontains='Empresa A')
    print(f"\n✅ Empresa: {empresa_a.nome} (código {empresa_a.codigo})")
    
    # Verificar se já existe
    if BillingCustomer.objects.filter(empresa=empresa_a).exists():
        print("⚠️  BillingCustomer já existe!")
        bc = BillingCustomer.objects.get(empresa=empresa_a)
    else:
        # Obter plano trial (ou criar um básico)
        trial_plan = Plan.objects.filter(plan_type='BASIC').first()
        if not trial_plan:
            print("⚠️  Nenhum plano encontrado, criando plano básico...")
            trial_plan = Plan.objects.create(
                plan_type="BASIC",
                max_employees=50,
                has_pdf_export=True,
                has_advanced_dashboard=True,
                has_custom_reports=True,
                has_api=False,
                support_level='EMAIL'
            )
        
        # Criar BillingCustomer em trial
        now = timezone.now()
        bc = BillingCustomer.objects.create(
            empresa=empresa_a,
            plan=trial_plan,
            status='trial',
            trial_active=True,
            trial_expires=(now + timedelta(days=30)).date()
        )
        print(f"✅ BillingCustomer criado com sucesso!")
    
    print(f"\n📊 Status do Billing:")
    print(f"   Status: {bc.status} ({bc.get_status_display()})")
    print(f"   Plano: {bc.plan if bc.plan else 'Nenhum'}")
    print(f"   Trial Ativo: {bc.trial_active}")
    print(f"   Trial Expira: {bc.trial_expires}")
    
    print(f"\n🎉 Empresa A agora está em TRIAL!")
    print(f"   ✅ Pode importar lançamentos")
    print(f"   ✅ Sem limite de colaboradores")
    print(f"   ✅ Acesso total por 30 dias")
    
except Exception as e:
    print(f"\n❌ Erro: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
