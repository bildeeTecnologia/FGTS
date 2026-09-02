from django import forms
from .models import Feedback


class FeedbackForm(forms.ModelForm):
    """Formulário para submissão de feedback"""
    
    class Meta:
        model = Feedback
        fields = ['tipo', 'titulo', 'mensagem', 'email_resposta']
        widgets = {
            'tipo': forms.Select(attrs={
                'class': 'form-select',
                'aria-label': 'Tipo de feedback'
            }),
            'titulo': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: Adicionar modo escuro',
                'maxlength': '255'
            }),
            'mensagem': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Descreva seu feedback aqui...',
                'rows': 5
            }),
            'email_resposta': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'seu@email.com (opcional)',
                'type': 'email'
            })
        }
        labels = {
            'tipo': 'Tipo de Feedback',
            'titulo': 'Assunto',
            'mensagem': 'Mensagem',
            'email_resposta': 'Email para Contato (opcional)'
        }
