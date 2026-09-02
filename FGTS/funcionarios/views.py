print('DEBUG: Arquivo views.py carregado', flush=True)
from django.shortcuts import render, redirect
from django.db import models
from django.db.models import OuterRef, Subquery
from django.urls import reverse_lazy
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views.generic.list import ListView
from django.views.generic.base import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.http import HttpResponseForbidden, HttpResponse, JsonResponse
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from fgtsweb.mixins import EmpresaScopeMixin, get_allowed_empresa_ids, is_empresa_allowed, get_active_empresa_ids
from .models import Funcionario
from .forms import FuncionarioForm, FuncionarioVinculoForm
from .forms_transferencia import TransferenciaFuncionarioForm
from .services import FuncionarioImportService, VinculoUpdateService
from empresas.models import Empresa
from billing.models import BillingCustomer
from io import BytesIO
from django.core.cache import cache
from django.views.generic.detail import DetailView
from empresas.models_grupo import TransferenciaFuncionario, FuncionarioVinculo, get_aliquota_fgts
from usuarios.models import EmpresaUsuarioRole
from audit_logs.models import AuditLog
from lancamentos.models import Lancamento
from decimal import Decimal

class FuncionarioCreateView(LoginRequiredMixin, EmpresaScopeMixin, CreateView):
    model = Funcionario
    form_class = FuncionarioForm
    template_name = 'funcionarios/funcionario_form.html'
    success_url = reverse_lazy('funcionario-list')

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        allowed_ids = get_allowed_empresa_ids(self.request.user)
        if allowed_ids is not None:
            form.fields['empresa'].queryset = Empresa.objects.filter(codigo__in=allowed_ids)
        return form

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        allowed_ids = get_allowed_empresa_ids(self.request.user)
        if allowed_ids is None:
            empresas = Empresa.objects.all()
        else:
            empresas = Empresa.objects.filter(codigo__in=allowed_ids)
        context['empresas_permitidas'] = empresas
        return context

    def form_valid(self, form):
        empresa = form.cleaned_data.get('empresa')
        if empresa and not is_empresa_allowed(self.request.user, empresa.codigo):
            return HttpResponseForbidden('Empresa não permitida para este usuário.')
        funcionario = form.save()
        messages.success(self.request, f'✅ Funcionário "{funcionario.nome}" cadastrado com sucesso!')
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'Foram encontradas inconsistencias nas informacoes enviadas. Revise as informacoes.')
        return super().form_invalid(form)

