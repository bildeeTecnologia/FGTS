# IMPLEMENTAÇÃO IMEDIATA - TRIAL SECURITY HARDENING
# Este arquivo contém os diffs/patches para as 8 vulnerabilidades
# Copie e aplique em cada arquivo correspondente

# ============================================================================
# PATCH 1: funcionarios/services.py
# ============================================================================
# ADICIONAR APÓS A LINHA ~175 (antes do loop de processamento)

"""
ENCONTRE ISTO:
    result = {
        'total': 0,
        'success': 0,
        'errors': [],
        'created_funcionarios': []
    }
    
    # Processar linhas
    for row_idx, row in enumerate(ws.iter_rows(min_row=2, values_only=False), 2):

SUBSTITUA POR:
    result = {
        'total': 0,
        'success': 0,
        'errors': [],
        'created_funcionarios': []
    }
    
    # PATCH 1: Validação de limite em trial
    # Contar linhas do arquivo (excluir header)
    total_rows = ws.max_row - 1
    
    # Obter empresa para validar status
    first_empresa = None
    first_empresa_identifier = None
    
    # Processar linhas
    for row_idx, row in enumerate(ws.iter_rows(min_row=2, values_only=False), 2):
        if row_idx == 2:  # Primeira linha de dados
            # Extrair empresa da primeira linha para validação
            for header, col_idx in headers.items():
                if header == 'EMPRESA':
                    first_empresa_identifier = row[col_idx - 1].value
                    break
            
            if first_empresa_identifier:
                try:
                    if isinstance(first_empresa_identifier, int):
                        first_empresa = Empresa.objects.get(pk=first_empresa_identifier)
                    else:
                        first_empresa = Empresa.objects.get(codigo=str(first_empresa_identifier))
                    
                    # Validar limite em trial ANTES de processar
                    if first_empresa and hasattr(first_empresa, 'billing_customer'):
                        billing = first_empresa.billing_customer
                        if billing.status == 'trial':
                            TRIAL_MAX_IMPORT = 10
                            if total_rows > TRIAL_MAX_IMPORT:
                                raise ValueError(
                                    f"🔒 LIMITE DE TRIAL ATINGIDO!\n"
                                    f"Seu arquivo tem {total_rows} linhas, mas o limite em trial é de {TRIAL_MAX_IMPORT}.\n"
                                    f"Divida seu arquivo em múltiplos menores ou assine para importar mais."
                                )
                except Empresa.DoesNotExist:
                    pass  # Vai gerar erro mais abaixo anyway
        
        try:
"""

# ============================================================================
# PATCH 2: empresas/views.py
# ============================================================================
# ADICIONAR MÉTODO dispatch() na classe EmpresaCreateView

"""
ENCONTRE ISTO:
class EmpresaCreateView(LoginRequiredMixin, CreateView):
    model = Empresa
    form_class = EmpresaForm
    template_name = 'empresas/empresa_form.html'
    success_url = reverse_lazy('empresa-list')

    def dispatch(self, request, *args, **kwargs):

VERIFIQUE SE JÁ TEM dispatch() - SE NÃO, SUBSTITUA:

class EmpresaCreateView(LoginRequiredMixin, CreateView):
    model = Empresa
    form_class = EmpresaForm
    template_name = 'empresas/empresa_form.html'
    success_url = reverse_lazy('empresa-list')

    def dispatch(self, request, *args, **kwargs):
        # PATCH 2: Validar limite de empresas em trial
        trial_empresas = Empresa.objects.filter(
            usuarioempresa__usuario=request.user,
            billing_customer__status='trial'
        ).count()
        
        if trial_empresas >= 1:
            messages.error(
                request,
                "🔒 Limite de trial: você pode testar com apenas 1 empresa por vez. "
                "Assine para criar múltiplas empresas."
            )
            return redirect('empresa-list')
        
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        # ... resto do código existente
"""

# ============================================================================
# PATCH 3: lancamentos/views.py - LancamentoCreateView
# ============================================================================
# MODIFICAR o método form_valid()

"""
ENCONTRE ISTO (por volta da linha 29-50):
    def form_valid(self, form):
        empresa = form.cleaned_data.get('empresa')
        if empresa and not is_empresa_allowed(self.request.user, empresa.codigo):
            return HttpResponseForbidden('Empresa não permitida para este usuário.')
        
        lancamento = form.save()
        messages.success(self.request, f'✅ Lançamento para {lancamento.funcionario.nome} ({lancamento.competencia}) registrado com sucesso!')
        return super().form_valid(form)

SUBSTITUA POR:
    def form_valid(self, form):
        empresa = form.cleaned_data.get('empresa')
        if empresa and not is_empresa_allowed(self.request.user, empresa.codigo):
            return HttpResponseForbidden('Empresa não permitida para este usuário.')
        
        # PATCH 3: Validar limite de lançamentos em trial
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
            pass  # Se não tem billing, deixa prosseguir
        
        lancamento = form.save()
        messages.success(self.request, f'✅ Lançamento para {lancamento.funcionario.nome} ({lancamento.competencia}) registrado com sucesso!')
        return super().form_valid(form)
"""

