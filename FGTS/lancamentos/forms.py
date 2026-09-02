import datetime
from decimal import Decimal
from dateutil.relativedelta import relativedelta

from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from empresas.models import Empresa
from empresas.models_grupo import FuncionarioVinculo
from funcionarios.models import Funcionario
from fgtsweb.mixins import get_allowed_empresa_ids
from indices.services.indice_service import IndiceFGTSService
from .models import Lancamento


class LancamentoForm(forms.ModelForm):
    """Formulário para cadastro/edição de lançamentos mensais (base FGTS)"""

    extrato_analitico = forms.BooleanField(
        required=False,
        label="Confirmado pelo Extrato Analítico CEF",
        help_text="Marque se este pagamento foi confirmado via Extrato Analítico da CEF (fonte da verdade).",
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input', 'id': 'id_extrato_analitico'}),
    )

    class Meta:
        model = Lancamento
        fields = ['empresa', 'vinculo', 'competencia', 'parcela_13', 'base_fgts', 'pago', 'data_pagto', 'valor_pago']
        widgets = {
            'empresa': forms.Select(attrs={'autocomplete': 'off', 'class': 'form-select'}),
            'vinculo': forms.Select(attrs={'autocomplete': 'off', 'class': 'form-select'}),
            'competencia': forms.TextInput(attrs={
                'placeholder': 'MM/YYYY (ex: 01/2025)',
                'autocomplete': 'off',
                'class': 'form-control competencia-input',
                'data-auto-format': 'competencia'
            }),
            'parcela_13': forms.Select(attrs={'autocomplete': 'off', 'class': 'form-select'}),
            'base_fgts': forms.NumberInput(attrs={
                'placeholder': 'Valor base para cálculo do FGTS',
                'step': '0.01',
                'class': 'form-control'
            }),
            'pago': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'data_pagto': forms.DateInput(attrs={
                'type': 'text',
                'class': 'form-control',
                'autocomplete': 'off',
            }, format='%Y-%m-%d'),
            'valor_pago': forms.NumberInput(attrs={
                'placeholder': 'Valor efetivamente pago',
                'step': '0.01',
                'class': 'form-control'
            }),
        }
        labels = {
            'empresa': 'Empresa *',
            'vinculo': 'Vínculo / Matrícula *',
            'competencia': 'Competência (MM/YYYY) *',
            'parcela_13': 'Parcela do 13º Salário',
            'base_fgts': 'Base FGTS (Salário)',
            'pago': 'FGTS Pago?',
            'data_pagto': 'Data do Pagamento',
            'valor_pago': 'Valor Pago',
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)

        # Pre-populate extrato_analitico from existing instance
        if self.instance and self.instance.pk:
            self.fields['extrato_analitico'].initial = (
                self.instance.fonte_confirmacao_pagamento == 'extrato_analitico'
            )

        allowed_ids = None

        # Filtrar empresas permitidas
        if user is not None:
            allowed_ids = get_allowed_empresa_ids(user)
            if allowed_ids is not None:
                self.fields['empresa'].queryset = Empresa.objects.filter(codigo__in=allowed_ids)

        # Determinar empresa pré-selecionada (POST, initial ou instance)
        empresa_id = None
        data_dict = kwargs.get('data') or {}
        initial_dict = kwargs.get('initial') or {}

        if data_dict.get('empresa'):
            try:
                empresa_id = int(data_dict.get('empresa'))
            except (ValueError, TypeError):
                empresa_id = None
        elif initial_dict.get('empresa'):
            try:
                empresa_id = int(initial_dict.get('empresa'))
            except (ValueError, TypeError):
                empresa_id = None
        elif self.instance and getattr(self.instance, 'empresa_id', None):
            empresa_id = self.instance.empresa_id

        # Filtrar funcionários conforme empresa selecionada ou escopo permitido
        if empresa_id:
            self.fields['vinculo'].queryset = FuncionarioVinculo.objects.filter(empresa_id=empresa_id).select_related('funcionario', 'empresa').order_by('funcionario__nome', 'data_admissao')
        elif allowed_ids is not None:
            self.fields['vinculo'].queryset = FuncionarioVinculo.objects.filter(empresa__codigo__in=allowed_ids).select_related('funcionario', 'empresa').order_by('empresa__nome', 'funcionario__nome', 'data_admissao')
        else:
            self.fields['vinculo'].queryset = FuncionarioVinculo.objects.select_related('funcionario', 'empresa').all().order_by('empresa__nome', 'funcionario__nome', 'data_admissao')


    def clean(self):
        cleaned_data = super().clean()

        vinculo = cleaned_data.get('vinculo')
        empresa = cleaned_data.get('empresa')
        competencia = (cleaned_data.get('competencia') or '').strip()

        if vinculo is None:
            raise ValidationError('Vínculo é obrigatório. Use a Matrícula/ID do vínculo para evitar ambiguidade.')

        if empresa and vinculo.empresa_id != empresa.id:
            self.add_error('vinculo', 'Este vínculo não pertence à empresa selecionada.')

        if vinculo and competencia:
            try:
                if '/' in competencia:
                    mes_str, ano_str = competencia.split('/')
                    comp_date = datetime.date(int(ano_str), int(mes_str), 1)
                    adm = vinculo.data_admissao
                    dem = vinculo.data_demissao
                    adm_month = datetime.date(adm.year, adm.month, 1)
                    dem_month = datetime.date(dem.year, dem.month, 1) if dem else None
                    if comp_date < adm_month or (dem_month and comp_date > dem_month):
                        self.add_error('competencia', 'Competência fora do período do vínculo.')
            except Exception:
                pass

        if vinculo and competencia:
            try:
                empresa_ctx = vinculo.empresa
                billing_customer = empresa_ctx.billing_customer
                max_history_months = billing_customer.get_effective_max_history_months()
                if max_history_months is not None and max_history_months > 0:
                    mes_str, ano_str = competencia.split('/')
                    comp_date = datetime.date(int(ano_str), int(mes_str), 1)
                    today = datetime.date.today()
                    current_month = datetime.date(today.year, today.month, 1)
                    min_date = current_month - relativedelta(months=max_history_months - 1)
                    if comp_date < min_date:
                        self.add_error(
                            'competencia',
                            f"Competência fora do limite do seu plano: máximo de {max_history_months} meses de histórico."
                        )
            except Exception:
                pass

        # Garantir que o model instance tenha empresa/funcionário antes do full_clean do ModelForm
        self.instance.vinculo = vinculo
        self.instance.empresa = vinculo.empresa
        self.instance.funcionario = vinculo.funcionario
        return cleaned_data

    def clean_data_pagto(self):
        return self.cleaned_data.get('data_pagto')

    def save(self, commit=True):
        """Sobrescrever save para calcular valor_fgts automaticamente"""
        from empresas.models_grupo import get_aliquota_fgts
        lancamento = super().save(commit=False)
        base_fgts = lancamento.base_fgts
        if base_fgts and (lancamento.valor_fgts is None or lancamento.valor_fgts == 0):
            aliquota = get_aliquota_fgts(lancamento.vinculo)
            lancamento.valor_fgts = (base_fgts * aliquota).quantize(Decimal('0.01'))
        if lancamento.pago:
            lancamento.fonte_confirmacao_pagamento = (
                'extrato_analitico' if self.cleaned_data.get('extrato_analitico') else 'manual'
            )
        else:
            lancamento.fonte_confirmacao_pagamento = None
        if commit:
            lancamento.save()
        return lancamento