class FuncionarioListView(LoginRequiredMixin, EmpresaScopeMixin, ListView):
    model = Funcionario
    template_name = 'funcionarios/funcionario_list.html'
    context_object_name = 'funcionarios'
    paginate_by = 20

    def get_queryset(self):
        qs = Funcionario.objects.all()
        user = self.request.user
        allowed = get_allowed_empresa_ids(user)

        # Escopo por empresas permitidas (inclui grupo para matriz)
        if allowed is not None:
            if not allowed:
                return qs.none()
            qs = qs.filter(vinculos__empresa_id__in=allowed)

        # Filtros de UI
        empresa_id = self.request.GET.get('empresa')
        status = self.request.GET.get('status')

        # Se empresa e status estão definidos, filtrar por vínculo específico
        if empresa_id and status:
            qs = qs.filter(
                vinculos__empresa_id=empresa_id,
                vinculos__status=status
            )
        elif empresa_id:
            # Se apenas empresa está definida, filtrar por qualquer vínculo com aquela empresa
            qs = qs.filter(vinculos__empresa_id=empresa_id)
        elif status:
            # Se apenas status está definido, filtrar por status em qualquer vínculo
            qs = qs.filter(vinculos__status=status)

        busca = self.request.GET.get('q')
        if busca:
            busca = busca.strip()
            filtros = (
                models.Q(nome__icontains=busca) |
                models.Q(cpf__icontains=busca) |
                models.Q(pis__icontains=busca) |
                models.Q(vinculos__matricula__icontains=busca)
            )
            if busca.isdigit() and busca.startswith('0'):
                busca_sem_zeros = busca.lstrip('0') or '0'
                filtros |= models.Q(vinculos__matricula__icontains=busca_sem_zeros)
            qs = qs.filter(filtros)

        ordenar = self.request.GET.get('ordenar')
        if ordenar == 'nome':
            qs = qs.order_by('nome')
        elif ordenar == 'matricula':
            qs = qs.order_by('vinculos__matricula')
        elif ordenar == 'empresa':
            qs = qs.order_by('vinculos__empresa__nome')
        elif ordenar == 'admissao':
            qs = qs.order_by('vinculos__data_admissao')
        return qs.distinct()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        queryset = self.get_queryset()

        # Contagem baseada no vínculo mais recente (status atual)
        latest_vinculo = FuncionarioVinculo.objects.filter(
            funcionario=OuterRef('pk')
        ).order_by('-data_admissao', '-id')

        annotated = queryset.annotate(
            status_atual=Subquery(latest_vinculo.values('status')[:1])
        )

        context['ativos_count'] = annotated.filter(status_atual='ativo').count()
        context['transferidos_count'] = annotated.filter(status_atual='transferido').count()
        context['demitidos_count'] = annotated.filter(status_atual='demitido').count()
        context['total_count'] = annotated.count()
        context['form'] = FuncionarioForm()
        allowed_ids = get_allowed_empresa_ids(self.request.user)
        if allowed_ids is None:
            empresas = Empresa.objects.all()
        else:
            empresas = Empresa.objects.filter(codigo__in=allowed_ids)
        context['empresas_permitidas'] = empresas
        context['filtro_empresa'] = self.request.GET.get('empresa', '')
        context['filtro_status'] = self.request.GET.get('status', '')
        context['filtro_busca'] = self.request.GET.get('q', '')
        context['filtro_ordenar'] = self.request.GET.get('ordenar', '')
        # Permissões de recursos para botões de ação
        from empresas.models_feature import empresa_tem_recurso
        empresa = None
        user = self.request.user

        # Resolver empresa base para o usuário
        if user.is_superuser or user.is_staff:
            context['can_add_funcionario'] = True
            context['can_gerar_relatorio'] = True
            return context

        if user.empresa_id:
            try:
                empresa = Empresa.objects.get(pk=user.empresa_id)
            except (Empresa.DoesNotExist, Exception):
                empresa = None
        if not empresa:
            try:
                empresa = user.empresas_permitidas.first()
            except Exception:
                empresa = None

        # Regras de habilitação: feature flag OU billing ativo/trial
        can_add = empresa_tem_recurso(empresa, 'criar_funcionario') if empresa else False
        can_report = empresa_tem_recurso(empresa, 'gerar_relatorio') if empresa else False

        if empresa and not can_add:
            try:
                billing_customer = empresa.billing_customer
                if billing_customer.status in ['trial', 'active']:
                    can_add = True
            except Exception:
                pass

        context['can_add_funcionario'] = can_add
        context['can_gerar_relatorio'] = can_report
        # Permissão para transferir: superuser/staff ou admin (role) em ao menos uma empresa permitida
        if user.is_superuser or user.is_staff:
            context['can_transfer_funcionario'] = True
        else:
            permitted_ids = list(allowed_ids) if allowed_ids is not None else []
            context['can_transfer_funcionario'] = EmpresaUsuarioRole.objects.filter(
                usuario=user,
                role=EmpresaUsuarioRole.ADMIN,
                empresa_id__in=permitted_ids
            ).exists() if permitted_ids else False
        return context


