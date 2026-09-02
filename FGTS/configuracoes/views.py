from django.shortcuts import render, redirect
from django.views.generic.list import ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from .models import Configuracao


class ConfiguracaoListView(LoginRequiredMixin, ListView):
    """Listar configurações do sistema (apenas para admin)."""
    model = Configuracao
    template_name = 'configuracoes/configuracao_list.html'
    context_object_name = 'configuracoes'

    def dispatch(self, request, *args, **kwargs):
        """Garante que apenas admin possa acessar."""
        if not request.user.is_staff:
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)


@login_required
def toggle_exibir_indice(request):
    """Alterna a exibição da coluna Índice nos relatórios (salvo na sessão do usuário)."""
    current = request.session.get('exibir_indice', False)
    request.session['exibir_indice'] = not current
    next_url = request.META.get('HTTP_REFERER') or '/'
    return redirect(next_url)


@login_required
def toggle_exibir_jam(request):
    """Alterna a exibição da coluna JAM nos relatórios (salvo na sessão do usuário)."""
    current = request.session.get('exibir_jam', True)
    request.session['exibir_jam'] = not current
    next_url = request.META.get('HTTP_REFERER') or '/'
    return redirect(next_url)


@login_required
def toggle_exibir_correcao(request):
    """Alterna a exibição da coluna Correção nos relatórios (salvo na sessão do usuário)."""
    current = request.session.get('exibir_correcao', True)
    request.session['exibir_correcao'] = not current
    next_url = request.META.get('HTTP_REFERER') or '/'
    return redirect(next_url)