class RelatorioCompetenciaForm(forms.Form):
    empresa = forms.ModelChoiceField(
        queryset=Empresa.objects.all(), 
        label='Empresa',
        widget=forms.Select(attrs={'class': 'form-select', 'autocomplete': 'off'})
    )
    funcionario = forms.ModelChoiceField(
        queryset=Funcionario.objects.none(), 
        label='Funcionário (opcional)', 
        required=False,
        widget=forms.Select(attrs={'class': 'form-select', 'autocomplete': 'off'})
    )
    matricula = forms.CharField(
        label='Matrícula (opcional)',
        required=False,
        help_text='Filtra pelo vínculo (cadeira). Recomendado quando há mais de um vínculo ativo na mesma competência.',
        widget=forms.TextInput(attrs={'class': 'form-control', 'autocomplete': 'off', 'placeholder': 'Ex: 10293'})
    )
    competencia = forms.CharField(
        label='Competência Única',
        required=False,
        help_text='MM/YYYY - Deixe vazio para calcular TODAS as competências em aberto',
        widget=forms.TextInput(attrs={'class': 'form-control competencia-input', 'autocomplete': 'off', 'placeholder': 'Vazio = todas em aberto', 'data-auto-format': 'competencia'})
    )
    competencias = forms.CharField(
        label='Múltiplas competências (uma por linha)',
        required=False,
        help_text='Uma por linha no formato MM/YYYY. Ignora se competência única estiver preenchida',
        widget=forms.Textarea(attrs={'class': 'form-control font-monospace competencias-input', 'rows': 3, 'autocomplete': 'off', 'placeholder': '01/2024\n02/2024\n03/2024', 'data-auto-format': 'competencias'})
    )
    agrupamento = forms.ChoiceField(
        label='Agrupar por',
        choices=[
            ('competencia', 'Competência'),
            ('ano', 'Ano'),
            ('funcionario', 'Funcionário'),
            ('vinculo', 'Vínculo / Matrícula'),
        ],
        initial='competencia',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    data_pagamento = forms.DateField(
        label='Data de Pagamento', 
        required=False, 
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date', 'autocomplete': 'off'})
    )

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user is not None:
            allowed_ids = get_allowed_empresa_ids(user)
            if allowed_ids is not None:
                self.fields['empresa'].queryset = Empresa.objects.filter(codigo__in=allowed_ids)

        # Se o formulário tem dados (POST), filtra funcionários pela empresa selecionada
        if 'data' in kwargs and kwargs['data'].get('empresa'):
            try:
                empresa_id = int(kwargs['data'].get('empresa'))
                self.fields['funcionario'].queryset = Funcionario.objects.filter(vinculos__empresa_id=empresa_id).distinct()
            except (ValueError, TypeError):
                self.fields['funcionario'].queryset = Funcionario.objects.none()
        elif user is not None and allowed_ids is not None:
            # Se não tem empresa selecionada, mostra todos das empresas permitidas
            self.fields['funcionario'].queryset = Funcionario.objects.filter(vinculos__empresa__codigo__in=allowed_ids).distinct()

        # Aplicar restrições de data de pagamento (min = hoje, max = última data disponível)
        hoje = timezone.now().date()
        data_maxima = IndiceFGTSService.obter_ultima_data_base()
        self.fields['data_pagamento'].widget.attrs['min'] = hoje.strftime('%Y-%m-%d')
        if data_maxima:
            self.fields['data_pagamento'].widget.attrs['max'] = data_maxima.strftime('%Y-%m-%d')

    def clean_data_pagamento(self):
        data_pagamento = self.cleaned_data.get('data_pagamento')
        if data_pagamento:
            hoje = timezone.now().date()
            if data_pagamento < hoje:
                raise ValidationError('A data de pagamento não pode ser anterior a hoje.')
            data_maxima = IndiceFGTSService.obter_ultima_data_base()
            if data_maxima and data_pagamento > data_maxima:
                raise ValidationError(f'Data máxima disponível: {data_maxima.strftime("%d/%m/%Y")}. Para datas posteriores, atualize os índices ou contrate o plano pago.')
        return data_pagamento


class SefipExportForm(forms.Form):
    empresa = forms.ModelChoiceField(
        queryset=Empresa.objects.all(),
        label='Empresa',
        widget=forms.Select(attrs={'class': 'form-select', 'autocomplete': 'off'})
    )
    competencia = forms.CharField(
        label='Competencia unica',
        help_text='Formato MM/YYYY ou 13/YYYY.',
        widget=forms.TextInput(attrs={'class': 'form-control competencia-input', 'autocomplete': 'off', 'placeholder': 'MM/YYYY', 'data-auto-format': 'competencia'})
    )
    funcionario_de = forms.ModelChoiceField(
        queryset=Funcionario.objects.none(),
        label='Funcionario de',
        widget=forms.Select(attrs={'class': 'form-select', 'autocomplete': 'off'})
    )
    funcionario_ate = forms.ModelChoiceField(
        queryset=Funcionario.objects.none(),
        label='Funcionario ate',
        widget=forms.Select(attrs={'class': 'form-select', 'autocomplete': 'off'})
    )

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)

        allowed_ids = None
        if user is not None:
            allowed_ids = get_allowed_empresa_ids(user)
            if allowed_ids is not None:
                self.fields['empresa'].queryset = Empresa.objects.filter(codigo__in=allowed_ids)

        data_dict = kwargs.get('data') or {}
        empresa_id = data_dict.get('empresa')
        if empresa_id:
            base_qs = Funcionario.objects.filter(vinculos__empresa_id=empresa_id).distinct().order_by('nome')
        elif allowed_ids is not None:
            base_qs = Funcionario.objects.filter(vinculos__empresa__codigo__in=allowed_ids).distinct().order_by('nome')
        else:
            base_qs = Funcionario.objects.all().order_by('nome')

        self.fields['funcionario_de'].queryset = base_qs
        self.fields['funcionario_ate'].queryset = base_qs

    def clean_competencia(self):
        competencia = (self.cleaned_data.get('competencia') or '').strip()
        if not competencia:
            raise ValidationError('Competencia obrigatoria.')
        if '/' not in competencia:
            raise ValidationError('Competencia deve estar no formato MM/YYYY ou 13/YYYY.')
        mes_str, ano_str = competencia.split('/', 1)
        if not mes_str.isdigit() or not ano_str.isdigit():
            raise ValidationError('Competencia deve estar no formato MM/YYYY ou 13/YYYY.')
        mes = int(mes_str)
        if mes not in range(1, 13) and mes != 13:
            raise ValidationError('Mes deve estar entre 01-12 ou 13.')
        if len(ano_str) != 4:
            raise ValidationError('Ano deve ter 4 digitos.')
        return f"{mes:02d}/{int(ano_str):04d}" if mes != 13 else f"13/{int(ano_str):04d}"

    def clean(self):
        cleaned_data = super().clean()

        empresa = cleaned_data.get('empresa')
        func_de = cleaned_data.get('funcionario_de')
        func_ate = cleaned_data.get('funcionario_ate')

        if func_de and func_ate and func_de.id > func_ate.id:
            self.add_error('funcionario_ate', 'Funcionario ate deve ser maior ou igual ao funcionario de.')

        if empresa and (func_de or func_ate):
            for field_name, funcionario in [('funcionario_de', func_de), ('funcionario_ate', func_ate)]:
                if funcionario and not funcionario.vinculos.filter(empresa=empresa).exists():
                    self.add_error(field_name, 'Funcionario nao pertence a empresa selecionada.')

        return cleaned_data


