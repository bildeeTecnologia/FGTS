# 🔴 ANÁLISE DE VULNERABILIDADES - SISTEMA TRIAL

## Status: ⚠️ CRÍTICO - TODAS REQUEREM CORREÇÃO IMEDIATA

---

## 📋 RESUMO EXECUTIVO

O sistema trial foi implementado com proteção de **middleware + UI warnings**, mas **FALTA ENFORCEMENT** nas operações críticas. Usuários em trial podem:

- ❌ Importar **10+ funcionários em lote** (sem limite)
- ❌ Criar **múltiplas empresas** (sem limite)
- ❌ Gerar **lançamentos ilimitados** (sem limite)
- ❌ **Exportar dados** em CSV/PDF (sem restrição)
- ❌ Fechar **banner de aviso** (UI bypass)

**Solução**: 5 correções críticas + 3 de segurança = TOTAL de 8 pontos de hardening

---

## 🔐 VULNERABILIDADES CRÍTICAS

### **1️⃣ FuncionarioImportService - Sem Limite em Trial**

**Localização**: `funcionarios/services.py` linha 150-260

**Problema**: 
```python
# CÓDIGO ATUAL - SEM LIMITE EM TRIAL
def import_funcionarios_from_file(file, empresa_id=None, user=None):
    # Validações existentes:
    # ✅ Permissão de empresa (is_empresa_allowed)
    # ✅ Billing ativo (status='active') - MAS trial NÃO É 'active'!
    # ✅ Limite do plano (plan.max_employees)
    # ❌ SEM LIMITE ESPECÍFICO PARA TRIAL
    
    # Cenário exploração:
    if billing_customer.status == 'trial':  # trial user
        # plan.max_employees = 50 (padrão do plano básico)
        # Importa 50 funcionários em um batch
        # Depois pode importar mais em outro arquivo = 100+ total
```

**Impacto**:
- Trial user cria 5 arquivos XLSX com 100 funcionários cada = **500 funcionários em 7 dias**
- Teste fraudulento com dados fictícios
- Possível extração de dados de template

**Correção Necessária**:
```python
# ADICIONAR em import_funcionarios_from_file() - LINHA ~180

# VALIDAÇÃO ADICIONAL: Limite para trial
if billing_customer.status == 'trial':
    TRIAL_MAX_IMPORT = 10  # Hardcoded limit
    # Contar quantas linhas tem o arquivo
    total_linhas = ws.max_row - 1  # -1 para descontar header
    
    if total_linhas > TRIAL_MAX_IMPORT:
        raise ValueError(
            f"✋ Limite de trial atingido! "
            f"Você pode importar no máximo {TRIAL_MAX_IMPORT} colaboradores por vez. "
            f"Seu arquivo tem {total_linhas} registros."
        )
```

---

### **2️⃣ EmpresaCreateView - Sem Limite de Empresas em Trial**

**Localização**: `empresas/views.py` linha 15-75

**Problema**:
```python
# CÓDIGO ATUAL - QUALQUER USER TRIAL CRIA N EMPRESAS
def form_valid(self, form):
    response = super().form_valid(form)
    
    # Se há plano selecionado, associar à empresa e redirecionar para checkout
    plan_type = self.request.session.get('selected_plan_type')
    if plan_type and self.object:
        try:
            # ✅ Cria BillingCustomer com trial
            # ❌ NADA IMPEDE DE CRIAR empresa2, empresa3, empresa4...
```

**Impacto**:
- Trial user cria empresa1 com trial = 10 imports
- Cria empresa2 com trial = +10 imports (TOTAL = 20)
- Cria empresa3 = +10 imports (TOTAL = 30)
- **Contorna limite de 10 por empresa criando múltiplas empresas**

**Cenário Real**:
```
Dia 1: empresa1 (trial) → importa 10 → 10 total
Dia 2: empresa2 (trial) → importa 10 → 20 total
Dia 3: empresa3 (trial) → importa 10 → 30 total
Dia 7: empresa7 (trial) → importa 10 → 70 total
```

