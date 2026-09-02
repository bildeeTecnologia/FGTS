from django.db import models
from django.contrib.auth import get_user_model
from empresas.models import Empresa
from decimal import Decimal

User = get_user_model()


class PerformanceLog(models.Model):
    """Registra performance de operações críticas do sistema"""
    
    OPERACAO_CHOICES = [
        ('relatorio_competencia', 'Relatório por Competência'),
        ('importacao_funcionarios', 'Importação de Funcionários'),
        ('exportacao_csv', 'Exportação CSV'),
        ('exportacao_pdf', 'Exportação PDF'),
        ('calculo_fgts', 'Cálculo FGTS'),
        ('geracao_lancamentos', 'Geração de Lançamentos'),
        ('importacao_lancamentos', 'Importação de Lançamentos'),
        ('outro', 'Outro'),
    ]
    
    STATUS_CHOICES = [
        ('sucesso', 'Sucesso'),
        ('erro', 'Erro'),
        ('timeout', 'Timeout'),
    ]
    
    # Identificação
    operacao = models.CharField(max_length=50, choices=OPERACAO_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='sucesso')
    
    # Usuário e empresa
    usuario = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='performance_logs')
    # Empresa: armazenar o ID como inteiro (evita problemas de FK com PK diferente no model vs DB)
    empresa_id = models.IntegerField(null=True, blank=True, verbose_name='ID da Empresa')
    
    # Timing
    tempo_inicio = models.DateTimeField(auto_now_add=True)
    tempo_final = models.DateTimeField(null=True, blank=True)
    duracao_segundos = models.DecimalField(max_digits=10, decimal_places=3, default=0)
    
    # Detalhes
    entrada_dados = models.JSONField(default=dict, blank=True, help_text="Parâmetros de entrada")
    saida_dados = models.JSONField(default=dict, blank=True, help_text="Dados de saída (resumido)")
    mensagem_erro = models.TextField(blank=True, help_text="Mensagem de erro se houver")
    
    # Contexto
    ip_cliente = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=500, blank=True)
    
    class Meta:
        verbose_name = 'Performance Log'
        verbose_name_plural = 'Performance Logs'
        ordering = ['-tempo_inicio']
        indexes = [
            models.Index(fields=['operacao', '-tempo_inicio']),
            models.Index(fields=['usuario', '-tempo_inicio']),
            models.Index(fields=['empresa_id', '-tempo_inicio']),
            models.Index(fields=['status', '-tempo_inicio']),
        ]
    
    def __str__(self):
        return f"{self.get_operacao_display()} - {self.tempo_inicio.strftime('%d/%m/%Y %H:%M:%S')}"
    
    @property
    def tempo_longo(self):
        """Flag se levou mais de 5 segundos"""
        return self.duracao_segundos > Decimal('5.0')
    
    @property
    def tempo_muito_longo(self):
        """Flag se levou mais de 15 segundos"""
        return self.duracao_segundos > Decimal('15.0')
