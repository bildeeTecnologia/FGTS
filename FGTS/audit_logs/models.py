from django.db import models
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
import json


class AuditLog(models.Model):
    """
    Modelo para registrar todas as atividades de usuários no sistema.
    Captura: Quem (user), Quando (timestamp), Onde (module), O que (action + description)
    """
    
    ACTION_CHOICES = [
        ('LOGIN', 'Login'),
        ('LOGOUT', 'Logout'),
        ('CREATE', 'Criação'),
        ('UPDATE', 'Atualização'),
        ('DELETE', 'Exclusão'),
        ('VIEW', 'Visualização'),
        ('EXPORT', 'Exportação'),
        ('IMPORT', 'Importação'),
        ('REPORT', 'Relatório'),
        ('PAYMENT', 'Pagamento'),
        ('OTHER', 'Outra'),
    ]
    
    MODULE_CHOICES = [
        ('auth', 'Autenticação'),
        ('empresas', 'Empresas'),
        ('funcionarios', 'Funcionários'),
        ('lancamentos', 'Lançamentos'),
        ('indices', 'Índices'),
        ('coefjam', 'Coef JAM'),
        ('relatorio', 'Relatórios'),
        ('configuracoes', 'Configurações'),
        ('billing', 'Billing'),
        ('outro', 'Outro'),
    ]
    
    # Identificação do usuário
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='audit_logs', verbose_name='Usuário')
    
    # Quando
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name='Data/Hora')
    
    # Onde
    module = models.CharField(max_length=20, choices=MODULE_CHOICES, default='outro', verbose_name='Módulo/App')
    view_name = models.CharField(max_length=255, blank=True, verbose_name='View/Função')
    url_path = models.CharField(max_length=500, blank=True, verbose_name='Caminho da URL')
    
    # O que/Por quê
    action = models.CharField(max_length=20, choices=ACTION_CHOICES, verbose_name='Ação')
    content_type = models.ForeignKey(ContentType, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Tipo de Conteúdo')
    object_id = models.PositiveIntegerField(null=True, blank=True, verbose_name='ID do Objeto')
    object_repr = models.CharField(max_length=500, blank=True, verbose_name='Descrição do Objeto')
    
    # Detalhes da ação
    description = models.TextField(blank=True, verbose_name='Descrição Detalhada')
    old_values = models.JSONField(default=dict, blank=True, verbose_name='Valores Anteriores')
    new_values = models.JSONField(default=dict, blank=True, verbose_name='Novos Valores')
    changes = models.JSONField(default=dict, blank=True, verbose_name='Mudanças')
    
    # Contexto da requisição
    ip_address = models.GenericIPAddressField(null=True, blank=True, verbose_name='Endereço IP')
    user_agent = models.TextField(blank=True, verbose_name='User Agent')
    method = models.CharField(max_length=10, blank=True, verbose_name='Método HTTP')
    status_code = models.IntegerField(null=True, blank=True, verbose_name='Código de Status HTTP')
    error_message = models.TextField(blank=True, verbose_name='Mensagem de Erro')
    
    class Meta:
        verbose_name = 'Log de Auditoria'
        verbose_name_plural = 'Logs de Auditoria'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['-timestamp']),
            models.Index(fields=['user', '-timestamp']),
            models.Index(fields=['action', '-timestamp']),
            models.Index(fields=['module', '-timestamp']),
        ]
    
    def __str__(self):
        user_str = self.user.username if self.user else 'Anônimo'
        return f"{user_str} - {self.get_action_display()} - {self.get_module_display()} - {self.timestamp.strftime('%d/%m/%Y %H:%M:%S')}"
    
    def get_object_url(self):
        """Retorna a URL do objeto se houver modelo e ID"""
        if self.content_type and self.object_id:
            try:
                obj = self.content_type.get_object_for_this_type(pk=self.object_id)
                if hasattr(obj, 'get_absolute_url'):
                    return obj.get_absolute_url()
            except:
                pass
        return None
    
    def get_summary(self):
        """Retorna um resumo legível da ação"""
        summary = f"{self.get_action_display()} em {self.get_module_display()}"
        if self.object_repr:
            summary += f": {self.object_repr}"
        if self.status_code and self.status_code >= 400:
            summary += f" (Erro {self.status_code})"
        return summary

