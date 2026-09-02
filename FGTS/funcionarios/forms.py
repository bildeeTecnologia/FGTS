from django import forms
from decimal import Decimal

from fgtsweb.utils.validators import digits_only, normalize_upper_ascii, validate_cpf
from .models import Funcionario
from empresas.models import Empresa
from empresas.models_grupo import FuncionarioVinculo, TipoVinculo
from .forms_transferencia import TransferenciaFuncionarioForm

class FuncionarioForm(forms.ModelForm):
    salario_inicial = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        label='Salário Inicial (Base FGTS)',
        help_text='Se informado, será criado automaticamente o primeiro lançamento de FGTS na competência de admissão',
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ex: 3500.00',
            'step': '0.01'
        })
    )
    
    class Meta:
        model = Funcionario
        fields = ['nome', 'pis', 'cpf', 'cbo', 'carteira_profissional', 
                  'serie_carteira', 'data_nascimento', 'observacao']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'pis': forms.TextInput(attrs={'class': 'form-control'}),
            'cpf': forms.TextInput(attrs={'class': 'form-control'}),
            'cbo': forms.TextInput(attrs={'class': 'form-control'}),
            'carteira_profissional': forms.TextInput(attrs={'class': 'form-control'}),
            'serie_carteira': forms.TextInput(attrs={'class': 'form-control'}),
            # Inputs HTML5 type="date" exigem valor no formato ISO (YYYY-MM-DD)
            'data_nascimento': forms.DateInput(format='%Y-%m-%d', attrs={'class': 'form-control', 'type': 'date'}),
            'observacao': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Campos extras para vínculo
        self.fields['matricula'] = forms.CharField(
            required=False,
            label='Matrícula (do vínculo)',
            help_text='Recomendado para importações. Se ficar em branco, você pode usar o ID do vínculo como fallback.',
            widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: 1001'})
        )
        self.fields['empresa'] = forms.ModelChoiceField(
            queryset=Empresa.objects.all(),
            required=True,
            label='Empresa',
            widget=forms.Select(attrs={'class': 'form-select'})
        )
        self.fields['data_admissao'] = forms.DateField(
            required=True,
            label='Data de Admissão',
            widget=forms.DateInput(format='%Y-%m-%d', attrs={'class': 'form-control', 'type': 'date'})
        )
        self.fields['data_demissao'] = forms.DateField(
            required=False,
            label='Data de Demissão',
            widget=forms.DateInput(format='%Y-%m-%d', attrs={'class': 'form-control', 'type': 'date'})
        )
        self.fields['cargo'] = forms.CharField(
            required=False,
            label='Cargo',
            widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Analista, Gerente...'})
        )
        self.fields['motivo_saida'] = forms.ChoiceField(
            required=False,
            label='Motivo do Desligamento',
            choices=[('', '---------')] + list(FuncionarioVinculo.MOTIVO_SAIDA_CHOICES),
            widget=forms.Select(attrs={'class': 'form-select'})
        )
        self.fields['tipo_vinculo'] = forms.ModelChoiceField(
            queryset=TipoVinculo.objects.filter(ativo=True),
            required=False,
            label='Tipo de Vínculo',
            empty_label='CLT (padrão)',
            widget=forms.Select(attrs={'class': 'form-select'}),
        )
        # Pré-popula dados do vínculo atual ao editar
        instance = getattr(self, 'instance', None)
        if instance and getattr(instance, 'pk', None):
            vinculo = instance.vinculo_atual()
            if vinculo:
                self.fields['matricula'].initial = vinculo.matricula
                self.fields['empresa'].initial = vinculo.empresa
                self.fields['data_admissao'].initial = vinculo.data_admissao
                self.fields['data_demissao'].initial = vinculo.data_demissao
                self.fields['cargo'].initial = vinculo.cargo
                self.fields['motivo_saida'].initial = vinculo.motivo_saida or ''
                self.fields['tipo_vinculo'].initial = vinculo.tipo_vinculo
                if vinculo.salario:
                    self.fields['salario_inicial'].initial = vinculo.salario
        # Django 5+ usa dict normal, não OrderedDict; não há garantia de ordem, mas não quebra o form
        # Se quiser garantir ordem, reordene manualmente ou ajuste o template

    def clean_nome(self):
        nome = self.cleaned_data.get('nome')
        return normalize_upper_ascii(nome, allow_digits=False)

    def clean_cpf(self):
        cpf = self.cleaned_data.get('cpf')
        return validate_cpf(cpf) if cpf else ''

    def clean_pis(self):
        # Regra atual permite CPF no lugar do PIS; portanto não validamos DV.
        # Normalizamos para somente dígitos para manter consistência de armazenamento.
        pis = digits_only(self.cleaned_data.get('pis'))
        if not pis:
            return ''
        if len(pis) > 15:
            raise forms.ValidationError('PIS muito longo. Informe no máximo 15 dígitos.')
        return pis

    def clean_matricula(self):
        matricula = self.cleaned_data.get('matricula')
        if not matricula:
            return ''
        matricula = digits_only(matricula)
        if not matricula:
            raise forms.ValidationError('Matrícula inválida. Informe apenas números.')
        if len(matricula) > 30:
            raise forms.ValidationError('Matrícula muito longa. Informe no máximo 30 dígitos.')
        return matricula

    def clean(self):
        cleaned_data = super().clean()
        # Normalização dos demais campos textuais
        cleaned_data['cbo'] = normalize_upper_ascii(cleaned_data.get('cbo'), allow_digits=True)
        cleaned_data['carteira_profissional'] = normalize_upper_ascii(cleaned_data.get('carteira_profissional'), allow_digits=True)
        cleaned_data['serie_carteira'] = normalize_upper_ascii(cleaned_data.get('serie_carteira'), allow_digits=True)
        if cleaned_data.get('observacao'):
            cleaned_data['observacao'] = normalize_upper_ascii(cleaned_data.get('observacao'), allow_digits=True)
        # Deixa o model.clean enxergar a empresa/datas antes de salvar
        self.instance._empresa_override = cleaned_data.get('empresa')
        self.instance._data_admissao_override = cleaned_data.get('data_admissao')
        self.instance._data_demissao_override = cleaned_data.get('data_demissao')
        return cleaned_data

    def save(self, commit=True):
        funcionario = super().save(commit=commit)
        empresa = self.cleaned_data['empresa']
        matricula = (self.cleaned_data.get('matricula') or '').strip()
        data_admissao = self.cleaned_data['data_admissao']
        data_demissao = self.cleaned_data.get('data_demissao')
        salario = self.cleaned_data.get('salario_inicial')
        cargo = (self.cleaned_data.get('cargo') or '').strip() or None
        motivo_saida = self.cleaned_data.get('motivo_saida') or None
        tipo_vinculo = self.cleaned_data.get('tipo_vinculo')
        # Atualiza vínculo atual (mesma empresa) ou cria novo se necessário
        vinculo = funcionario.vinculo_atual()
        if vinculo and vinculo.empresa == empresa:
            vinculo.matricula = matricula or None
            vinculo.data_admissao = data_admissao
            vinculo.data_demissao = data_demissao
            vinculo.salario = salario or None
            vinculo.cargo = cargo
            vinculo.motivo_saida = motivo_saida
            vinculo.tipo_vinculo = tipo_vinculo
            vinculo.save()
        elif not funcionario.vinculos.filter(empresa=empresa, data_admissao=data_admissao).exists():
            FuncionarioVinculo.objects.create(
                funcionario=funcionario,
                empresa=empresa,
                matricula=matricula or None,
                data_admissao=data_admissao,
                data_demissao=data_demissao,
                salario=salario or None,
                cargo=cargo,
                motivo_saida=motivo_saida,
                tipo_vinculo=tipo_vinculo,
            )
        return funcionario


