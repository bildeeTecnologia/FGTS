from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from django.utils import timezone

from empresas.models import Empresa
from funcionarios.models import Funcionario
from lancamentos.models import Lancamento
from indices.models import Indice
from coefjam.models import CoefJam
from billing.models import BillingCustomer, Subscription, Payment, PricingPlan
from django.core.cache import cache
from datetime import timedelta
from django.utils import timezone


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'dashboard.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        now = timezone.now()

        # Chave de cache depende do tipo de usuário/empresa
        if self.request.user.is_superuser or self.request.user.is_staff:
            cache_key = 'dashboard_counts_global'
            empresa = None
        else:
            empresa = None
            if self.request.user.empresa_id:
                try:
                    empresa = Empresa.objects.get(pk=self.request.user.empresa_id)
                except (Empresa.DoesNotExist, Exception):
                    empresa = None
            if not empresa:
                try:
                    empresa = self.request.user.empresas_permitidas.first()
                except Exception:
                    empresa = None
            cache_key = f'dashboard_counts_empresa_{empresa.pk if empresa else "none"}'

        # Tenta obter do cache
        counts = cache.get(cache_key)
        if not counts:
            if self.request.user.is_superuser or self.request.user.is_staff:
                ativos_count = Funcionario.objects.filter(vinculos__data_demissao__isnull=True).distinct().count()
                demitidos_count = Funcionario.objects.filter(vinculos__data_demissao__isnull=False).distinct().count()
                total_count = Funcionario.objects.all().count()
                lancs_total = Lancamento.objects.count()
                lancs_pendentes = Lancamento.objects.filter(pago=False).count()
            elif empresa:
                ativos_count = Funcionario.objects.filter(vinculos__empresa=empresa, vinculos__data_demissao__isnull=True).distinct().count()
                demitidos_count = Funcionario.objects.filter(vinculos__empresa=empresa, vinculos__data_demissao__isnull=False).distinct().count()
                total_count = Funcionario.objects.filter(vinculos__empresa=empresa).distinct().count()
                lancs_total = Lancamento.objects.filter(empresa=empresa).count()
                lancs_pendentes = Lancamento.objects.filter(empresa=empresa, pago=False).count()
            else:
                ativos_count = demitidos_count = total_count = lancs_total = lancs_pendentes = 0
            counts = {
                'ativos_count': ativos_count,
                'demitidos_count': demitidos_count,
                'total_count': total_count,
                'lancs_total': lancs_total,
                'lancs_pendentes': lancs_pendentes,
            }
            cache.set(cache_key, counts, timeout=30)  # 30 segundos
        else:
            ativos_count = counts.get('ativos_count', 0)
            demitidos_count = counts.get('demitidos_count', 0)
            total_count = counts.get('total_count', 0)
            lancs_total = counts.get('lancs_total', 0)
            lancs_pendentes = counts.get('lancs_pendentes', 0)

        ctx['ativos_count'] = ativos_count
        ctx['demitidos_count'] = demitidos_count
        ctx['total_count'] = total_count
        ctx['lancs_total'] = lancs_total
        ctx['lancs_pendentes'] = lancs_pendentes

        # Buscar informações de billing/trial através da empresa
        billing_customer = None
        if empresa:
            try:
                billing_customer = BillingCustomer.objects.filter(empresa=empresa).first()
            except Exception:
                billing_customer = None

        # Definir plano atual baseado em billing_customer
        current_plan = None
        # Corrigir: se trial expirou, não mostrar plano premium/trial
        if billing_customer:
            # Se trial expirou, não mostrar plano premium
            if billing_customer.trial_active and hasattr(billing_customer, 'trial_expires') and billing_customer.trial_expires:
                from datetime import date
                if date.today() > billing_customer.trial_expires:
                    billing_customer.trial_active = False
                    if billing_customer.status == 'trial':
                        billing_customer.status = 'pending'
                    billing_customer.save()
            if billing_customer.trial_active:
                current_plan = billing_customer.plan
            elif billing_customer.status == 'active' and billing_customer.plan:
                current_plan = billing_customer.plan
            else:
                current_plan = None
        else:
            current_plan = PricingPlan.objects.filter(active=True).order_by('sort_order', '-updated_at').first()

        ctx.update({
            'lancs_total': lancs_total,
            'lancs_pendentes': lancs_pendentes,
            'empresa': empresa,
            'billing_customer': billing_customer,
            'current_plan': current_plan,
            'now': now,
        })
        return ctx