**Correção Necessária**:
```python
# ADICIONAR em EmpresaCreateView.dispatch() ou form_valid()

def dispatch(self, request, *args, **kwargs):
    # Verificar se user em trial já tem empresa criada
    trial_empresas = Empresa.objects.filter(
        usuarioempresa__usuario=request.user,
        billing_customer__status='trial'
    ).count()
    
    if trial_empresas >= 1:  # Max 1 empresa por trial
        messages.error(
            request,
            "🔒 Em trial, você pode testar com apenas 1 empresa. "
            "Assine para criar múltiplas empresas."
        )
        return redirect('empresa-list')
    
    return super().dispatch(request, *args, **kwargs)
```

---

### **3️⃣ LancamentoCreateView - Sem Limite de Lançamentos em Trial**

**Localização**: `lancamentos/views.py` linha 29-50

**Problema**:
```python
# CÓDIGO ATUAL - SEM LIMITE
class LancamentoCreateView(LoginRequiredMixin, EmpresaScopeMixin, CreateView):
    def form_valid(self, form):
        empresa = form.cleaned_data.get('empresa')
        # ✅ Valida se empresa pertence ao user
        # ❌ NÃO VALIDA QUANTIDADE DE LANÇAMENTOS EM TRIAL
        
        lancamento = form.save()  # SALVA SEM LIMITE!
```

**Impacto**:
- Trial user cria 1000 lançamentos em 7 dias
- Pode gerar relatórios pesados (CPU intensive)
- Possível DoS interno (banco cresce muito)

**Cenário**:
```
Trial user com 50 funcionários:
- 50 funcionários × 12 meses = 600 lançamentos
- Em 3 horas, pode ter 6 anos de histórico fictício
```

**Correção Necessária**:
```python
# ADICIONAR em LancamentoCreateView.form_valid()

def form_valid(self, form):
    empresa = form.cleaned_data.get('empresa')
    
    if empresa and not is_empresa_allowed(self.request.user, empresa.codigo):
        return HttpResponseForbidden('Empresa não permitida.')
    
    # NOVA VALIDAÇÃO: Limite de lançamentos em trial
    try:
        billing = empresa.billing_customer
        if billing.status == 'trial':
            TRIAL_MAX_LANCAMENTOS = 100
            existing_count = Lancamento.objects.filter(empresa=empresa).count()
            
            if existing_count >= TRIAL_MAX_LANCAMENTOS:
                messages.error(
                    self.request,
                    f"🔒 Limite de trial atingido! "
                    f"Máximo {TRIAL_MAX_LANCAMENTOS} lançamentos em trial. "
                    f"Você já tem {existing_count}. Assine para continuar."
                )
                return self.form_invalid(form)
    except:
        pass  # Se não tem billing, deixa falhar no save()
    
    lancamento = form.save()
    messages.success(self.request, f'✅ Lançamento registrado!')
    return super().form_valid(form)
```

---

### **4️⃣ Export (CSV/PDF) - Sem Restrição em Trial**

**Localização**: `lancamentos/views.py` linha 400-500

**Problema**:
```python
# CÓDIGO ATUAL - EXPORTA TUDO
@require_http_methods(["GET"])
def export_relatorio_competencia_csv(request):
    empresa_id = request.GET.get('empresa')
    competencias_multi = request.GET.get('competencias', '')
    funcionario_id = request.GET.get('funcionario')
    
    empresa = Empresa.objects.get(pk=empresa_id)
    # ❌ NÃO VALIDA SE É TRIAL
    # ❌ EXPORTA TUDO EM CSV SEM RESTRIÇÃO
    
    # CSV COM TODOS OS DADOS...
    return resp
```

**Impacto**:
- Trial user vê preview em tela ✅ OK
- Mas pode fazer download de CSV/PDF com **todos os dados**
- "Ah, vou exportar em CSV para fazer backup antes de expirar"

**Cenário**:
```
Trial user:
1. Importa 10 funcionários (fictícios para teste)
2. Cria lançamentos para 2024-2025 (teste)
3. Gera relatório e EXPORTA EM CSV/PDF
4. Trial expira, mas tem dados extraídos
```