class FuncionarioUpdateView(LoginRequiredMixin, EmpresaScopeMixin, UpdateView):
    model = Funcionario
    form_class = FuncionarioForm
    template_name = 'funcionarios/funcionario_form.html'
    success_url = reverse_lazy('funcionario-list')

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        allowed_ids = get_allowed_empresa_ids(self.request.user)
        if allowed_ids is not None:
            form.fields['empresa'].queryset = Empresa.objects.filter(codigo__in=allowed_ids)
        return form

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        allowed_ids = get_allowed_empresa_ids(self.request.user)
        if allowed_ids is None:
            empresas = Empresa.objects.all()
        else:
            empresas = Empresa.objects.filter(codigo__in=allowed_ids)
        context['empresas_permitidas'] = empresas
        return context

    def get_queryset(self):
        # Não podemos usar super() aqui porque EmpresaScopeMixin filtra por campos
        # de empresa inexistentes neste modelo e derruba o queryset para vazio.
        qs = Funcionario.objects.all()
        allowed = get_allowed_empresa_ids(self.request.user)
        if allowed is None:
            return qs
        if not allowed:
            return qs.none()
        # Filtra por empresas permitidas via vínculos (multi-empresa)
        return qs.filter(vinculos__empresa_id__in=allowed).distinct()

    def form_valid(self, form):
        empresa = form.cleaned_data.get('empresa')
        if empresa and not is_empresa_allowed(self.request.user, empresa.codigo):
            return HttpResponseForbidden('Empresa não permitida para este usuário.')

        # Captura tipo_vinculo ANTES de salvar para detectar mudança e aplicar restrição
        funcionario_obj = self.get_object()
        old_vinculo = funcionario_obj.vinculo_atual()
        old_tipo = old_vinculo.tipo_vinculo if old_vinculo else None
        new_tipo = form.cleaned_data.get('tipo_vinculo')

        is_admin = self.request.user.is_staff or self.request.user.is_superuser
        tipo_mudou = old_tipo != new_tipo

        # Regra: usuário regular não pode mudar Aprendiz → outro tipo
        if (
            tipo_mudou
            and old_tipo is not None
            and old_tipo.codigo == 'APRENDIZ'
            and not is_admin
        ):
            form.add_error(
                'tipo_vinculo',
                'Para efetivação de Aprendiz como CLT, encerre este vínculo e crie um novo. '
                'Se for um cadastro incorreto, solicite a correção ao administrador da plataforma.'
            )
            return self.form_invalid(form)

        funcionario = form.save()
        vinculo_atualizado = funcionario.vinculo_atual()

        if tipo_mudou and vinculo_atualizado:
            ip = self.request.META.get('HTTP_X_FORWARDED_FOR', self.request.META.get('REMOTE_ADDR', ''))
            AuditLog.objects.create(
                user=self.request.user,
                action='UPDATE',
                module='funcionarios',
                view_name='FuncionarioUpdateView',
                url_path=self.request.path,
                ip_address=(ip.split(',')[0].strip() if ip else None),
                user_agent=self.request.META.get('HTTP_USER_AGENT', '')[:500],
                method='POST',
                status_code=302,
                object_id=vinculo_atualizado.pk,
                object_repr=f'Vínculo #{vinculo_atualizado.pk} — {funcionario.nome}',
                description=(
                    f'Tipo de vínculo alterado de '
                    f'"{old_tipo.descricao if old_tipo else "CLT (padrão)"}" para '
                    f'"{new_tipo.descricao if new_tipo else "CLT (padrão)"}"'
                ),
                old_values={'tipo_vinculo': str(old_tipo) if old_tipo else 'CLT (padrão)'},
                new_values={'tipo_vinculo': str(new_tipo) if new_tipo else 'CLT (padrão)'},
            )
            messages.success(
                self.request,
                f'✅ Tipo de vínculo de "{funcionario.nome}" atualizado com sucesso.'
            )
            return redirect('vinculo-recalcular', pk=funcionario.pk, vid=vinculo_atualizado.pk)

        messages.success(self.request, f'✅ Funcionário "{funcionario.nome}" atualizado com sucesso!')
        return redirect(self.success_url)

    def form_invalid(self, form):
        messages.error(self.request, 'Foram encontradas inconsistencias nas informacoes enviadas. Revise as informacoes.')
        return super().form_invalid(form)


