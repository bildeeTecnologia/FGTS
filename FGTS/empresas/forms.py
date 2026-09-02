from django import forms
from django.core.exceptions import ValidationError
from django.db.models import Q
from fgtsweb.utils.validators import (
    digits_only,
    fetch_cep_data,
    normalize_upper_ascii,
    validate_cep,
)
from fgtsweb.mixins import get_allowed_empresa_ids
from .models import Empresa
from .models_grupo import GrupoEmpresa

class EmpresaForm(forms.ModelForm):
    class Meta:
        model = Empresa
        fields = ['grupo', 'nome', 'cnpj', 'codigo_folha', 'endereco', 'numero', 'bairro', 'cep', 'cidade', 'uf', 
              'nome_contato', 'fone_contato', 'cnae', 'percentual_rat', 'optante_simples', 
              'fpas', 'outras_entidades', 'email', 'paga_13_aniversario', 'validar_meses_parcela_13']
        widgets = {
            'grupo': forms.Select(attrs={'class': 'form-select'}),
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'cnpj': forms.TextInput(attrs={'class': 'form-control'}),
            'codigo_folha': forms.TextInput(attrs={'class': 'form-control'}),
            'endereco': forms.TextInput(attrs={'class': 'form-control'}),
            'numero': forms.TextInput(attrs={'class': 'form-control'}),
            'bairro': forms.TextInput(attrs={'class': 'form-control'}),
            'cep': forms.TextInput(attrs={'class': 'form-control'}),
            'cidade': forms.TextInput(attrs={'class': 'form-control'}),
            'uf': forms.TextInput(attrs={'class': 'form-control'}),
            'nome_contato': forms.TextInput(attrs={'class': 'form-control'}),
            'fone_contato': forms.TextInput(attrs={'class': 'form-control'}),
            'cnae': forms.TextInput(attrs={'class': 'form-control'}),
            'percentual_rat': forms.NumberInput(attrs={'class': 'form-control'}),
            'optante_simples': forms.Select(attrs={'class': 'form-select'}),
            'fpas': forms.TextInput(attrs={'class': 'form-control'}),
            'outras_entidades': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'paga_13_aniversario': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'validar_meses_parcela_13': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if 'codigo_folha' in self.fields:
            self.fields['codigo_folha'].required = False
        if 'grupo' in self.fields:
            allowed = get_allowed_empresa_ids(user)
            qs = GrupoEmpresa.objects.all()
            if allowed is None:
                pass
            elif not allowed:
                qs = GrupoEmpresa.objects.none()
            else:
                qs = qs.filter(
                    Q(empresa_principal__codigo__in=allowed) |
                    Q(empresas__codigo__in=allowed)
                ).distinct()
            self.fields['grupo'].queryset = qs

        # Se o usuário é matriz de algum grupo, pré-selecionar o grupo dele
        if user and getattr(user, 'empresa', None):
            try:
                grupo_user = getattr(user.empresa, 'grupo', None)
                if grupo_user:
                    self.fields['grupo'].initial = grupo_user
            except Exception:
                pass

    def clean(self):
        cleaned_data = super().clean()

        if 'grupo' not in self.data and getattr(self.instance, 'pk', None):
            cleaned_data['grupo'] = self.instance.grupo

        if not cleaned_data.get('codigo_folha'):
            cleaned_data['codigo_folha'] = Empresa._generate_codigo_folha()

        # Normalizar campos textuais para maiúsculas ASCII
        cleaned_data['nome'] = normalize_upper_ascii(cleaned_data.get('nome'), allow_digits=True)
        cleaned_data['endereco'] = normalize_upper_ascii(cleaned_data.get('endereco'), allow_digits=True)
        cleaned_data['bairro'] = normalize_upper_ascii(cleaned_data.get('bairro'), allow_digits=True)
        cleaned_data['cidade'] = normalize_upper_ascii(cleaned_data.get('cidade'), allow_digits=False)
        cleaned_data['uf'] = normalize_upper_ascii(cleaned_data.get('uf'), allow_digits=False)[:2]
        cleaned_data['nome_contato'] = normalize_upper_ascii(cleaned_data.get('nome_contato'), allow_digits=True)

        # Remover caracteres especiais de campos numéricos/documentos
        cleaned_data['cnpj'] = digits_only(cleaned_data.get('cnpj'))
        cleaned_data['numero'] = digits_only(cleaned_data.get('numero'))
        cleaned_data['fone_contato'] = digits_only(cleaned_data.get('fone_contato'))
        cleaned_data['cnae'] = digits_only(cleaned_data.get('cnae'))
        cleaned_data['fpas'] = digits_only(cleaned_data.get('fpas'))
        cleaned_data['outras_entidades'] = digits_only(cleaned_data.get('outras_entidades'))

        cep_raw = cleaned_data.get('cep')
        if cep_raw:
            try:
                cep = validate_cep(cep_raw)
                cleaned_data['cep'] = cep
                cep_data = fetch_cep_data(cep)
                cleaned_data['endereco'] = cleaned_data.get('endereco') or cep_data['endereco']
                cleaned_data['bairro'] = cleaned_data.get('bairro') or cep_data['bairro']
                cleaned_data['cidade'] = cleaned_data.get('cidade') or cep_data['cidade']
                cleaned_data['uf'] = cleaned_data.get('uf') or cep_data['uf']
            except ValidationError as exc:
                self.add_error('cep', exc)

        return cleaned_data
