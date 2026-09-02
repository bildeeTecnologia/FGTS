"""
Views para importação de arquivos RE (SEFIP) e Extrato Analítico (CEF).

Segue o mesmo padrão das views existentes de importação XLSX:
  Upload → Preview síncrono → Confirmar → Processar em background → Status com polling.
"""

import time
import threading

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.generic import View

from empresas.models import Empresa
from empresas.models_feature import empresa_tem_recurso
from fgtsweb.mixins import EmpresaScopeMixin, get_allowed_empresa_ids, is_empresa_allowed
from lancamentos.models import ImportacaoExtratoAnalitico, ImportacaoRE
from lancamentos.services.extrato_analitico_service import ExtratoAnaliticoService, ExtratoImportError
from lancamentos.services.re_importer_service import REImporterService, REImportError


# ---------------------------------------------------------------------------
# Helpers de background
# ---------------------------------------------------------------------------

def _process_importacao_re(importacao_id: int):
    """Processa ImportacaoRE em thread background."""
    from django.db import connection

    importacao = None
    try:
        importacao = ImportacaoRE.objects.get(id=importacao_id)
        importacao.status = 'processing'
        importacao.save(update_fields=['status', 'atualizado_em'])

        last_update = [0.0]

        def on_progress(processados, total):
            nonlocal last_update
            now = time.time()
            if processados == 0:
                importacao.linhas_total = total
                importacao.save(update_fields=['linhas_total', 'atualizado_em'])
                last_update[0] = now
            elif now - last_update[0] >= 2.0:
                importacao.linhas_processadas = processados
                importacao.save(update_fields=['linhas_processadas', 'atualizado_em'])
                last_update[0] = now

        svc = REImporterService()
        with open(importacao.arquivo.path, 'rb') as f:
            arquivo_bytes = f.read()

        empresa = importacao.empresa
        resultado = svc.importar(
            arquivo_bytes,
            tipo=importacao.tipo_fonte,
            empresa=empresa,
            progress_callback=on_progress,
        )

        importacao.status = 'done'
        importacao.resultado_json = resultado
        importacao.save(update_fields=['status', 'resultado_json', 'atualizado_em'])

    except Exception as exc:
        try:
            if importacao is None:
                importacao = ImportacaoRE.objects.get(id=importacao_id)
            importacao.status = 'error'
            importacao.mensagem_erro = str(exc)
            importacao.save(update_fields=['status', 'mensagem_erro', 'atualizado_em'])
        except Exception:
            pass
    finally:
        connection.close()


def _process_importacao_extrato(importacao_id: int):
    """Processa ImportacaoExtratoAnalitico em thread background."""
    from django.db import connection

    importacao = None
    try:
        importacao = ImportacaoExtratoAnalitico.objects.get(id=importacao_id)
        importacao.status = 'processing'
        importacao.save(update_fields=['status', 'atualizado_em'])

        last_update = [0.0]

        def on_progress(processados, total):
            now = time.time()
            if processados == 0:
                importacao.linhas_total = total
                importacao.save(update_fields=['linhas_total', 'atualizado_em'])
                last_update[0] = now
            elif now - last_update[0] >= 2.0:
                importacao.linhas_processadas = processados
                importacao.save(update_fields=['linhas_processadas', 'atualizado_em'])
                last_update[0] = now

        svc = ExtratoAnaliticoService()
        with open(importacao.arquivo.path, 'rb') as f:
            xlsx_bytes = f.read()

        resultado = svc.importar(xlsx_bytes, progress_callback=on_progress)

        importacao.status = 'done'
        importacao.resultado_json = resultado
        importacao.save(update_fields=['status', 'resultado_json', 'atualizado_em'])

    except Exception as exc:
        try:
            if importacao is None:
                importacao = ImportacaoExtratoAnalitico.objects.get(id=importacao_id)
            importacao.status = 'error'
            importacao.mensagem_erro = str(exc)
            importacao.save(update_fields=['status', 'mensagem_erro', 'atualizado_em'])
        except Exception:
            pass
    finally:
        connection.close()


# ---------------------------------------------------------------------------
# Views RE / SEFIP
# ---------------------------------------------------------------------------

