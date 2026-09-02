# SISTEMA DE PLANOS - GUIA DE USO

## 1. PLANOS CRIADOS

Três planos foram criados no banco de dados:

### 🔷 Básico - R$ 99/mês
- Máximo: 50 colaboradores
- Features: Dashboard básico
- Suporte: E-mail
- API: Não

### 🟣 Profissional - R$ 199/mês
- Máximo: 200 colaboradores
- Features: Dashboard avançado, Relatórios personalizados, Exportar PDF/Excel
- Suporte: Prioritário
- API: Não

### 🟡 Empresarial - R$ 399/mês
- Máximo: Ilimitado
- Features: Dashboard avançado, Relatórios personalizados, Exportar PDF/Excel, API
- Suporte: 24/7
- API: Sim

---

## 2. ATRIBUINDO PLANO A EMPRESA

No admin Django (`/admin/billing/billingcustomer/`):

1. Clique na empresa
2. Selecione o plano desejado
3. Salve

Ou via Python Shell:

```python
from billing.models import Plan
from empresas.models import Empresa

empresa = Empresa.objects.first()
plan = Plan.objects.get(plan_type='PROFESSIONAL')

# Atualizar plano
empresa.billing_customer.plan = plan
empresa.billing_customer.save()
```

---

## 3. VALIDAÇÕES AUTOMÁTICAS

### ✅ ao_criar_funcionário

Quando tentar criar um novo funcionário, o sistema verifica:

```python
# Automaticamente validado em Funcionario.clean()
funcionario = Funcionario.objects.create(
    empresa=empresa_basico_50_usuarios,
    nome="João",
    cpf="123.456.789-00",
    data_admissao="2025-12-31"
)
# Se já tiver 50 funcionários, gera erro:
# "Seu plano Básico permite no máximo 50 colaboradores ativos. 
#  Você já possui 50. Faça upgrade para adicionar mais."
```

---

## 4. USAR MIXINS PARA PROTEGER VIEWS

### Exemplo 1: Proteger Dashboard Avançado

```python
from fgtsweb.mixins import AdvancedDashboardRequiredMixin
from django.views import View

class DashboardAvancadoView(AdvancedDashboardRequiredMixin, TemplateView):
    template_name = 'dashboard_avancado.html'
    
    # Se plano não tiver has_advanced_dashboard=True:
    # → Redireciona para dashboard com mensagem de erro
```

### Exemplo 2: Proteger Exportação PDF

```python
from fgtsweb.mixins import PDFExportRequiredMixin

class LancamentoExportPDFView(PDFExportRequiredMixin, View):
    def get(self, request):
        # Se plano não permite PDF export:
        # → Mostra: "Este recurso não está disponível no seu plano Básico"
        pass
```

### Exemplo 3: Proteger API

```python
from fgtsweb.mixins import APIAccessRequiredMixin
from rest_framework.views import APIView

class LancamentoAPIView(APIAccessRequiredMixin, APIView):
    def get(self, request):
        # Apenas Empresarial tem acesso
        pass
```

### Exemplo 4: Criar Custom Mixin

```python
from fgtsweb.mixins import PlanFeatureRequiredMixin

class MinhaCustomFeatureView(PlanFeatureRequiredMixin, TemplateView):
    required_feature = 'has_custom_reports'
    # ou qualquer outro campo booleano do modelo Plan
```

---

## 5. VERIFICAR PLANO EM VIEW

```python
from django.shortcuts import redirect
from django.contrib import messages

def meu_relatorio(request):
    plan = request.user.empresa.billing_customer.plan
    
    # Verificar feature específica
    if not plan.has_custom_reports:
        messages.error(request, 'Upgrade para Profissional para acessar relatórios')
        return redirect('dashboard')
    
    # ... renderizar relatório
    return render(request, 'relatorio.html')
```

---

## 6. RASTREAR LIMITE DE COLABORADORES

```python
from billing.models import BillingCustomer

billing = empresa.billing_customer
print(billing.plan.max_employees)          # 50, 200, ou None (ilimitado)
print(billing.active_employees)            # Número atual
print(billing.get_usage_percentage())      # 0, 50, 100
print(billing.get_employees_remaining())   # Quantos faltam
```

---

## 7. ATUALIZAR CONTADOR DE COLABORADORES

Quando um colaborador é demitido, o campo `data_demissao` deve ser preenchido:

```python
funcionario.data_demissao = "2025-12-31"
funcionario.save()

# A validação .clean() NÃO vai contar como ativo
# (data_demissao__isnull=True)
```

---

## 8. REGISTROS EM AUDIT LOGS

Todas as ações relacionadas a planos são registradas:
- ✅ Mudança de plano da empresa
- ✅ Tentativa de criar funcionário acima do limite
- ✅ Acesso a features não permitidas
- ✅ Tentativas de acesso não autorizado

Visualizar em: `/auditoria/` (admin ou staff apenas)

---

## 9. PRÓXIMOS PASSOS (NÃO IMPLEMENTADO AINDA)

- [ ] Integração com Asaas para pagamentos
- [ ] Webhooks para mudanças de plano
- [ ] Dashboard mostrando: Plano atual, uso, próxima renovação
- [ ] Fluxo de upgrade direto na app
- [ ] Notificações quando atingir 80% do limite
- [ ] Testes unitários para validações

---

## 10. TROUBLESHOOTING

### Erro: "Empresa não possui plano configurado"
- Solução: Atribua um plano em `/admin/billing/billingcustomer/`

### Funcionário criado mas não conta para limite
- Verifique se tem `data_demissao` (deve ser NULL para ativo)

### Mixin redireciona mas não mostra mensagem
- Use `messages.get_messages(request)` no template

