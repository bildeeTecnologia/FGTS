import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fgtsweb.settings')
django.setup()

from empresas.models import Empresa
from billing.models import BillingCustomer, Plan
from datetime import date, timedelta

# Buscar Empresa A
empresa = Empresa.objects.filter(nome__icontains='Empresa A').first()
if not empresa:
    print("❌ Empresa A não encontrada")
    exit(1)

print(f"✅ Empresa encontrada: {empresa.nome} (Código: {empresa.codigo})")

# Verificar BillingCustomer
billing = BillingCustomer.objects.filter(empresa=empresa).first()
if billing:
    print(f"📋 BillingCustomer existente:")
    print(f"   Status: {billing.status}")
    print(f"   Plan: {billing.plan}")
    print(f"   Trial Active: {billing.trial_active}")
    print(f"   Trial Expires: {billing.trial_expires}")
else:
    print("⚠️  BillingCustomer não existe")

# Buscar ou criar um plano básico
plan = Plan.objects.filter(plan_type='BASIC', active=True).first()
if not plan:
    print("⚠️  Criando plano BASIC...")
    plan = Plan.objects.create(
        plan_type='BASIC',
        max_employees=50,
        price_monthly=99.00,
        price_yearly=990.00,
        active=True,
        has_advanced_dashboard=False,
        has_custom_reports=False,
        has_pdf_export=True,
        has_api=False,
        support_level='EMAIL'
    )
    print(f"✅ Plano criado: {plan}")
else:
    print(f"✅ Plano encontrado: {plan}")

# Criar ou atualizar BillingCustomer
if billing:
    print("\n🔧 Atualizando BillingCustomer...")
    billing.plan = plan
    billing.status = 'trial'
    billing.trial_active = True
    if not billing.trial_expires or billing.trial_expires < date.today():
        billing.trial_expires = date.today() + timedelta(days=7)
    billing.save()
    print("✅ BillingCustomer atualizado!")
else:
    print("\n🔧 Criando BillingCustomer...")
    billing = BillingCustomer.objects.create(
        empresa=empresa,
        plan=plan,
        status='trial',
        trial_active=True,
        trial_expires=date.today() + timedelta(days=7),
        email_cobranca=empresa.email or 'admin@empresaa.com'
    )
    print("✅ BillingCustomer criado!")

print(f"\n📊 Configuração final:")
print(f"   Empresa: {empresa.nome}")
print(f"   Plano: {billing.plan}")
print(f"   Status: {billing.status}")
print(f"   Trial ativo: {billing.trial_active}")
print(f"   Trial expira: {billing.trial_expires}")
print(f"   Limite de funcionários: {billing.plan.max_employees}")

print("\n✨ Configuração concluída! Agora você pode importar funcionários.")