class REImportView(LoginRequiredMixin, EmpresaScopeMixin, View):
    """Upload de arquivo RE (.RE texto) ou PDF visual do SEFIP."""

    template_name = 'lancamentos/re_import.html'

    def get(self, request, *args, **kwargs):
        empresa_ids = get_allowed_empresa_ids(request.user)
        empresas = (
            Empresa.objects.filter(codigo__in=empresa_ids)
            if empresa_ids is not None
            else Empresa.objects.all()
        ).order_by('nome')

        if not request.user.is_staff:
            empresas_liberadas = [e for e in empresas if empresa_tem_recurso(e, 'importar_re_sefip')]
            if not empresas_liberadas:
                return render(request, self.template_name, {
                    'erro': 'Seu acesso ao importador RE/SEFIP não está habilitado. Contate o administrador.',
                    'empresas': [],
                })
            empresas = empresas_liberadas

        return render(request, self.template_name, {'empresas': empresas})

    def post(self, request, *args, **kwargs):
        if 'file' not in request.FILES:
            return render(request, self.template_name, {'erro': 'Nenhum arquivo foi enviado.'})

        file = request.FILES['file']
        nome = file.name.lower()

        if not (nome.endswith('.re') or nome.endswith('.txt') or nome.endswith('.pdf')):
            return render(request, self.template_name, {
                'erro': 'Formato inválido. Envie um arquivo .RE, .TXT ou .PDF do SEFIP.',
                'empresas': self._get_empresas(request),
            })

        tipo_fonte = 'pdf' if nome.endswith('.pdf') else 're_texto'

        empresa = None
        empresa_codigo = request.POST.get('empresa')
        if empresa_codigo:
            try:
                empresa = Empresa.objects.get(codigo=empresa_codigo)
                if not is_empresa_allowed(request.user, empresa.codigo):
                    return render(request, self.template_name, {
                        'erro': 'Empresa não permitida para este usuário.',
                        'empresas': self._get_empresas(request),
                    })
            except Empresa.DoesNotExist:
                return render(request, self.template_name, {
                    'erro': 'Empresa não encontrada.',
                    'empresas': self._get_empresas(request),
                })

        if empresa and not request.user.is_staff and not empresa_tem_recurso(empresa, 'importar_re_sefip'):
            return render(request, self.template_name, {
                'erro': 'Importação RE/SEFIP não habilitada para esta empresa. Contate o administrador.',
                'empresas': self._get_empresas(request),
            })

        importacao = ImportacaoRE.objects.create(
            usuario=request.user,
            empresa=empresa,
            arquivo=file,
            nome_arquivo=file.name,
            tipo_fonte=tipo_fonte,
            status='preview',
        )

        try:
            svc = REImporterService()
            with open(importacao.arquivo.path, 'rb') as f:
                arquivo_bytes = f.read()
            preview = svc.preview(arquivo_bytes, tipo=tipo_fonte, empresa=empresa)
            importacao.preview_resultado = preview
            importacao.save(update_fields=['preview_resultado', 'atualizado_em'])
        except (REImportError, Exception) as exc:
            importacao.delete()
            return render(request, self.template_name, {
                'erro': str(exc),
                'empresas': self._get_empresas(request),
            })

        return redirect('re-import-preview', pk=importacao.pk)

    def _get_empresas(self, request):
        empresa_ids = get_allowed_empresa_ids(request.user)
        qs = (
            Empresa.objects.filter(codigo__in=empresa_ids)
            if empresa_ids is not None
            else Empresa.objects.all()
        )
        return qs.order_by('nome')


class REImportPreviewView(LoginRequiredMixin, View):
    """Pré-visualização da amostra do arquivo RE antes de confirmar."""

    def get(self, request, pk):
        importacao = get_object_or_404(ImportacaoRE, pk=pk, usuario=request.user, status='preview')
        return render(request, 'lancamentos/re_import_preview.html', {'importacao': importacao})

    def post(self, request, pk):
        return redirect('re-import-confirm', pk=pk)


class REImportConfirmView(LoginRequiredMixin, View):
    """Confirma o import RE e dispara processamento em background."""

    def post(self, request, pk):
        importacao = get_object_or_404(ImportacaoRE, pk=pk, usuario=request.user, status='preview')
        importacao.status = 'pending'
        importacao.save(update_fields=['status', 'atualizado_em'])
        threading.Thread(
            target=_process_importacao_re,
            args=(importacao.id,),
            daemon=True,
        ).start()
        return redirect('re-import-status', pk=importacao.pk)


class REImportStatusView(LoginRequiredMixin, View):
    """Página de acompanhamento com polling do importador RE."""

    def get(self, request, pk):
        importacao = get_object_or_404(ImportacaoRE, pk=pk, usuario=request.user)
        return render(request, 'lancamentos/re_import_status.html', {'importacao': importacao})


@login_required
def re_import_status_json(request, pk):
    """Endpoint JSON para polling do importador RE."""
    importacao = get_object_or_404(ImportacaoRE, pk=pk, usuario=request.user)
    return JsonResponse({
        'status': importacao.status,
        'resultado': importacao.resultado_json,
        'erro': importacao.mensagem_erro,
        'linhas_total': importacao.linhas_total,
        'linhas_processadas': importacao.linhas_processadas,
    })


# ---------------------------------------------------------------------------
# Views Extrato Analítico
# ---------------------------------------------------------------------------