**Correção Necessária**:
```python
# ADICIONAR no início de export_relatorio_competencia_csv()

def export_relatorio_competencia_csv(request):
    empresa_id = request.GET.get('empresa')
    competencias_multi = request.GET.get('competencias', '')
    funcionario_id = request.GET.get('funcionario')
    
    empresa = Empresa.objects.get(pk=empresa_id)
    
    # NOVA VALIDAÇÃO: Bloquear export em trial
    try:
        billing = empresa.billing_customer
        if billing.status == 'trial':
            return JsonResponse(
                {
                    'error': '🔒 Exportação indisponível em trial',
                    'message': 'Faça upgrade para exportar dados em CSV/PDF'
                },
                status=403
            )
    except:
        pass
    
    # ... resto do código
```

**E igual para PDF**:
```python
def export_relatorio_competencia_pdf(request):
    empresa_id = request.GET.get('empresa')
    # ... validações ...
    
    # MESMA VALIDAÇÃO
    try:
        billing = empresa.billing_customer
        if billing.status == 'trial':
            return JsonResponse({'error': 'PDF export bloqueado em trial'}, status=403)
    except:
        pass
```

---

### **5️⃣ Middleware Banner - Permitir Fechar (Bypass UI)**

**Localização**: `empresas/templates/base.html` linha 332-360

**Problema**:
```html
<!-- CÓDIGO ATUAL -->
<div class="alert alert-warning alert-dismissible fade show mb-0" role="alert">
    <!-- ⚠️ BOTÃO CLOSE: USUÁRIO PODE FECHAR E IGNORAR AVISO -->
    <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    
    <div class="d-flex align-items-center justify-content-between">
        <div>
            <i class="bi bi-clock-history me-2 fs-5"></i>
            <strong>{{ request.trial_customer.trial_warning_message }}</strong>
```

**Impacto**:
- Banner mostra "3 dias restantes" ✅ Funciona
- Usuário clica no X e fecha banner ✅ UI bypass
- Continua usando sistema como se tudo fosse normal
- **Falso senso de segurança**

**Correção Necessária**:
```html
<!-- NOVO CÓDIGO -->
{% if request.user.is_authenticated and request.trial_customer %}
    {% if request.trial_customer.is_trial_active %}
    <div class="container-lg mb-3">
        {% if request.trial_customer.days_remaining_trial <= 3 %}
        <!-- ÚLTIMOS 3 DIAS: NÃO PERMITIR FECHAR -->
        <div class="alert alert-danger alert-dismissible fade show mb-0" role="alert">
            <!-- SEM btn-close! -->
            <div class="d-flex align-items-center justify-content-between">
                <div>
                    <i class="bi bi-exclamation-triangle-fill me-2 fs-5 text-danger"></i>
                    <strong>⚠️ {{ request.trial_customer.trial_warning_message }}</strong>
                    <br>
                    <small class="text-muted">
                        Trial expirando em breve. Clique em "Assinar Agora!" para continuar usando.
                    </small>
                </div>
                <a href="{% url 'billing-checkout-plano' %}" class="btn btn-danger btn-sm ms-2">
                    <i class="bi bi-lightning-fill me-1"></i> Assinar Agora!
                </a>
            </div>
        </div>
        {% else %}
        <!-- MAIS DE 3 DIAS: PERMITIR FECHAR (MAS COM AVISO) -->
        <div class="alert alert-warning alert-dismissible fade show mb-0" role="alert">
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            <div class="d-flex align-items-center justify-content-between">
                <div>
                    <i class="bi bi-clock-history me-2 fs-5"></i>
                    <strong>{{ request.trial_customer.trial_warning_message }}</strong>
                    <br>
                    <small class="text-muted">Teste completo com todas as funcionalidades</small>
                </div>
                <a href="{% url 'billing-checkout-plano' %}" class="btn btn-primary btn-sm ms-2">
                    <i class="bi bi-credit-card me-1"></i> Assinar Agora
                </a>
            </div>
        </div>
        {% endif %}
    </div>
    {% endif %}
{% endif %}
```