class FuncionarioDeleteView(LoginRequiredMixin, EmpresaScopeMixin, DeleteView):
    model = Funcionario
    template_name = 'funcionarios/funcionario_confirm_delete.html'
    success_url = reverse_lazy('funcionario-list')

    def get_queryset(self):
        # Evita filtro vazio do EmpresaScopeMixin em modelos sem campo empresa
        qs = Funcionario.objects.all()
        allowed = get_allowed_empresa_ids(self.request.user)
        if allowed is None:
            return qs
        if not allowed:
            return qs.none()
        return qs.filter(vinculos__empresa_id__in=allowed).distinct()

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        nome = self.object.nome
        response = super().delete(request, *args, **kwargs)
        messages.success(request, f'✅ Funcionário "{nome}" excluído com sucesso!')
        return response

class FuncionarioDownloadTemplateView(LoginRequiredMixin, View):
    """Download do modelo XLSX para importação de funcionários"""
    
    def get(self, request):
        try:
            wb = FuncionarioImportService.generate_template_xlsx()
            
            # Salvar em BytesIO
            output = BytesIO()
            wb.save(output)
            output.seek(0)
            
            # Preparar resposta
            response = HttpResponse(
                output.getvalue(),
                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
            response['Content-Disposition'] = f'attachment; filename="modelo_funcionarios_{datetime.now().strftime("%d_%m_%Y")}.xlsx"'
            
            return response
        except Exception as e:
            messages.error(request, f'❌ Erro ao gerar modelo: {str(e)}')
            return redirect('funcionario-list')


class FuncionarioUploadImportView(LoginRequiredMixin, EmpresaScopeMixin, View):
    """Upload e processamento de importação em lote"""
    
    def post(self, request):
        try:
            # Validar arquivo
            if 'import_file' not in request.FILES:
                return JsonResponse({'success': False, 'error': 'Nenhum arquivo foi enviado'}, status=400)
            
            file = request.FILES['import_file']
            
            # Validar extensão
            if not file.name.endswith('.xlsx'):
                return JsonResponse({'success': False, 'error': 'Por favor, envie um arquivo XLSX'}, status=400)
            
            # Obter empresa se fornecida
            empresa_id = request.POST.get('empresa_id')
            
            # Processar importação com validações de permissão e billing
            result = FuncionarioImportService.import_funcionarios_from_file(
                file=file,
                empresa_id=empresa_id,
                user=request.user
            )
            
            # Preparar resposta com IDs dos funcionários criados
            response_data = {
                'success': result['success'] > 0,
                'total': result['total'],
                'success_count': result['success'],
                'error_count': len(result['errors']),
                'errors': result['errors'],  # Todos os erros
                'created_ids': result['created_funcionarios'],
                'message': f"✅ {result['success']} funcionário(s) importado(s) com sucesso!"
            }
            
            if result['errors']:
                response_data['message'] = 'Foram encontradas inconsistencias nas informacoes enviadas. Revise as informacoes.'
                response_data['message'] += f" ⚠️ {len(result['errors'])} erro(s) encontrado(s)."
            
            return JsonResponse(response_data)
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Erro na importação: {str(e)}", exc_info=True)
            return JsonResponse({'success': False, 'error': f'Erro ao processar arquivo: {str(e)}'}, status=400)


class VinculoUploadUpdateView(LoginRequiredMixin, EmpresaScopeMixin, View):
    """Recebe XLSX e atualiza vínculos existentes em lote."""

    def post(self, request):
        if 'import_file' not in request.FILES:
            return JsonResponse({'success': False, 'error': 'Nenhum arquivo foi enviado.'}, status=400)

        file = request.FILES['import_file']
        if not file.name.endswith('.xlsx'):
            return JsonResponse({'success': False, 'error': 'Por favor, envie um arquivo XLSX.'}, status=400)

        try:
            result = VinculoUpdateService.update_vinculos_from_file(file=file, user=request.user)
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)

        response_data = {
            'success': result['success'] > 0,
            'total': result['total'],
            'success_count': result['success'],
            'error_count': len(result['errors']),
            'errors': result['errors'],
            'message': f"✅ {result['success']} vínculo(s) atualizado(s) com sucesso!",
        }
        if result['errors']:
            response_data['message'] += f" ⚠️ {len(result['errors'])} erro(s) encontrado(s)."
        return JsonResponse(response_data)


