from django.shortcuts import render
from django.views.generic.list import ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Indice, SupabaseIndice


class IndiceListView(LoginRequiredMixin, ListView):
    """Listar índices FGTS do banco local e Supabase."""
    template_name = 'indices/indice_list.html'
    context_object_name = 'indices'
    paginate_by = 50
    
    def get_queryset(self):
        """Combina índices locais e do Supabase (quando disponível)."""
        try:
            # Tenta buscar do Supabase primeiro (mais recente)
            return SupabaseIndice.objects.order_by('-data_base')
        except Exception:
            # Fallback para índices locais
            return Indice.objects.order_by('-data_indice')
