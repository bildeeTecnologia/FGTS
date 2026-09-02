
from django import forms
from indices.services.indice_service import IndiceFGTSService
from django.utils import timezone

class FGTSCalculadoraForm(forms.Form):

    base_fgts = forms.DecimalField(
        label="Base FGTS",
        decimal_places=2,
        max_digits=12,
        widget=forms.NumberInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': 'Ex: 2500,00'
        })
    )
    competencia = forms.CharField(
        label="Competência",
        max_length=7,
        help_text="MM/AAAA",
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-lg competencia-input',
            'placeholder': 'MM/AAAA',
            'data-auto-format': 'competencia'
        })
    )
    data_pagamento = forms.DateField(
        label="Data de Pagamento",
        widget=forms.DateInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': 'dd/mm/aaaa',
            'type': 'date'
        })
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        hoje = timezone.now().date()
        data_maxima = IndiceFGTSService.obter_ultima_data_base()
        data_min = min(hoje, data_maxima) if data_maxima else hoje
        self.fields['data_pagamento'].widget.attrs['min'] = data_min.strftime('%Y-%m-%d')
        if data_maxima:
            self.fields['data_pagamento'].widget.attrs['max'] = data_maxima.strftime('%Y-%m-%d')

    def clean_competencia(self):
        competencia = self.cleaned_data['competencia']
        from datetime import datetime
        competencia_dt = None
        try:
            competencia_dt = datetime.strptime(competencia, '%m/%Y').date().replace(day=1)
        except Exception:
            raise forms.ValidationError('Competência inválida. Use o formato MM/AAAA.')
        min_competencia = datetime.strptime('01/2000', '%m/%Y').date().replace(day=1)
        if competencia_dt < min_competencia:
            raise forms.ValidationError('Para consultar competências anteriores a 01/2000, contrate o plano pago e tenha acesso a este e muitos outros recursos avançados.')
        return competencia

    def clean_data_pagamento(self):
        data_pagamento = self.cleaned_data['data_pagamento']
        hoje = timezone.now().date()
        if data_pagamento < hoje:
            raise forms.ValidationError('A data de pagamento não pode ser anterior a hoje.')
        data_maxima = IndiceFGTSService.obter_ultima_data_base()
        if data_maxima and data_pagamento > data_maxima:
            raise forms.ValidationError(f'Data máxima disponível: {data_maxima.strftime("%d/%m/%Y")}. Para datas posteriores, atualize os índices ou contrate o plano pago.')
        if data_pagamento.weekday() in (5, 6):
            raise forms.ValidationError('A data de pagamento não pode ser sábado ou domingo.')
        return data_pagamento
