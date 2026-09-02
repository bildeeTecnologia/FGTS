from django import forms
from empresas.models_grupo import FuncionarioVinculo
from empresas.models import Empresa
from fgtsweb.mixins import get_allowed_empresa_ids

class TransferenciaFuncionarioForm(forms.Form):
    empresa_destino = forms.ModelChoiceField(queryset=Empresa.objects.none(), label="Empresa de Destino", widget=forms.Select(attrs={'class': 'form-select'}))
    data_transferencia = forms.DateField(label="Data da Transferência", widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}))
    cargo = forms.CharField(label="Cargo na nova empresa", required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    salario = forms.DecimalField(label="Salário na nova empresa", required=False, max_digits=12, decimal_places=2, widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}))
    observacoes = forms.CharField(label="Observações", required=False, widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2}))

    def __init__(self, funcionario, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        empresa_origem = funcionario.empresa or (funcionario.vinculo_atual().empresa if funcionario.vinculo_atual() else None)
        grupo = None
        if empresa_origem:
            grupo = empresa_origem.grupo or getattr(empresa_origem, 'grupo_principal', None)

        if grupo and empresa_origem:
            qs = grupo.empresas.exclude(pk=empresa_origem.pk)
            allowed_ids = get_allowed_empresa_ids(user) if user else None
            if allowed_ids is not None:
                qs = qs.filter(codigo__in=allowed_ids)
            self.fields['empresa_destino'].queryset = qs
        else:
            self.fields['empresa_destino'].queryset = Empresa.objects.none()