# ============================================================================
# PATCH 4: lancamentos/views.py - export_relatorio_competencia_csv()
# ============================================================================
# ADICIONAR NO INÍCIO DA FUNÇÃO (linha 400)

"""
ENCONTRE ISTO (linha 400):
def export_relatorio_competencia_csv(request):
    from django.http import HttpResponse
    empresa_id = request.GET.get('empresa')

SUBSTITUA POR:
def export_relatorio_competencia_csv(request):
    from django.http import HttpResponse
    
    # PATCH 4: Bloquear export em trial
    empresa_id = request.GET.get('empresa')
    try:
        empresa = Empresa.objects.get(pk=empresa_id)
        billing = empresa.billing_customer
        
        if billing.status == 'trial':
            return JsonResponse(
                {
                    'error': '🔒 Exportação indisponível em trial',
                    'message': 'Faça upgrade ou entre em contato para exportar dados em CSV'
                },
                status=403
            )
    except:
        pass  # Continue se erro
    
    # Resto do código original
    empresa_id = request.GET.get('empresa')
"""

# ============================================================================
# PATCH 5: lancamentos/views.py - export_relatorio_competencia_pdf()
# ============================================================================
# ADICIONAR NO INÍCIO DA FUNÇÃO (linha 467)

"""
ENCONTRE ISTO (linha 467):
def export_relatorio_competencia_pdf(request):
    from django.http import HttpResponse
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas
    empresa_id = request.GET.get('empresa')

SUBSTITUA POR:
def export_relatorio_competencia_pdf(request):
    from django.http import HttpResponse
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas
    
    # PATCH 5: Bloquear export PDF em trial
    empresa_id = request.GET.get('empresa')
    try:
        empresa = Empresa.objects.get(pk=empresa_id)
        billing = empresa.billing_customer
        
        if billing.status == 'trial':
            return JsonResponse(
                {
                    'error': '🔒 Exportação indisponível em trial',
                    'message': 'Faça upgrade ou entre em contato para exportar dados em PDF'
                },
                status=403
            )
    except:
        pass  # Continue se erro
    
    # Resto do código original
    empresa_id = request.GET.get('empresa')
"""

# ============================================================================
# PATCH 6: empresas/templates/base.html
# ============================================================================
# SUBSTITUIR a seção do Banner de Trial

"""
ENCONTRE ISTO (por volta da linha 345):
        <!-- Banner de Trial -->
        {% if request.user.is_authenticated and request.trial_customer %}
            {% if request.trial_customer.is_trial_active %}
            <div class="container-lg mb-3">
                <div class="alert alert-warning alert-dismissible fade show mb-0" role="alert">
                    <div class="d-flex align-items-center justify-content-between">
                        <div>
                            <i class="bi bi-clock-history me-2 fs-5"></i>
                            <strong>{{ request.trial_customer.trial_warning_message }}</strong>
                            <br>
                            <small class="text-muted">Teste completo com todas as funcionalidades por 7 dias</small>
                        </div>
                        <a href="{% url 'checkout-plano' %}" class="btn btn-primary btn-sm">
                            <i class="bi bi-lightning-fill me-1"></i> Assinar Agora!
                        </a>
                    </div>
                    <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                </div>
            </div>
            {% endif %}
        {% endif %}

SUBSTITUA POR:
        <!-- Banner de Trial - PATCH 6 -->
        {% if request.user.is_authenticated and request.trial_customer %}
            {% if request.trial_customer.is_trial_active %}
            <div class="container-lg mb-3">
                {% if request.trial_customer.days_remaining_trial <= 3 %}
                <!-- ÚLTIMOS 3 DIAS: Banner vermelho SEM botão close -->
                <div class="alert alert-danger alert-dismissible fade show mb-0" role="alert">
                    <div class="d-flex align-items-center justify-content-between">
                        <div>
                            <i class="bi bi-exclamation-triangle-fill me-2 fs-5 text-danger"></i>
                            <strong>⚠️ {{ request.trial_customer.trial_warning_message }}</strong>
                            <br>
                            <small class="text-muted">
                                {% if request.trial_customer.days_remaining_trial == 0 %}
                                    Trial expira hoje! Assine agora para não perder acesso.
                                {% else %}
                                    Assine agora para não interromper seu trabalho.
                                {% endif %}
                            </small>
                        </div>
                        <a href="{% url 'checkout-plano' %}" class="btn btn-danger btn-sm ms-2" style="white-space: nowrap;">
                            <i class="bi bi-lightning-fill me-1"></i> Assinar Agora!
                        </a>
                    </div>
                    <!-- SEM btn-close nos últimos 3 dias! -->
                </div>
                {% else %}
                <!-- MAIS DE 3 DIAS: Banner amarelo COM botão close opcional -->
                <div class="alert alert-warning alert-dismissible fade show mb-0" role="alert">
                    <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                    <div class="d-flex align-items-center justify-content-between">
                        <div>
                            <i class="bi bi-clock-history me-2 fs-5"></i>
                            <strong>{{ request.trial_customer.trial_warning_message }}</strong>
                            <br>
                            <small class="text-muted">Teste completo com todas as funcionalidades</small>
                        </div>
                        <a href="{% url 'checkout-plano' %}" class="btn btn-primary btn-sm ms-2" style="white-space: nowrap;">
                            <i class="bi bi-credit-card me-1"></i> Assinar Agora
                        </a>
                    </div>
                </div>
                {% endif %}
            </div>
            {% endif %}
        {% endif %}
"""