class LegacyImportForm(forms.Form):
    """Formulário para importar dados históricos do sistema legado (VB6)"""
    
    IMPORT_TYPE_CHOICES = [
        ('empresas', 'Importar Empresas'),
        ('funcionarios', 'Importar Funcionários'),
        ('lancamentos', 'Importar Lançamentos (Base FGTS)'),
    ]
    
    csv_file = forms.FileField(
        label='Arquivo CSV',
        help_text='Selecione um arquivo CSV com os dados do sistema legado',
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.csv',
            'required': True
        })
    )
    
    import_type = forms.ChoiceField(
        label='Tipo de Importação',
        choices=IMPORT_TYPE_CHOICES,
        widget=forms.RadioSelect(attrs={
            'class': 'form-check-input'
        }),
        initial='lancamentos'
    )
    
    empresa = forms.ModelChoiceField(
        label='Empresa (obrigatório para funcionários/lançamentos)',
        queryset=Empresa.objects.all(),
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    skip_duplicates = forms.BooleanField(
        label='Pular registros duplicados',
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )
    
    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user is not None:
            allowed_ids = get_allowed_empresa_ids(user)
            if allowed_ids is not None:
                self.fields['empresa'].queryset = Empresa.objects.filter(codigo__in=allowed_ids)
    
    def clean(self):
        """Validação customizada do formulário"""
        cleaned_data = super().clean()
        import_type = cleaned_data.get('import_type')
        csv_file = cleaned_data.get('csv_file')
        empresa = cleaned_data.get('empresa')
        
        # Valida tipo de arquivo
        if csv_file:
            if not csv_file.name.lower().endswith('.csv'):
                raise ValidationError('Arquivo deve ser um CSV válido (.csv)')
            
            # Verifica tamanho máximo (20MB)
            if csv_file.size > 20 * 1024 * 1024:
                raise ValidationError('Arquivo não pode ser maior que 20MB')
        
        # Validações específicas por tipo
        if import_type in ['funcionarios', 'lancamentos'] and not empresa:
            raise ValidationError(f'Empresa é obrigatória para importar {import_type}')
        
        return cleaned_data
    
    def clean_csv_file(self):
        """Valida o arquivo CSV"""
        csv_file = self.cleaned_data.get('csv_file')
        if csv_file:
            try:
                # Tenta ler as primeiras linhas para validar formato
                import codecs
                csv_file.seek(0)
                first_line = csv_file.readline().decode('latin1')
                csv_file.seek(0)
                
                if not first_line.strip():
                    raise ValidationError('Arquivo CSV está vazio')
                
            except UnicodeDecodeError:
                raise ValidationError('Arquivo deve estar em formato Latin1 (ISO-8859-1)')
            except Exception as e:
                raise ValidationError(f'Erro ao validar arquivo: {str(e)}')
        
        return csv_file


class ConferenciaLancamentoForm(forms.Form):
    """Formulário para conferência de lançamento"""
    
    valor_conferido = forms.DecimalField(
        label='Valor Conferido',
        required=False,
        max_digits=15,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01',
            'placeholder': 'Deixe em branco se concordar com o valor calculado'
        }),
        help_text='Informe apenas se o valor estiver diferente do calculado automaticamente'
    )
    
    observacoes = forms.CharField(
        label='Observações',
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'Adicione notas sobre esta conferência (opcional)...'
        }),
        help_text='Registre qualquer observação relevante sobre este lançamento'
    )
    
    def __init__(self, *args, conferencia=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.conferencia = conferencia
        
        if conferencia:
            # Pré-preenche com valores existentes
            if conferencia.valor_conferido:
                self.fields['valor_conferido'].initial = conferencia.valor_conferido
            if conferencia.observacoes:
                self.fields['observacoes'].initial = conferencia.observacoes


class RejeicaoLancamentoForm(forms.Form):
    """Formulário para rejeitar um lançamento"""
    
    MOTIVOS_REJEICAO = [
        ('valor_incorreto', 'Valor incorreto'),
        ('competencia_errada', 'Competência errada'),
        ('funcionario_incorreto', 'Funcionário incorreto'),
        ('duplicado', 'Lançamento duplicado'),
        ('data_invalida', 'Data de pagamento inválida'),
        ('falta_documentacao', 'Falta documentação comprobatória'),
        ('outro', 'Outro motivo'),
    ]
    
    motivo_padrao = forms.ChoiceField(
        label='Motivo da Rejeição',
        choices=MOTIVOS_REJEICAO,
        widget=forms.RadioSelect(attrs={
            'class': 'form-check-input'
        }),
        required=True
    )
    
    motivo_detalhado = forms.CharField(
        label='Detalhes',
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Descreva o motivo da rejeição em detalhes...'
        }),
        required=True,
        help_text='Explique claramente o motivo da rejeição para facilitar a correção'
    )
    
    def clean(self):
        cleaned_data = super().clean()
        motivo_padrao = cleaned_data.get('motivo_padrao')
        motivo_detalhado = cleaned_data.get('motivo_detalhado')
        
        if motivo_detalhado and len(motivo_detalhado.strip()) < 10:
            raise ValidationError('Motivo detalhado deve ter pelo menos 10 caracteres')
        
        return cleaned_data


