# MAPEAMENTO: SISTEMA DE PLANOS E ASSINATURAS

## 1. ARQUITETURA DO BANCO DE DADOS

### Estrutura Existente:
- ✓ `BillingCustomer` - Cliente de faturamento
- ✓ `PricingPlan` - Plano de preço
- ✓ `Subscription` - Assinatura

### Necessário Adicionar:
```
📦 PlansFeatures (novo modelo)
├── plan_type: BASIC, PROFESSIONAL, ENTERPRISE
├── max_users: 50, 200, ilimitado
├── has_advanced_dashboard: True/False
├── has_custom_reports: True/False
├── has_pdf_export: True/False
├── has_api: True/False
├── support_level: EMAIL, PRIORITY, 24_7
└── price: 99, 199, 399

📦 BillingCustomer (atualizar)
├── plan_type: FK(PlansFeatures) ← ADICIONAR
└── active_subscribers_count: int (rastrear uso)
```

---

## 2. FLUXO DE IMPLEMENTAÇÃO

### FASE 1: Criar Modelos de Planos
```
1. Criar modelo `Plan` com tipos (BASIC, PROFESSIONAL, ENTERPRISE)
2. Adicionar campo `plan` em `BillingCustomer`
3. Criar fixtures com os 3 planos padrão
4. Adicionar validações de limites
```

### FASE 2: Validações por Plano
```
📍 ao_criar_funcionario:
   ├─ Validar: count(funcionarios) < plan.max_users
   └─ Erro: "Plano {plan} permite apenas {limit} colaboradores"

📍 ao_acessar_funcionalidade:
   ├─ Dashboard Avançado → Validar plan.has_advanced_dashboard
   ├─ Relatórios Custom → Validar plan.has_custom_reports
   ├─ Exportar PDF/Excel → Validar plan.has_pdf_export
   └─ API → Validar plan.has_api

📍 ao_requisitar_suporte:
   ├─ EMAIL: até 2 dias úteis
   ├─ PRIORITY: até 24 horas
   └─ 24_7: resposta imediata
```

### FASE 3: Middleware de Validação
```
AuditPlan Middleware:
├─ Interceptar acesso a features premium
├─ Registrar tentativa de acesso não autorizado
├─ Redirecionar com mensagem amigável
└─ Log em audit_logs
```

### FASE 4: Interface do Admin
```
Admin Dashboard:
├─ Visualizar plano da empresa
├─ Atualizar plano
├─ Ver uso atual vs limite
└─ Gerar relatório de utilização
```

---

## 3. IMPLEMENTAÇÃO TÉCNICA

### Modelo Plan
```python
class Plan(models.Model):
    PLAN_TYPES = [
        ('BASIC', 'Básico'),
        ('PROFESSIONAL', 'Profissional'),
        ('ENTERPRISE', 'Empresarial'),
    ]
    
    SUPPORT_LEVELS = [
        ('EMAIL', 'E-mail'),
        ('PRIORITY', 'Prioritário'),
        ('24_7', '24/7'),
    ]
    
    plan_type = CharField(choices=PLAN_TYPES, unique=True)
    max_employees = IntegerField()  # 50, 200, unlimited
    
    # Features
    has_advanced_dashboard = BooleanField(default=False)
    has_custom_reports = BooleanField(default=False)
    has_pdf_export = BooleanField(default=False)
    has_api = BooleanField(default=False)
    
    # Support
    support_level = CharField(choices=SUPPORT_LEVELS)
    
    # Pricing
    price_monthly = DecimalField()
    price_yearly = DecimalField()
```

### BillingCustomer (atualizar)
```python
class BillingCustomer(models.Model):
    empresa = OneToOneField(Empresa)
    plan = ForeignKey(Plan)  # ← ADICIONAR
    active_employees = IntegerField(default=0)  # ← RASTREAR USO
    
    def can_add_employee(self):
        if self.plan.max_employees is None:  # ilimitado
            return True
        return self.active_employees < self.plan.max_employees
    
    def get_usage_percentage(self):
        if self.plan.max_employees is None:
            return 0
        return (self.active_employees / self.plan.max_employees) * 100
```

---

## 4. VALIDAÇÕES APLICADAS

### ✅ ao_criar_funcionario
```python
def clean(self):
    super().clean()
    empresa_plan = self.empresa.billing_customer.plan
    
    if not empresa_plan.can_add_employee():
        raise ValidationError(
            f"Seu plano {empresa_plan.plan_type} permite "
            f"apenas {empresa_plan.max_employees} colaboradores"
        )
```

### ✅ ao_acessar_dashboard_avancado
```python
@user_passes_test(lambda u: u.empresa.billing_customer.plan.has_advanced_dashboard)
def dashboard_advanced_view(request):
    # acesso permitido
```

### ✅ ao_exportar_pdf
```python
def export_pdf(request):
    plan = request.user.empresa.billing_customer.plan
    
    if not plan.has_pdf_export:
        messages.error(request, "Recurso disponível apenas nos planos Profissional e Empresarial")
        return redirect('lancamento-list')
```

---

## 5. AUDIT LOGS + PLANOS

Registrar:
- ✓ Quando plano é alterado
- ✓ Quando limite é atingido
- ✓ Quando feature é acessada indevidamente
- ✓ Tentativas de uso não autorizado

---

## 6. ROADMAP DE IMPLEMENTAÇÃO

### Semana 1:
- [ ] Criar modelo `Plan` com 3 tipos
- [ ] Atualizar `BillingCustomer`
- [ ] Adicionar migrations
- [ ] Criar fixtures com planos padrão

### Semana 2:
- [ ] Adicionar validações em `Funcionario.clean()`
- [ ] Criar mixins de autorização
- [ ] Validar acesso a PDF/Excel export
- [ ] Validar acesso a API

### Semana 3:
- [ ] Interface admin para gerenciar planos
- [ ] Dashboard de uso do plano
- [ ] Mensagens amigáveis de limite atingido
- [ ] Tests

### Semana 4:
- [ ] Integração com Asaas (upgrade/downgrade de planos)
- [ ] Webhooks para mudanças de plano
- [ ] Notificações de renovação
