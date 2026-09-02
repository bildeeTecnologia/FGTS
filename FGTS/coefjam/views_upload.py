from django.contrib.auth.mixins import UserPassesTestMixin, LoginRequiredMixin
from django.views.generic.edit import FormView
from django.urls import reverse_lazy
from django.shortcuts import redirect
from .forms import CoefJamUploadForm
from .models import CoefJam
import io
import datetime

class CoefJamUploadView(LoginRequiredMixin, UserPassesTestMixin, FormView):
    template_name = 'coefjam/coefjam_upload.html'
    form_class = CoefJamUploadForm
    success_url = reverse_lazy('coefjam-list')

    def test_func(self):
        return self.request.user.is_superuser or self.request.user.is_staff

    def form_valid(self, form):
        arquivo = form.cleaned_data['arquivo']
        # Limpa todos os dados antigos
        CoefJam.objects.all().delete()
        # Lê e importa os novos dados
        linhas = io.TextIOWrapper(arquivo.file, encoding='utf-8').readlines()
        novos = []
        for linha in linhas:
            linha = linha.strip()
            if not linha:
                continue
            # Exemplo: 0120210002466
            competencia = f"01/{linha[2:6]}"
            valor = float("0." + linha[12:])
            data_pagamento = datetime.date(int(linha[4:8]), int(linha[2:4]), 1)
            novos.append(CoefJam(competencia=competencia, valor=valor, data_pagamento=data_pagamento))
        CoefJam.objects.bulk_create(novos)
        return super().form_valid(form)
