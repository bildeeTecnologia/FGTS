from django.shortcuts import render
from django.views.generic.list import ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import CoefJam


class CoefJamListView(LoginRequiredMixin, ListView):
    """Listar coeficientes JAM."""
    model = CoefJam
    template_name = 'coefjam/coefjam_list.html'
    context_object_name = 'coeficientes'
    paginate_by = 50
    
    def get_queryset(self):
        """Retorna coeficientes ordenados por data de pagamento (mais recentes primeiro)."""
        return CoefJam.objects.order_by('-data_pagamento')
