from django.views import View
from django.http import JsonResponse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404
from django.contrib import messages
from .models import Lancamento
from fgtsweb.mixins import is_empresa_allowed

class LancamentoBulkDeleteView(LoginRequiredMixin, View):
    def post(self, request):
        ids = request.POST.getlist('ids[]')
        deleted = 0
        errors = []
        for pk in ids:
            lancamento = get_object_or_404(Lancamento, pk=pk)
            if not is_empresa_allowed(request.user, lancamento.empresa.codigo):
                errors.append(f"Sem permissão para excluir lançamento {pk}")
                continue
            lancamento.delete()
            deleted += 1
        if errors:
            return JsonResponse({'success': False, 'deleted': deleted, 'errors': errors}, status=403)
        return JsonResponse({'success': True, 'deleted': deleted})