class FiltroConferenciaForm(forms.Form):
    """Formulário para filtrar conferências"""
    
    STATUS_CHOICES = [
        ('TODOS', 'Todos'),
        ('PENDENTE', 'Pendentes'),
        ('CONFERIDO', 'Conferidos'),
        ('PROBLEMA', 'Com Problemas'),
        ('REJEITADO', 'Rejeitados'),
    ]
    
    competencia = forms.CharField(
        label='Competência',
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control competencia-input',
            'placeholder': 'MM/YYYY (ex: 01/2025)',
            'data-auto-format': 'competencia'
        })
    )
    
    status = forms.ChoiceField(
        label='Status',
        choices=STATUS_CHOICES,
        initial='PENDENTE',
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    funcionario = forms.ModelChoiceField(
        label='Funcionário',
        queryset=Funcionario.objects.none(),
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    def __init__(self, *args, empresa=None, **kwargs):
        super().__init__(*args, **kwargs)
        if empresa:
            self.fields['funcionario'].queryset = Funcionario.objects.filter(empresa=empresa)


class SefipImportForm(forms.Form):
    """Formulário para importar lançamentos a partir de arquivo SEFIP.RE legado."""

    empresa = forms.ModelChoiceField(
        label='Empresa de destino',
        queryset=Empresa.objects.all(),
        required=True,
        widget=forms.Select(attrs={'class': 'form-select'}),
        help_text='Os lançamentos serão criados para esta empresa.',
    )

    arquivo_re = forms.FileField(
        label='Arquivo SEFIP.RE',
        required=True,
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.re,.RE,.txt,.TXT',
        }),
        help_text='Arquivo gerado pelo SEFIP da Caixa Econômica Federal (360 caracteres/linha, ISO-8859-1).',
    )

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user is not None:
            allowed_ids = get_allowed_empresa_ids(user)
            if allowed_ids is not None:
                self.fields['empresa'].queryset = Empresa.objects.filter(codigo__in=allowed_ids)

    def clean_arquivo_re(self):
        arquivo = self.cleaned_data.get('arquivo_re')
        if arquivo:
            nome = arquivo.name.lower()
            if not (nome.endswith('.re') or nome.endswith('.txt')):
                raise ValidationError(
                    'Arquivo deve ter extensão .RE ou .TXT (arquivo gerado pelo SEFIP).'
                )
            if arquivo.size > 50 * 1024 * 1024:
                raise ValidationError('Arquivo não pode ser maior que 50 MB.')
            # Verifica se as primeiras linhas têm comprimento compatível com SEFIP
            try:
                arquivo.seek(0)
                primeira_linha = arquivo.readline()
                arquivo.seek(0)
                linha_str = primeira_linha.decode('latin1').rstrip('\r\n')
                if len(linha_str) < 2 or linha_str[:2] not in ('00', '10', '30'):
                    raise ValidationError(
                        'O arquivo não parece ser um SEFIP.RE válido '
                        '(primeira linha não começa com registro 00, 10 ou 30).'
                    )
            except ValidationError:
                raise
            except Exception:
                pass  # decodagem falha → service reportará
        return arquivo