class ExtratoImportView(LoginRequiredMixin, EmpresaScopeMixin, View):
    """Upload do Extrato Analítico XLSX da CEF."""

    template_name = 'lancamentos/extrato_import.html'

    def get(self, request, *args, **kwargs):
        if not request.user.is_staff:
            empresa_ids = get_allowed_empresa_ids(request.user)
            empresas = (
                Empresa.objects.filter(codigo__in=empresa_ids)
                if empresa_ids is not None
                else Empresa.objects.all()
            )
            if not any(empresa_tem_recurso(e, 'importar_extrato_cef') for e in empresas):
                return render(request, self.template_name, {
                    'erro': 'Importação de Extrato CEF não habilitada para sua empresa. Contate o administrador.',
                })
        return render(request, self.template_name, {})

    def post(self, request, *args, **kwargs):
        if 'file' not in request.FILES:
            return render(request, self.template_name, {'erro': 'Nenhum arquivo foi enviado.'})

        file = request.FILES['file']
        if not file.name.lower().endswith('.xlsx'):
            return render(request, self.template_name, {
                'erro': 'Formato inválido. Envie o arquivo XLSX do Extrato Analítico.',
            })

        if not request.user.is_staff:
            empresa_ids = get_allowed_empresa_ids(request.user)
            empresas = (
                Empresa.objects.filter(codigo__in=empresa_ids)
                if empresa_ids is not None
                else Empresa.objects.all()
            )
            if not any(empresa_tem_recurso(e, 'importar_extrato_cef') for e in empresas):
                return render(request, self.template_name, {
                    'erro': 'Importação de Extrato CEF não habilitada para sua empresa. Contate o administrador.',
                })

        importacao = ImportacaoExtratoAnalitico.objects.create(
            usuario=request.user,
            arquivo=file,
            nome_arquivo=file.name,
            status='preview',
        )

        try:
            svc = ExtratoAnaliticoService()
            with open(importacao.arquivo.path, 'rb') as f:
                xlsx_bytes = f.read()
            preview = svc.preview(xlsx_bytes)
            importacao.preview_resultado = preview
            importacao.save(update_fields=['preview_resultado', 'atualizado_em'])
        except (ExtratoImportError, Exception) as exc:
            importacao.delete()
            return render(request, self.template_name, {'erro': str(exc)})

        return redirect('extrato-import-preview', pk=importacao.pk)


class ExtratoImportPreviewView(LoginRequiredMixin, View):
    """Pré-visualização dos registros do Extrato antes de confirmar."""

    def get(self, request, pk):
        importacao = get_object_or_404(
            ImportacaoExtratoAnalitico, pk=pk, usuario=request.user, status='preview'
        )
        return render(request, 'lancamentos/extrato_import_preview.html', {'importacao': importacao})


class ExtratoImportConfirmView(LoginRequiredMixin, View):
    """Confirma o import do Extrato e dispara processamento em background."""

    def post(self, request, pk):
        importacao = get_object_or_404(
            ImportacaoExtratoAnalitico, pk=pk, usuario=request.user, status='preview'
        )
        importacao.status = 'pending'
        importacao.save(update_fields=['status', 'atualizado_em'])
        threading.Thread(
            target=_process_importacao_extrato,
            args=(importacao.id,),
            daemon=True,
        ).start()
        return redirect('extrato-import-status', pk=importacao.pk)


class ExtratoImportStatusView(LoginRequiredMixin, View):
    """Página de acompanhamento com polling do importador de Extrato."""

    def get(self, request, pk):
        importacao = get_object_or_404(ImportacaoExtratoAnalitico, pk=pk, usuario=request.user)
        return render(request, 'lancamentos/extrato_import_status.html', {'importacao': importacao})


@login_required
def extrato_import_status_json(request, pk):
    """Endpoint JSON para polling do importador de Extrato."""
    importacao = get_object_or_404(ImportacaoExtratoAnalitico, pk=pk, usuario=request.user)
    return JsonResponse({
        'status': importacao.status,
        'resultado': importacao.resultado_json,
        'erro': importacao.mensagem_erro,
        'linhas_total': importacao.linhas_total,
        'linhas_processadas': importacao.linhas_processadas,
    })


class ExtratoImportDownloadRelatorioView(LoginRequiredMixin, View):
    """Gera e baixa o relatório XLSX de uma importação de extrato analítico."""

    def get(self, request, pk):
        from django.http import HttpResponse
        from .services.import_report_service import gerar_relatorio_extrato
        importacao = get_object_or_404(ImportacaoExtratoAnalitico, pk=pk, usuario=request.user)
        if importacao.status != 'done':
            return HttpResponse('Relatório disponível apenas após o processamento.', status=400)
        xlsx_bytes = gerar_relatorio_extrato(importacao)
        response = HttpResponse(
            xlsx_bytes,
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        )
        response['Content-Disposition'] = (
            f'attachment; filename="relatorio_extrato_{pk}.xlsx"'
        )
        return response