# ============================================================================
# PATCH 7: billing/decorators.py (NOVO ARQUIVO)
# ============================================================================
# CRIAR NOVO ARQUIVO: billing/decorators.py

"""
from functools import wraps
from django.http import JsonResponse


def require_plan_feature(feature_name):
    '''Decorator para validar se usuário tem acesso a determinado feature do plano'''
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            try:
                from .models import BillingCustomer
                from empresas.models import Empresa
                
                # Obter BillingCustomer do usuário
                billing = BillingCustomer.objects.filter(
                    empresa__usuarioempresa__usuario=request.user
                ).first()
                
                if not billing:
                    return JsonResponse(
                        {'error': 'No billing customer found'},
                        status=403
                    )
                
                if not billing.plan:
                    return JsonResponse(
                        {'error': 'No plan associated with this customer'},
                        status=403
                    )
                
                # Validar se feature está disponível no plano
                has_feature = getattr(billing.plan, f'has_{feature_name}', False)
                
                if not has_feature:
                    feature_display = feature_name.replace('_', ' ').title()
                    return JsonResponse(
                        {
                            'error': f'🔒 {feature_display} não está disponível no seu plano',
                            'feature': feature_name
                        },
                        status=403
                    )
                
                # Feature disponível - continuar
                return view_func(request, *args, **kwargs)
                
            except Exception as e:
                return JsonResponse(
                    {'error': f'Error validating plan feature: {str(e)}'},
                    status=500
                )
        
        return wrapper
    return decorator
"""

# ============================================================================
# PATCH 8: lancamentos/views.py - Adicionar imports para JSON
# ============================================================================
# NO TOPO DO ARQUIVO, adicionar:

"""
ENCONTRE ISTO (linha 1):
from datetime import datetime, date
from decimal import Decimal
from dateutil.relativedelta import relativedelta
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.views.generic import FormView, CreateView, UpdateView, ListView, View
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from billing.models import BillingCustomer
from empresas.models import Empresa

ADICIONE:
from datetime import datetime, date
from decimal import Decimal
from dateutil.relativedelta import relativedelta
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.views.generic import FormView, CreateView, UpdateView, ListView, View
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.http import JsonResponse  # NOVO
from billing.models import BillingCustomer
from empresas.models import Empresa
"""

# ============================================================================
# CHECKLIST DE APLICAÇÃO
# ============================================================================
"""
Ordem recomendada de aplicação:

1. ✅ PATCH 8: Adicionar import JsonResponse em lancamentos/views.py (linha 1)
2. ✅ PATCH 1: Adicionar limite 10 em funcionarios/services.py (linha ~175)
3. ✅ PATCH 2: Adicionar dispatch() em empresas/views.py (classe EmpresaCreateView)
4. ✅ PATCH 3: Modificar form_valid() em lancamentos/views.py (LancamentoCreateView)
5. ✅ PATCH 4: Bloquear CSV export em lancamentos/views.py (linha ~400)
6. ✅ PATCH 5: Bloquear PDF export em lancamentos/views.py (linha ~467)
7. ✅ PATCH 6: Substituir Banner em empresas/templates/base.html (linha ~345)
8. ✅ PATCH 7: Criar novo arquivo billing/decorators.py

DEPOIS:
- Rodar testes: python manage.py test
- Fazer deploy
- Monitorar logs de tentativas de bypass
"""

print("=" * 80)
print("IMPLEMENTAÇÃO DE SEGURANÇA PARA TRIAL")
print("=" * 80)
print("\n8 Patches preparados para aplicação imediata")
print("Veja instruções de aplicação acima")
