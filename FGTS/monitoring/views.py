from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from .services import PerformanceAnalyzer
from .models import PerformanceLog


class DashboardPerformanceView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    """Dashboard de performance do sistema"""
    template_name = 'monitoring/dashboard.html'
    
    def test_func(self):
        """Apenas super users podem acessar"""
        return self.request.user.is_superuser or self.request.user.is_staff
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Resumo últimas 24h
        context['resumo'] = PerformanceAnalyzer.resumo_ultima_24h()
        
        # Top operações lentas
        context['operacoes_lentas'] = PerformanceAnalyzer.top_operacoes_lentas(limite=10)
        
        # Operações por tipo
        context['operacoes_por_tipo'] = PerformanceAnalyzer.operacoes_por_tipo()
        
        # Gargalos identificados
        context['gargalos'] = PerformanceAnalyzer.gargalos_identifıcados()
        
        # Total de logs
        context['total_logs'] = PerformanceLog.objects.count()
        
        return context