class FuncionarioVinculoForm(forms.ModelForm):
    """Criação manual de um novo vínculo (cadeira) para um funcionário existente."""

    class Meta:
        model = FuncionarioVinculo
        fields = ['empresa', 'matricula', 'tipo_vinculo', 'data_admissao', 'data_demissao', 'cargo', 'salario', 'observacoes']
        widgets = {
            'empresa': forms.Select(attrs={'class': 'form-select'}),
            'matricula': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: 1001'}),
            'tipo_vinculo': forms.Select(attrs={'class': 'form-select'}),
            'data_admissao': forms.DateInput(format='%Y-%m-%d', attrs={'class': 'form-control', 'type': 'date'}),
            'data_demissao': forms.DateInput(format='%Y-%m-%d', attrs={'class': 'form-control', 'type': 'date'}),
            'cargo': forms.TextInput(attrs={'class': 'form-control'}),
            'salario': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'observacoes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        # Matrícula é altamente recomendada quando há múltiplos vínculos.
        self.fields['matricula'].required = True
        self.fields['matricula'].help_text = 'Obrigatório. Usado para importar lançamentos sem ambiguidade.'
        self.fields['tipo_vinculo'].required = False
        self.fields['tipo_vinculo'].empty_label = 'CLT (padrão)'
        self.fields['tipo_vinculo'].queryset = TipoVinculo.objects.filter(ativo=True)

        from fgtsweb.mixins import get_allowed_empresa_ids
        allowed_ids = get_allowed_empresa_ids(user) if user else None
        if allowed_ids is not None:
            self.fields['empresa'].queryset = Empresa.objects.filter(codigo__in=allowed_ids)

    def clean_matricula(self):
        matricula = self.cleaned_data.get('matricula')
        matricula = digits_only(matricula)
        if not matricula:
            raise forms.ValidationError('Matrícula inválida. Informe apenas números.')
        if len(matricula) > 30:
            raise forms.ValidationError('Matrícula muito longa. Informe no máximo 30 dígitos.')
        return matricula
