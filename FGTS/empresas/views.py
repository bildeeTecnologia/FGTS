from django.shortcuts import render, redirect
from django.http import HttpResponseForbidden
from django.urls import reverse_lazy
from django.views.generic.edit import CreateView, UpdateView
from django.views.generic.list import ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from fgtsweb.mixins import EmpresaScopeMixin, get_allowed_empresa_ids
from .models import Empresa
from .forms import EmpresaForm
from billing.models import Plan, BillingCustomer
from usuarios.models import EmpresaUsuarioRole, Usuario
from django.views import View

class PainelAdminEmpresaView(LoginRequiredMixin, View):
    def get(self, request, empresa_id):
        empresa = Empresa.objects.get(pk=empresa_id)
        is_admin = EmpresaUsuarioRole.objects.filter(usuario=request.user, empresa=empresa, role=EmpresaUsuarioRole.ADMIN).exists()
        grupo = empresa.grupo
        if not grupo:
            try:
                grupo = empresa.grupo_principal
            except Exception:
                grupo = None
        context = {
            'empresa': empresa,
            'user': request.user,
            'is_admin_empresa': is_admin,
            'grupo': grupo,
        }
        if not is_admin:
            return HttpResponseForbidden('Acesso restrito ao administrador da empresa.')
        return render(request, 'empresas/painel_admin_empresa.html', context)

    def post(self, request, empresa_id):
        empresa = Empresa.objects.get(pk=empresa_id)
        is_admin = EmpresaUsuarioRole.objects.filter(usuario=request.user, empresa=empresa, role=EmpresaUsuarioRole.ADMIN).exists()
        if not is_admin:
            return HttpResponseForbidden('Acesso restrito ao administrador da empresa.')
        action = request.POST.get('action')
        username = request.POST.get('username')
        role = request.POST.get('role')
        target_id = request.POST.get('target_id')
        # Adicionar usuário
        if action == 'add' and username and role:
            try:
                usuario = Usuario.objects.get(username=username)
                EmpresaUsuarioRole.objects.update_or_create(usuario=usuario, empresa=empresa, defaults={'role': role})
                messages.success(request, f'Usuário {usuario.username} adicionado como {role}.')
            except Usuario.DoesNotExist:
                messages.error(request, 'Usuário não encontrado.')
        # Remover usuário
        elif action == 'remove' and target_id:
            EmpresaUsuarioRole.objects.filter(id=target_id, empresa=empresa).delete()
            messages.success(request, 'Usuário removido da empresa.')
        # Promover usuário
        elif action == 'promote' and target_id:
            role_obj = EmpresaUsuarioRole.objects.filter(id=target_id, empresa=empresa).first()
            if role_obj:
                role_obj.role = EmpresaUsuarioRole.ADMIN
                role_obj.save()
                messages.success(request, f'Usuário {role_obj.usuario.username} promovido a administrador.')
        return redirect('painel-admin-empresa', empresa_id=empresa.id)