class VinculoDownloadUpdateTemplateView(LoginRequiredMixin, View):
    """Download do modelo XLSX para atualização de vínculos."""

    def get(self, request):
        try:
            from datetime import datetime as _dt
            wb = VinculoUpdateService.generate_template_update_xlsx()
            output = BytesIO()
            wb.save(output)
            output.seek(0)
            response = HttpResponse(
                output.getvalue(),
                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            )
            response['Content-Disposition'] = (
                f'attachment; filename="modelo_atualizacao_vinculos_{_dt.now().strftime("%d_%m_%Y")}.xlsx"'
            )
            return response
        except Exception as e:
            messages.error(request, f'Erro ao gerar modelo: {e}')
            return redirect('funcionario-list')


class FuncionarioDetailView(LoginRequiredMixin, EmpresaScopeMixin, DetailView):
    model = Funcionario
    template_name = 'funcionarios/funcionario_detail.html'
    context_object_name = 'funcionario'

    def get_queryset(self):
        # Evita filtro vazio do EmpresaScopeMixin em modelos sem campo empresa
        qs = Funcionario.objects.all()
        allowed = get_allowed_empresa_ids(self.request.user)
        if allowed is None:
            return qs
        if not allowed:
            return qs.none()
        return qs.filter(vinculos__empresa_id__in=allowed).distinct()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['historico_vinculos'] = self.object.historico_vinculos()
        return context


class FuncionarioVinculoCreateView(LoginRequiredMixin, EmpresaScopeMixin, CreateView):
    """Cria um novo vínculo (cadeira) para um funcionário existente."""

    model = FuncionarioVinculo
    form_class = FuncionarioVinculoForm
    template_name = 'funcionarios/funcionario_vinculo_form.html'

    def dispatch(self, request, *args, **kwargs):
        self.funcionario = Funcionario.objects.get(pk=kwargs['pk'])

        # Garantir que o usuário tem acesso ao funcionário pelo escopo de empresas permitidas.
        allowed = get_allowed_empresa_ids(request.user)
        if allowed is not None and not (request.user.is_staff or request.user.is_superuser):
            if not self.funcionario.vinculos.filter(empresa_id__in=allowed).exists():
                return HttpResponseForbidden('Você não tem permissão para criar vínculo para este funcionário.')

        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['funcionario'] = self.funcionario
        return context

    def form_valid(self, form):
        vinculo = form.save(commit=False)
        vinculo.funcionario = self.funcionario

        if not is_empresa_allowed(self.request.user, vinculo.empresa.codigo):
            return HttpResponseForbidden('Você não tem permissão para criar vínculo nesta empresa.')

        vinculo.save()
        messages.success(
            self.request,
            f'✅ Vínculo criado: {self.funcionario.nome} — {vinculo.empresa.nome} (Matrícula {vinculo.matricula}).'
        )
        return redirect('funcionario-detail', pk=self.funcionario.pk)

    def form_invalid(self, form):
        messages.error(self.request, 'Foram encontradas inconsistencias nas informacoes enviadas. Revise as informacoes.')
        return super().form_invalid(form)

