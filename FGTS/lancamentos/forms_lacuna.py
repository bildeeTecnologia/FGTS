from django import forms

from lancamentos.models_lacuna import LacunaJustificativa


class JustificativaLacunaForm(forms.ModelForm):
    class Meta:
        model = LacunaJustificativa
        fields = ['motivo', 'observacao']
        widgets = {
            # form="justificarForm" associa estes campos ao <form> da tela de detalhe do
            # vínculo, mesmo estando fora dele (ver auditoria_vinculo_detail.html).
            'motivo': forms.Select(attrs={'class': 'form-select', 'autocomplete': 'off', 'form': 'justificarForm'}),
            'observacao': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Detalhe o motivo (obrigatório para "Outro")',
                'form': 'justificarForm',
            }),
        }
        labels = {
            'motivo': 'Motivo da lacuna',
            'observacao': 'Observação',
        }

    def clean(self):
        cleaned_data = super().clean()
        motivo = cleaned_data.get('motivo')
        observacao = (cleaned_data.get('observacao') or '').strip()
        if motivo == 'outro' and not observacao:
            self.add_error('observacao', 'Informe uma observação ao selecionar o motivo "Outro".')
        return cleaned_data
