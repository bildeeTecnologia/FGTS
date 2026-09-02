"""
Script para criar os 3 planos padrão no sistema.
Execute com: python manage.py shell < scripts/create_default_plans.py
"""

from billing.models import Plan

# Dados dos 3 planos
plans_data = [
    {
        'plan_type': 'BASIC',
        'max_employees': 50,
        'has_advanced_dashboard': False,
        'has_custom_reports': False,
        'has_pdf_export': False,
        'has_api': False,
        'support_level': 'EMAIL',
        'price_monthly': 99.00,
        'price_yearly': 990.00,
        'active': True,
    },
    {
        'plan_type': 'PROFESSIONAL',
        'max_employees': 200,
        'has_advanced_dashboard': True,
        'has_custom_reports': True,
        'has_pdf_export': True,
        'has_api': False,
        'support_level': 'PRIORITY',
        'price_monthly': 199.00,
        'price_yearly': 1990.00,
        'active': True,
    },
    {
        'plan_type': 'ENTERPRISE',
        'max_employees': None,  # Ilimitado
        'has_advanced_dashboard': True,
        'has_custom_reports': True,
        'has_pdf_export': True,
        'has_api': True,
        'support_level': '24_7',
        'price_monthly': 399.00,
        'price_yearly': 3990.00,
        'active': True,
    },
]

# Criar os planos
for plan_data in plans_data:
    plan, created = Plan.objects.get_or_create(
        plan_type=plan_data['plan_type'],
        defaults=plan_data
    )
    
    if created:
        print(f"✓ Plano {plan.get_plan_type_display()} criado com sucesso!")
    else:
        print(f"- Plano {plan.get_plan_type_display()} já existe")

print("\nPlanos padrão carregados!")