class FuncionarioTransferenciaView(LoginRequiredMixin, EmpresaScopeMixin, View):
    template_name = 'funcionarios/funcionario_transferencia.html'

    def _verificar_permissao(self, request, funcionario):
        # Superuser/staff têm acesso
        if request.user.is_superuser or request.user.is_staff:
            return True
        empresa_origem = funcionario.empresa
        if not empresa_origem:
            return False
        # Precisa estar no escopo (inclui grupo para matriz)
        if not is_empresa_allowed(request.user, empresa_origem.codigo):
            return False
        # Precisa ser admin da empresa origem
        return EmpresaUsuarioRole.objects.filter(
            usuario=request.user,
            empresa=empresa_origem,
            role=EmpresaUsuarioRole.ADMIN
        ).exists()

    def get(self, request, pk):
        funcionario = Funcionario.objects.get(pk=pk)
        if not self._verificar_permissao(request, funcionario):
            return HttpResponseForbidden('Acesso restrito ao administrador da empresa de origem.')
        form = TransferenciaFuncionarioForm(funcionario, user=request.user)
        return render(request, self.template_name, {'form': form, 'funcionario': funcionario})

    def post(self, request, pk):
        funcionario = Funcionario.objects.get(pk=pk)
        if not self._verificar_permissao(request, funcionario):
            return HttpResponseForbidden('Acesso restrito ao administrador da empresa de origem.')
        form = TransferenciaFuncionarioForm(funcionario, request.POST, user=request.user)
        if form.is_valid():
            empresa_origem = funcionario.empresa
            empresa_destino = form.cleaned_data['empresa_destino']
            data_transferencia = form.cleaned_data['data_transferencia']
            cargo = form.cleaned_data.get('cargo')
            salario = form.cleaned_data.get('salario')
            observacoes = form.cleaned_data.get('observacoes')
            # Encerrar vínculo atual
            vinculo_atual = funcionario.vinculo_atual()
            if vinculo_atual:
                vinculo_atual.data_demissao = data_transferencia
                vinculo_atual.motivo_saida = 'transferencia'
                vinculo_atual.save()
            # Criar novo vínculo
            FuncionarioVinculo.objects.create(
                funcionario=funcionario,
                empresa=empresa_destino,
                data_admissao=data_transferencia,
                data_transferencia=data_transferencia,
                cargo=cargo,
                salario=salario,
                observacoes=observacoes
            )
            # Registrar auditoria
            TransferenciaFuncionario.objects.create(
                funcionario=funcionario,
                empresa_origem=empresa_origem,
                empresa_destino=empresa_destino,
                data_transferencia=data_transferencia,
                usuario_responsavel=request.user,
                observacoes=observacoes
            )
            messages.success(request, f'Transferência realizada com sucesso!')
            return redirect('funcionario-detail', pk=funcionario.pk)
        messages.error(request, 'Foram encontradas inconsistencias nas informacoes enviadas. Revise as informacoes.')
        return render(request, self.template_name, {'form': form, 'funcionario': funcionario})


def funcionarios_json(request):
    """Endpoint leve para popular dropdowns de funcionário filtrados por empresa."""
    if not request.user.is_authenticated:
        return JsonResponse([], safe=False)

    empresa_id = request.GET.get('empresa_id', '').strip()
    if not empresa_id:
        return JsonResponse([], safe=False)

    try:
        empresa_id = int(empresa_id)
    except ValueError:
        return JsonResponse([], safe=False)

    # Garantir que o usuário tem acesso à empresa solicitada
    allowed_ids = get_allowed_empresa_ids(request.user)
    if allowed_ids is not None:
        if not Empresa.objects.filter(id=empresa_id, codigo__in=allowed_ids).exists():
            return JsonResponse([], safe=False)

    data = list(
        Funcionario.objects
        .filter(vinculos__empresa_id=empresa_id)
        .distinct()
        .order_by('nome')
        .values('id', 'nome')
    )
    return JsonResponse(data, safe=False)