---

## ⚠️ VULNERABILIDADES ALTAS (Circunvenção Possível)

### **6️⃣ Relatório Pesado - Sem Rate Limiting**

**Localização**: `lancamentos/views.py` linha 252

**Problema**:
```python
class RelatorioCompetenciaView(LoginRequiredMixin, FormView):
    def form_valid(self, form):
        # ❌ NÃO LIMITA QUANTIDADE DE RELATÓRIOS
        # Trial user pode gerar 1000 relatórios/dia
        # Cálculos pesados = CPU heavy = degradação de performance
```

**Correção**: Adicionar cache + rate limit

```python
from django.views.decorators.cache import cache_page
from django.core.cache import cache

class RelatorioCompetenciaView(LoginRequiredMixin, FormView):
    def form_valid(self, form):
        # Verificar rate limit
        user_key = f"relatorio_count_{self.request.user.id}"
        current_count = cache.get(user_key, 0)
        
        if current_count >= 5:  # Max 5 relatórios/dia em trial
            try:
                billing = # ... get billing
                if billing.status == 'trial':
                    messages.error(self.request, "Máximo 5 relatórios/dia em trial")
                    return self.form_invalid(form)
            except:
                pass
        
        cache.set(user_key, current_count + 1, 86400)  # 24 horas
        # ... continua
```

---

### **7️⃣ Plan Feature Flags - Não Validados**

**Localização**: `billing/models.py` + views varias

**Problema**:
```python
class Plan(models.Model):
    has_api = models.BooleanField(default=False)
    has_pdf_export = models.BooleanField(default=False)
    has_custom_reports = models.BooleanField(default=False)
    # ❌ ESSES CAMPOS EXISTEM MAS NÃO SÃO VALIDADOS EM LUGAR ALGUM!
```

**Correção**: Criar decorator

```python
# billing/decorators.py
from functools import wraps
from django.http import JsonResponse

def require_plan_feature(feature_name):
    """Decorator para validar se usuário tem acesso ao feature"""
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            try:
                # Obter BillingCustomer do user
                billing = BillingCustomer.objects.filter(
                    empresa__usuarioempresa__usuario=request.user
                ).first()
                
                if not billing or not billing.plan:
                    return JsonResponse({'error': 'No plan found'}, status=403)
                
                # Validar feature
                if not getattr(billing.plan, f'has_{feature_name}', False):
                    return JsonResponse(
                        {'error': f'{feature_name} not available in your plan'},
                        status=403
                    )
                
                # Feature disponível
                return view_func(request, *args, **kwargs)
            except Exception as e:
                return JsonResponse({'error': str(e)}, status=500)
        
        return wrapper
    return decorator

# Uso:
@require_plan_feature('pdf_export')
def export_relatorio_competencia_pdf(request):
    # ... código
```

---

### **8️⃣ Validação de Status Billing Incompleta**

**Localização**: `funcionarios/services.py` linha 215

**Problema**:
```python
# CÓDIGO ATUAL - VALIDAÇÃO INCOMPLETA
if billing_customer.status != 'active':
    raise ValueError(f"Status atual: {billing_customer.get_status_display()}")

# ❌ MAS: status='trial' NÃO É 'active'!
# A validação FALTA para trial users
```

**Cenário Bug**:
- User com `status='trial'` tenta importar
- Código checa `status != 'active'` 
- `'trial' != 'active'` = TRUE
- Levanta erro "não possui assinatura ativa"
- **MAS O MIDDLEWARE DEIXA PASSAR PORQUE status='trial' é válido**

**Correção**:
```python
# ADICIONAR validação explícita
VALID_STATUSES_FOR_IMPORT = ['active', 'trial']  # trial DEVE ser válido

if billing_customer.status not in VALID_STATUSES_FOR_IMPORT:
    raise ValueError(
        f"Empresa não pode importar. Status: {billing_customer.get_status_display()}"
    )

# Depois, adicionar limite se trial:
if billing_customer.status == 'trial':
    # ... validar limite específico
```

