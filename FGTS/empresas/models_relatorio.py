from django.db import models

class RelatorioPremium(models.Model):
    email = models.EmailField()
    data_geracao = models.DateTimeField(auto_now_add=True)
    memoria = models.JSONField(null=True, blank=True)  # Armazena o relatório gerado
    # Pode adicionar campos extras se necessário

    class Meta:
        verbose_name = 'Relatório Premium FGTS'
        verbose_name_plural = 'Relatórios Premium FGTS'

    def __str__(self):
        return f"{self.email} - {self.data_geracao:%d/%m/%Y %H:%M}"
