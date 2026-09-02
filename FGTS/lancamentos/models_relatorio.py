from django.db import models
from django.conf import settings
from empresas.models import Empresa


class RelatorioTask(models.Model):
    STATUS_CHOICES = [
        ('pending',    'Aguardando'),
        ('processing', 'Processando'),
        ('done',       'Concluído'),
        ('error',      'Erro'),
    ]

    usuario           = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='relatorio_tasks')
    empresa           = models.ForeignKey(Empresa, on_delete=models.SET_NULL, null=True, blank=True)
    parametros_json   = models.JSONField()
    status            = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    resultado_json    = models.JSONField(null=True, blank=True)
    avisos_json       = models.JSONField(null=True, blank=True)
    mensagem_erro     = models.TextField(blank=True)
    total_lancamentos = models.IntegerField(null=True, blank=True)
    criado_em         = models.DateTimeField(auto_now_add=True)
    atualizado_em     = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-criado_em']
        verbose_name = 'Tarefa de Relatório'
        verbose_name_plural = 'Tarefas de Relatório'

    def __str__(self):
        empresa_nome = self.empresa.nome if self.empresa else '—'
        return f'RelatorioTask #{self.pk} — {empresa_nome} [{self.status}]'
