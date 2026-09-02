from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView
from django.db.models import Q
from .models import AuditLog


class AuditLogListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """View para visualizar logs de auditoria - Apenas admin/staff"""
    model = AuditLog
    template_name = 'audit_logs/auditlog_list.html'
    context_object_name = 'audit_logs'
    paginate_by = 50
    
    def test_func(self):
        """Permitir acesso apenas para staff/admin"""
        return self.request.user.is_staff or self.request.user.is_superuser
    
    def get_queryset(self):
        queryset = AuditLog.objects.all().select_related('user', 'content_type')
        
        # Filtros
        action = self.request.GET.get('action', '').strip()
        user_filter = self.request.GET.get('user', '').strip()
        date_from = self.request.GET.get('date_from', '').strip()
        date_to = self.request.GET.get('date_to', '').strip()
        
        if action:
            queryset = queryset.filter(action=action)
        
        if user_filter:
            queryset = queryset.filter(user__username__icontains=user_filter)
        
        if date_from:
            queryset = queryset.filter(timestamp__date__gte=date_from)
        
        if date_to:
            queryset = queryset.filter(timestamp__date__lte=date_to)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['actions'] = AuditLog.ACTION_CHOICES
        context['action_filter'] = self.request.GET.get('action', '')
        context['user_filter'] = self.request.GET.get('user', '')
        context['date_from'] = self.request.GET.get('date_from', '')
        context['date_to'] = self.request.GET.get('date_to', '')
        return context
