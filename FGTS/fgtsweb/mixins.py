from typing import Iterable, Optional
from django.db.models import QuerySet
from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib import messages
from django.shortcuts import redirect


def get_allowed_empresa_ids(user) -> Optional[list]:
    """Return allowed empresa IDs for the user.
    - None means unrestricted (superuser).
    - Empty list means no access.
    """
    if not getattr(user, "is_authenticated", False):
        return []
    if getattr(user, "is_superuser", False):
        return None
    # Staff deve ter acesso amplo para suporte/ops
    if getattr(user, "is_staff", False):
        return None

    allowed = set()
    base_empresa_ids = set()
    user_empresa = None
    try:
        user_empresa = user.empresa
    except Exception:
        user_empresa = None

    if user_empresa:
        allowed.add(user_empresa.codigo)
        base_empresa_ids.add(user_empresa.codigo)
        # Se e empresa_principal de um grupo, libera todas as empresas do grupo
        try:
            grupo = getattr(user_empresa, "grupo", None)
            if not grupo:
                try:
                    grupo = getattr(user_empresa, "grupo_principal", None)
                except Exception:
                    grupo = None
            if grupo and getattr(grupo, "empresa_principal_id", None) == user_empresa.codigo:
                allowed.update(grupo.empresas.values_list("codigo", flat=True))
        except Exception:
            pass

    if getattr(user, "is_multi_empresa", False):
        try:
            permitted_ids = set(user.empresas_permitidas.values_list("codigo", flat=True))
            base_empresa_ids.update(permitted_ids)
            allowed.update(permitted_ids)
        except Exception:
            # If relation not ready yet, ignore
            pass

    # Se a empresa do usuário for um escritório BPO, libera todas as empresas gerenciadas.
    try:
        from billing.models_bpo import ContaBPO
        conta_bpo = ContaBPO.objects.filter(empresa_bpo_id=user_empresa.codigo).first() if user_empresa else None
        if conta_bpo:
            bpo_empresa_ids = conta_bpo.empresas_gerenciadas.filter(
                status='active'
            ).values_list('empresa_id', flat=True)
            allowed.update(bpo_empresa_ids)
    except Exception:
        pass

    # Se for ADMIN em alguma empresa permitida, libera todo o grupo economico dessa empresa.
    try:
        from usuarios.models import EmpresaUsuarioRole
        from empresas.models import Empresa

        admin_empresa_ids = set(EmpresaUsuarioRole.objects.filter(
            usuario=user,
            role=EmpresaUsuarioRole.ADMIN
        ).values_list("empresa_id", flat=True))

        if base_empresa_ids:
            admin_empresa_ids = admin_empresa_ids.intersection(base_empresa_ids)

        if admin_empresa_ids:
            admin_empresas = Empresa.objects.filter(codigo__in=admin_empresa_ids).select_related("grupo")
            for empresa in admin_empresas:
                grupo = getattr(empresa, "grupo", None)
                if grupo:
                    allowed.update(grupo.empresas.values_list("codigo", flat=True))
    except Exception:
        pass

    return list(allowed)


def is_empresa_allowed(user, empresa_id: int) -> bool:
    allowed = get_allowed_empresa_ids(user)
    if allowed is None:
        return True
    return empresa_id in allowed


def get_active_empresa_ids():
    """Return empresa IDs com billing status ativo ou em trial.
    Se nenhum billing customer existe, retorna todas as empresas."""
    from billing.models import BillingCustomer
    from empresas.models import Empresa
    
    active_billing = BillingCustomer.objects.filter(
        status__in=['active', 'trial']
    ).values_list('empresa__codigo', flat=True)
    
    if active_billing.exists():
        return list(active_billing)
    
    # Se não há clientes de billing, retorna todas as empresas
    return list(Empresa.objects.values_list('codigo', flat=True))


class EmpresaScopeMixin:
    """Mixin to scope querysets by empresa for multi-tenant isolation."""

    def get_allowed_empresa_ids(self) -> Optional[list]:
        return get_allowed_empresa_ids(self.request.user)

    def filter_queryset_by_empresa(self, qs: QuerySet) -> QuerySet:
        allowed = self.get_allowed_empresa_ids()
        if allowed is None:
            return qs
        if not allowed:
            return qs.none()
        model_field_names = {f.name for f in qs.model._meta.fields}
        if "empresa_id" in model_field_names:
            return qs.filter(empresa_id__in=allowed)
        elif "empresa" in model_field_names:
            # Usar lookup direto no campo ForeignKey (por codigo da Empresa)
            return qs.filter(empresa__codigo__in=allowed)
        return qs.none()

    def get_queryset(self):
        qs = super().get_queryset()
        return self.filter_queryset_by_empresa(qs)


# ============ PLAN-BASED AUTHORIZATION MIXINS ============

class PlanFeatureRequiredMixin(UserPassesTestMixin):
    """Verifica se o plano da empresa permite acessar uma feature específica"""
    
    required_feature = None  # Sobrescrever com feature desejada
    
    def test_func(self):
        """Testa se usuário tem acesso à feature"""
        if not self.request.user.is_authenticated:
            return False
        
        try:
            billing_customer = self.request.user.empresa.billing_customer
            
            # ✅ EMPRESAS EM TRIAL TÊM ACESSO TOTAL!
            if billing_customer.status == 'trial':
                return True
            
            plan = billing_customer.plan
        except:
            return False
        
        if not plan:
            return False
        
        # Mapear feature para atributo do modelo Plan
        feature_attr = self.get_feature_attribute()
        return getattr(plan, feature_attr, False)
    
    def get_feature_attribute(self):
        """Retorna o atributo do modelo Plan a verificar"""
        return self.required_feature
    
    def handle_no_permission(self):
        """Redireciona com mensagem amigável"""
        plan_name = self.request.user.empresa.billing_customer.plan.get_plan_type_display()
        messages.error(
            self.request,
            f'Este recurso não está disponível no seu plano {plan_name}. '
            f'Faça upgrade para acessá-lo.'
        )
        return redirect('dashboard')


class AdvancedDashboardRequiredMixin(PlanFeatureRequiredMixin):
    """Requer que o plano tenha has_advanced_dashboard=True"""
    required_feature = 'has_advanced_dashboard'


class CustomReportsRequiredMixin(PlanFeatureRequiredMixin):
    """Requer que o plano tenha has_custom_reports=True"""
    required_feature = 'has_custom_reports'


class PDFExportRequiredMixin(PlanFeatureRequiredMixin):
    """Requer que o plano tenha has_pdf_export=True"""
    required_feature = 'has_pdf_export'


class APIAccessRequiredMixin(PlanFeatureRequiredMixin):
    """Requer que o plano tenha has_api=True"""
    required_feature = 'has_api'