def funcionarios_autocomplete(request):
    """Autocomplete de funcionário por texto, com empresa_id opcional.
    Retorna [{id, label}] — label inclui nomes de empresa quando há múltiplos vínculos.
    """
    if not request.user.is_authenticated:
        return JsonResponse([], safe=False)

    q = request.GET.get('q', '').strip()
    empresa_id = request.GET.get('empresa_id', '').strip()
    agrupar_cpf = request.GET.get('agrupar_cpf', '').strip() == '1'

    if len(q) < 2:
        return JsonResponse([], safe=False)

    allowed_ids = get_allowed_empresa_ids(request.user)

    if empresa_id:
        try:
            empresa_id = int(empresa_id)
        except ValueError:
            return JsonResponse([], safe=False)

        if allowed_ids is not None:
            if empresa_id not in allowed_ids:
                return JsonResponse([], safe=False)

        qs = (
            FuncionarioVinculo.objects
            .filter(empresa_id=empresa_id, funcionario__nome__icontains=q)
            .select_related('funcionario')
            .order_by('funcionario__nome')[:30]
        )
        vistos = set()
        data = []
        for v in qs:
            fid = v.funcionario_id
            if fid not in vistos:
                vistos.add(fid)
                data.append({'id': fid, 'label': v.funcionario.nome})
    else:
        from collections import defaultdict
        qs = (
            FuncionarioVinculo.objects
            .filter(funcionario__nome__icontains=q)
            .select_related('funcionario', 'empresa')
            .order_by('funcionario__nome')
        )
        if allowed_ids is not None:
            qs = qs.filter(empresa__codigo__in=allowed_ids)

        if agrupar_cpf:
            # Agrupa por CPF: a mesma pessoa pode ter registros de Funcionario
            # distintos em cada empresa do grupo econômico — aqui ela aparece
            # como uma única opção, cruzando todas as empresas permitidas.
            func_map = defaultdict(lambda: {'nome': '', 'cpf': '', 'funcionario_id': None, 'empresas': []})
            for v in qs[:200]:
                cpf = (v.funcionario.cpf or '').strip()
                chave = ('cpf', cpf) if cpf else ('id', v.funcionario_id)
                func_map[chave]['nome'] = v.funcionario.nome
                func_map[chave]['cpf'] = cpf
                func_map[chave]['funcionario_id'] = v.funcionario_id
                if v.empresa.nome not in func_map[chave]['empresas']:
                    func_map[chave]['empresas'].append(v.empresa.nome)

            data = []
            for chave, info in func_map.items():
                empresas_label = ' / '.join(info['empresas'])
                label = '{} ({})'.format(info['nome'], empresas_label)
                id_val = 'cpf:{}'.format(info['cpf']) if info['cpf'] else info['funcionario_id']
                data.append({'id': id_val, 'label': label})

            data.sort(key=lambda x: x['label'])
            data = data[:30]
        else:
            func_map = defaultdict(lambda: {'nome': '', 'empresas': []})
            for v in qs[:100]:
                func_map[v.funcionario_id]['nome'] = v.funcionario.nome
                if v.empresa.nome not in func_map[v.funcionario_id]['empresas']:
                    func_map[v.funcionario_id]['empresas'].append(v.empresa.nome)

            data = []
            for fid, info in func_map.items():
                empresas_label = ' / '.join(info['empresas'])
                label = '{} ({})'.format(info['nome'], empresas_label)
                data.append({'id': fid, 'label': label})

            data.sort(key=lambda x: x['label'])
            data = data[:30]

    return JsonResponse(data, safe=False)


def vinculos_json(request):
    """Endpoint leve para popular o select de vínculo no form de lançamento."""
    if not request.user.is_authenticated:
        return JsonResponse([], safe=False)

    empresa_id = request.GET.get('empresa_id', '').strip()
    if not empresa_id:
        return JsonResponse([], safe=False)

    try:
        empresa_id = int(empresa_id)
    except ValueError:
        return JsonResponse([], safe=False)

    allowed_ids = get_allowed_empresa_ids(request.user)
    if allowed_ids is not None:
        if empresa_id not in allowed_ids:
            return JsonResponse([], safe=False)

    vinculos = (
        FuncionarioVinculo.objects
        .filter(empresa_id=empresa_id)
        .select_related('funcionario', 'empresa')
        .order_by('funcionario__nome', 'data_admissao')
    )
    data = [{'id': v.pk, 'nome': str(v)} for v in vinculos]
    return JsonResponse(data, safe=False)


from datetime import datetime