class RelatorioRecolhimentoFuncionarioForm(forms.Form):
    """Formulário para o relatório de Listagem do Recolhimento por Funcionário"""

    empresa = forms.ModelChoiceField(
        queryset=Empresa.objects.all(),
        label='Empresa',
        required=False,
        empty_label='Todas as empresas',
        widget=forms.Select(attrs={'class': 'form-select', 'autocomplete': 'off'})
    )
    competencia_inicio = forms.CharField(
        label='Competência Inicial',
        max_length=7,
        help_text='MM/YYYY',
        widget=forms.TextInput(attrs={
            'class': 'form-control competencia-input',
            'placeholder': 'MM/YYYY',
            'autocomplete': 'off',
            'data-auto-format': 'competencia'
        })
    )
    competencia_fim = forms.CharField(
        label='Competência Final',
        max_length=7,
        help_text='MM/YYYY',
        widget=forms.TextInput(attrs={
            'class': 'form-control competencia-input',
            'placeholder': 'MM/YYYY',
            'autocomplete': 'off',
            'data-auto-format': 'competencia'
        })
    )
    funcionario = forms.CharField(
        label='Funcionário (opcional)',
        required=False,
        widget=forms.HiddenInput(),
    )

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        allowed_ids = None
        if user is not None:
            allowed_ids = get_allowed_empresa_ids(user)
            if allowed_ids is not None:
                self.fields['empresa'].queryset = Empresa.objects.filter(codigo__in=allowed_ids)
        self._allowed_ids = allowed_ids

    def clean_funcionario(self):
        """
        Aceita dois formatos vindos do autocomplete:
        - 'cpf:<cpf>'  → busca por CPF, cruzando todas as empresas do escopo permitido
                         (mesma pessoa pode ter registros de Funcionario distintos por empresa).
        - '<id>'       → busca por Funcionario.pk exato (fluxo com empresa pré-selecionada).
        Sempre valida se o resultado está dentro do escopo (empresa selecionada ou allowed_ids).
        """
        raw = (self.cleaned_data.get('funcionario') or '').strip()
        if not raw:
            return None

        empresa = self.cleaned_data.get('empresa')
        allowed_ids = getattr(self, '_allowed_ids', None)

        if raw.startswith('cpf:'):
            cpf = raw[4:].strip()
            if not cpf:
                raise ValidationError('Funcionário inválido.')
            qs = Funcionario.objects.filter(cpf=cpf)
            if empresa is not None:
                qs = qs.filter(vinculos__empresa=empresa)
            elif allowed_ids is not None:
                qs = qs.filter(vinculos__empresa__codigo__in=allowed_ids)
            if not qs.exists():
                raise ValidationError('Funcionário não encontrado ou fora do escopo permitido.')
            return {'modo': 'cpf', 'cpf': cpf}

        try:
            pk = int(raw)
        except ValueError:
            raise ValidationError('Funcionário inválido.')

        qs = Funcionario.objects.filter(pk=pk)
        if empresa is not None:
            qs = qs.filter(vinculos__empresa=empresa)
        elif allowed_ids is not None:
            qs = qs.filter(vinculos__empresa__codigo__in=allowed_ids)
        if not qs.exists():
            raise ValidationError('Funcionário não encontrado ou fora do escopo permitido.')
        return {'modo': 'id', 'funcionario_id': pk}

    def _parse_competencia(self, value):
        from datetime import datetime
        value = (value or '').strip()
        try:
            return datetime.strptime(value, '%m/%Y').date().replace(day=1)
        except Exception:
            return None

    def clean_competencia_inicio(self):
        value = self.cleaned_data.get('competencia_inicio', '')
        dt = self._parse_competencia(value)
        if not dt:
            raise ValidationError('Competência inválida. Use o formato MM/YYYY.')
        return value.strip()

    def clean_competencia_fim(self):
        value = self.cleaned_data.get('competencia_fim', '')
        dt = self._parse_competencia(value)
        if not dt:
            raise ValidationError('Competência inválida. Use o formato MM/YYYY.')
        return value.strip()

    def clean(self):
        cleaned = super().clean()
        inicio = cleaned.get('competencia_inicio')
        fim = cleaned.get('competencia_fim')
        if inicio and fim:
            dt_inicio = self._parse_competencia(inicio)
            dt_fim = self._parse_competencia(fim)
            if dt_inicio and dt_fim and dt_inicio > dt_fim:
                raise ValidationError('A competência inicial não pode ser maior que a final.')
        return cleaned