class EmpresaCreateView(LoginRequiredMixin, CreateView):
    model = Empresa
    form_class = EmpresaForm
    template_name = 'empresas/empresa_form.html'
    success_url = reverse_lazy('empresa-list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def dispatch(self, request, *args, **kwargs):
        # Usuários autenticados podem criar empresas
        # O trial é gerenciado no form_valid após criação
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Passar plano selecionado se houver na sessão
        plan_type = self.request.session.get('selected_plan_type')
        if plan_type:
            try:
                context['selected_plan'] = Plan.objects.get(plan_type=plan_type, active=True)
            except Plan.DoesNotExist:
                pass
        return context
    
    def form_valid(self, form):
        usuario = self.request.user
        
        # Validação de limite de empresas por grupo (plano da matriz)
        from datetime import date, timedelta
        grupo = form.cleaned_data.get('grupo')
        if grupo and grupo.empresa_principal:
            try:
                bc = grupo.empresa_principal.billing_customer
                max_companies = bc.get_effective_max_companies()
                if max_companies is not None:
                    total_empresas_grupo = grupo.empresas.count()
                    if total_empresas_grupo >= max_companies:
                        messages.error(
                            self.request,
                            f'❌ Seu plano limita a {max_companies} empresas no grupo. Faça upgrade para adicionar mais CNPJs.'
                        )
                        return redirect('empresa-create')
            except Exception:
                pass
        
        # Salvar a empresa
        empresa = form.save()
        
        # Associar a empresa como empresa principal do usuário (somente se não tiver)
        if not usuario.empresa_id:
            usuario.empresa_id = empresa.codigo
            usuario.save()
            # Fazer refresh do usuário para atualizar sessão
            from django.contrib.auth import get_user_model
            User = get_user_model()
            self.request.user.refresh_from_db()
        
        # Também adicionar às empresas permitidas (com proteção)
        try:
            usuario.empresas_permitidas.add(empresa)
        except Exception:
            pass

        # Garantir que o criador da empresa vire administrador dela
        try:
            EmpresaUsuarioRole.objects.update_or_create(
                usuario=usuario,
                empresa=empresa,
                defaults={'role': EmpresaUsuarioRole.ADMIN},
            )
        except Exception:
            pass
        
        # Criar BillingCustomer com trial automático se não existir
        try:
            plan = Plan.objects.filter(plan_type='BASIC', active=True).first()
            if not plan:
                plan = Plan.objects.filter(active=True).first()
            
            if plan:
                billing, created = BillingCustomer.objects.get_or_create(
                    empresa=empresa,
                    defaults={
                        'plan': plan,
                        'email_cobranca': empresa.email,
                        'status': 'trial',
                        'trial_active': True,
                        'trial_expires': date.today() + timedelta(days=7),
                    }
                )
                if not created and not billing.trial_active:
                    billing.trial_active = True
                    billing.trial_expires = date.today() + timedelta(days=7)
                    billing.status = 'trial'
                    billing.save()
        except Exception as e:
            print(f"Erro ao criar BillingCustomer: {e}")
        
        messages.success(self.request, f'✅ Empresa "{empresa.nome}" criada com sucesso! Você tem 7 dias de trial.')
        
        # Fazer refresh do usuário na sessão para atualizar empresa_id
        self.request.user.refresh_from_db()
        
        # Redirecionar para o dashboard
        return redirect('dashboard')

    def form_invalid(self, form):
        messages.error(self.request, 'Foram encontradas inconsistencias nas informacoes enviadas. Revise as informacoes.')
        return super().form_invalid(form)

class EmpresaListView(LoginRequiredMixin, EmpresaScopeMixin, ListView):
    model = Empresa
    template_name = 'empresas/empresa_list.html'
    context_object_name = 'empresas'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = EmpresaForm(user=self.request.user)
        return context


class EmpresaUpdateView(LoginRequiredMixin, UpdateView):
    model = Empresa
    form_class = EmpresaForm
    template_name = 'empresas/empresa_edit.html'
    success_url = reverse_lazy('dashboard')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_queryset(self):
        """Permitir editar apenas a empresa vinculada ao usuário"""
        qs = super().get_queryset()
        user = self.request.user
        
        # Superuser vê tudo
        if user.is_superuser or user.is_staff:
            return qs
        
        # Usuário normal só pode editar sua empresa
        allowed_ids = get_allowed_empresa_ids(user)
        if allowed_ids is None:
            return qs
        if not allowed_ids:
            return qs.none()
        return qs.filter(codigo__in=allowed_ids)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        allowed_ids = get_allowed_empresa_ids(self.request.user)
        if allowed_ids is None:
            empresas = Empresa.objects.all()
        else:
            empresas = Empresa.objects.filter(codigo__in=allowed_ids)
        context['empresas_permitidas'] = empresas
        return context
    def form_valid(self, form):
        messages.success(self.request, '✅ Empresa atualizada com sucesso.')
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'Foram encontradas inconsistencias nas informacoes enviadas. Revise as informacoes.')
        return super().form_invalid(form)