def _recalcular_historico_vinculo(vinculo, user, ip=None):
    """
    Recalcula valor_fgts de todos os lançamentos do vínculo usando a alíquota atual.
    Lançamentos sem base_fgts são coletados mas não alterados.
    Retorna dict com contagens e lista de ids sem base.
    Usa bulk_update para não disparar Lancamento.save() e evitar loops.
    """
    aliquota = get_aliquota_fgts(vinculo)
    qs = Lancamento.objects.filter(vinculo=vinculo)

    com_base = list(qs.filter(base_fgts__isnull=False))
    sem_base_ids = list(qs.filter(base_fgts__isnull=True).values_list('id', flat=True))

    for lanc in com_base:
        lanc.valor_fgts = (lanc.base_fgts * aliquota).quantize(Decimal('0.01'))

    if com_base:
        Lancamento.objects.bulk_update(com_base, ['valor_fgts'])

    tipo_nome = vinculo.tipo_vinculo.descricao if vinculo.tipo_vinculo_id else 'CLT (padrão)'
    AuditLog.objects.create(
        user=user,
        action='UPDATE',
        module='lancamentos',
        view_name='VinculoRecalcularView',
        ip_address=ip,
        object_id=vinculo.pk,
        object_repr=f'Vínculo #{vinculo.pk} — {vinculo.funcionario.nome}',
        description=(
            f'Recálculo histórico de FGTS: {len(com_base)} lançamento(s) atualizados '
            f'para {float(aliquota) * 100:.0f}% ({tipo_nome}). '
            f'{len(sem_base_ids)} lançamento(s) ignorados por ausência de base_fgts.'
        ),
        new_values={'aliquota_pct': str(aliquota * 100), 'recalculados': len(com_base), 'sem_base': len(sem_base_ids)},
    )
    return {'recalculados': len(com_base), 'sem_base_ids': sem_base_ids}


class VinculoRecalcularView(LoginRequiredMixin, View):
    """
    GET: Pergunta ao usuário se deseja recalcular o histórico após mudança de tipo_vinculo.
    POST: Executa o recálculo e exibe resultado.
    """
    template_name = 'funcionarios/vinculo_recalcular_confirm.html'

    def _get_vinculo_and_funcionario(self, pk, vid):
        funcionario = Funcionario.objects.get(pk=pk)
        vinculo = FuncionarioVinculo.objects.select_related(
            'tipo_vinculo', 'funcionario', 'empresa'
        ).get(pk=vid, funcionario=funcionario)
        return funcionario, vinculo

    def get(self, request, pk, vid):
        try:
            funcionario, vinculo = self._get_vinculo_and_funcionario(pk, vid)
        except (Funcionario.DoesNotExist, FuncionarioVinculo.DoesNotExist):
            messages.error(request, 'Vínculo não encontrado.')
            return redirect('funcionario-list')

        total_lancamentos = Lancamento.objects.filter(vinculo=vinculo).count()
        sem_base = Lancamento.objects.filter(vinculo=vinculo, base_fgts__isnull=True).count()

        return render(request, self.template_name, {
            'funcionario': funcionario,
            'vinculo': vinculo,
            'total_lancamentos': total_lancamentos,
            'sem_base': sem_base,
        })

    def post(self, request, pk, vid):
        try:
            funcionario, vinculo = self._get_vinculo_and_funcionario(pk, vid)
        except (Funcionario.DoesNotExist, FuncionarioVinculo.DoesNotExist):
            messages.error(request, 'Vínculo não encontrado.')
            return redirect('funcionario-list')

        if 'confirmar' in request.POST:
            ip = request.META.get('HTTP_X_FORWARDED_FOR', request.META.get('REMOTE_ADDR', ''))
            resultado = _recalcular_historico_vinculo(
                vinculo, request.user, ip=(ip.split(',')[0].strip() if ip else None)
            )
            messages.success(
                request,
                f'✅ {resultado["recalculados"]} lançamento(s) recalculados. '
                + (f'⚠️ {len(resultado["sem_base_ids"])} lançamento(s) sem base FGTS foram ignorados.' if resultado["sem_base_ids"] else '')
            )
        else:
            messages.info(request, 'Recálculo cancelado. Os lançamentos existentes não foram alterados.')

        return redirect('funcionario-detail', pk=funcionario.pk)