class ImportacaoUploadForm(forms.Form):
    """Formulário de upload com opções de cálculo para o import de lançamentos."""

    FGTS_OPCOES = [
        ('recalcular', 'RECALCULAR — Forçar 8% da base (recomendado)'),
        ('manter',     'MANTER — Usar o valor VALOR_FGTS exatamente como está no arquivo'),
    ]

    empresa = forms.IntegerField(
        required=False,
        widget=forms.HiddenInput(),
    )

    recalcular_fgts = forms.ChoiceField(
        choices=FGTS_OPCOES,
        initial='recalcular',
        label='Valor FGTS',
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
    )

    aplicar_jam = forms.BooleanField(
        required=False,
        label='Aplicar correção JAM/índices acumulados',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text='Aplica os coeficientes JAM sobre o valor FGTS até a data de referência.',
    )

    data_referencia_jam = forms.DateField(
        required=False,
        label='Data de referência (para JAM)',
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control form-control-sm'}),
        help_text='Deixe em branco para usar a data de hoje.',
    )

    extrato_analitico = forms.BooleanField(
        required=False,
        label="Lançamentos pagos confirmados pelo Extrato Analítico CEF",
        help_text="Marque se os pagamentos desta importação foram confirmados via Extrato Analítico da CEF (fonte da verdade).",
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
    )