---

## 📊 MATRIZ DE RISCO

| # | Vulnerabilidade | Severidade | Fácil de Explorar? | Impacto |
|---|---|---|---|---|
| 1 | FuncionarioImportService sem limite | 🔴 CRÍTICA | ✅ SIM (5 imports) | 500+ registros fictícios |
| 2 | Múltiplas empresas em trial | 🔴 CRÍTICA | ✅ SIM (botão criar) | ∞ escalabilidade |
| 3 | Lançamentos ilimitados | 🔴 CRÍTICA | ✅ SIM (form manual) | DoS interno |
| 4 | Export CSV/PDF sem restrição | 🔴 CRÍTICA | ✅ SIM (1 clique) | Extração de dados |
| 5 | Banner bypass (fechar aviso) | 🟠 ALTA | ✅ SIM (UI) | Falso senso segurança |
| 6 | Relatório rate limiting | 🟠 ALTA | ✅ SIM (script) | CPU drain |
| 7 | Feature flags não validados | 🟠 ALTA | ❌ NÃO (mas existe) | Inconsistência |
| 8 | Validação status incompleta | 🟡 MÉDIA | ❌ NÃO (mas existe) | Edge case |

---

## 🛡️ PRIORIDADE DE CORREÇÃO

### **🚨 PRIORITY 1 - Fazer HOJE (15 min cada)**
1. ✅ Limite 10 imports por arquivo em trial (`FuncionarioImportService`)
2. ✅ Max 1 empresa por trial user (`EmpresaCreateView`)
3. ✅ Bloquear CSV/PDF export em trial (`export_relatorio_*`)

### **⚡ PRIORITY 2 - Fazer AMANHÃ**
4. Limite 100 lançamentos por empresa em trial (`LancamentoCreateView`)
5. Remover botão close em banner se < 3 dias (`base.html`)
6. Rate limiting relatórios (5/dia em trial)

### **🔧 PRIORITY 3 - Esta Semana**
7. Feature flag decorator (@require_plan_feature)
8. Audit logging de tentativas de bypass
9. Testes automatizados para cada limite

---

## ✅ CHECKLIST DE IMPLEMENTAÇÃO

- [ ] **Passo 1**: Editar `funcionarios/services.py` - Adicionar limite 10 imports
- [ ] **Passo 2**: Editar `empresas/views.py` - Adicionar dispatch() com check de empresas
- [ ] **Passo 3**: Editar `lancamentos/views.py` - Bloquear export em trial
- [ ] **Passo 4**: Editar `empresas/templates/base.html` - Remover close em <3 dias
- [ ] **Passo 5**: Criar testes em `tests/test_trial_security.py`
- [ ] **Passo 6**: Executar testes e validar
- [ ] **Passo 7**: Fazer deploy

---

## 📝 NOTAS IMPORTANTES

1. **Trial Status**: Usuários em trial têm `BillingCustomer.status = 'trial'` (não 'active')
2. **Middleware**: Já valida expiração diária ✅ - MAS não limita operações
3. **UI vs Backend**: Banner é UI (pode fechar). Limites devem ser BACKEND (não podem contornar)
4. **Test Cases**: Criar scenarios com trial users para validar cada limite

---

## 🎯 CONCLUSÃO

Sistema trial tem **estrutura correta** (modelo, middleware, UI) mas **falta camada de enforcement** (validações nos endpoints). 

**Sem essas 8 correções**, trial users podem:
- Importar 100+ colaboradores
- Criar 10+ empresas
- Gerar 1000+ lançamentos
- Exportar dados em CSV/PDF
- Fazer "testes produtivos" durante 7 dias

**Com essas 8 correções**, trial users ficam limitados a:
- Máximo 10 colaboradores por import (total ~30-50 no trial)
- 1 empresa apenas
- 100 lançamentos max
- Preview em tela, sem export
- Uso real de teste, não exploração

---

**Documento gerado**: 2025-01-10
**Status**: ⚠️ AGUARDANDO IMPLEMENTAÇÃO DAS 8 CORREÇÕES
