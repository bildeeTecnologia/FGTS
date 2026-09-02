from django import forms

class CoefJamUploadForm(forms.Form):
    arquivo = forms.FileField(label="Arquivo COEFJAM.TXT")