class ImportacaoConfirmacaoForm(forms.Form):
    """Formulário de aceite de responsabilidade na etapa de confirmação do import."""

    aceite_responsabilidade = forms.BooleanField(
        required=True,
        label=(
            'Declaro que sou responsável pela exatidão dos dados importados, '
            'estou ciente das opções de cálculo selecionadas e aceito as '
            'consequências legais e trabalhistas desta importação.'
        ),
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input', 'id': 'id_aceite_responsabilidade'}),
        error_messages={'required': 'É obrigatório aceitar a responsabilidade antes de confirmar.'},
    )


class RelatorioStatusPosicaoForm(forms.Form):
    """Filtros para o Relatório de Posição em Aberto com Valor Atualizado."""

    empresa = forms.ModelChoiceField(
        queryset=Empresa.objects.none(),
        label='Empresa',
        widget=forms.Select(attrs={'class': 'form-select', 'autocomplete': 'off'})
    )
    competencia_inicio = forms.CharField(
        label='Competência Inicial',
        max_length=7,
        help_text='MM/YYYY',
        widget=forms.TextInput(attrs={
            'class': 'form-control competencia-input',
            'placeholder': 'MM/YYYY',
            'autocomplete': 'off',
            'data-auto-format': 'competencia',
        })
    )
    competencia_fim = forms.CharField(
        label='Competência Final',
        max_length=7,
        help_text='MM/YYYY',
        widget=forms.TextInput(attrs={
            'class': 'form-control competencia-input',
            'placeholder': 'MM/YYYY',
            'autocomplete': 'off',
            'data-auto-format': 'competencia',
        })
    )

    def __init__(self, *args, empresa_ids=None, **kwargs):
        super().__init__(*args, **kwargs)
        if empresa_ids is None:
            # None = irrestrito (superuser/staff) → mostra todas
            self.fields['empresa'].queryset = Empresa.objects.all()
        else:
            self.fields['empresa'].queryset = Empresa.objects.filter(pk__in=empresa_ids)

    def _parse_competencia(self, value, field_name):
        value = value.strip()
        try:
            parts = value.split('/')
            if len(parts) != 2:
                raise ValueError
            mes, ano = int(parts[0]), int(parts[1])
            if not (1 <= mes <= 13) or ano < 1970:
                raise ValueError
            return value
        except (ValueError, IndexError):
            raise forms.ValidationError(f'{field_name} deve estar no formato MM/YYYY.')

    def clean_competencia_inicio(self):
        return self._parse_competencia(self.cleaned_data['competencia_inicio'], 'Competência Inicial')

    def clean_competencia_fim(self):
        return self._parse_competencia(self.cleaned_data['competencia_fim'], 'Competência Final')
