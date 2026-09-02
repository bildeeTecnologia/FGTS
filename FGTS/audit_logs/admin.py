from django.contrib import admin
from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'user', 'action', 'module', 'object_repr', 'status_code', 'ip_address')
    list_filter = ('action', 'module', 'timestamp', 'user', 'status_code')
    search_fields = ('user__username', 'object_repr', 'ip_address', 'error_message', 'description')
    readonly_fields = ('user', 'action', 'module', 'view_name', 'url_path', 'content_type', 'object_id', 
                      'object_repr', 'description', 'old_values', 'new_values', 'changes', 
                      'ip_address', 'user_agent', 'timestamp', 'status_code', 'error_message', 'method')
    date_hierarchy = 'timestamp'
    
    fieldsets = (
        ('Identificação (Quem)', {
            'fields': ('user', 'ip_address', 'user_agent')
        }),
        ('Contexto Temporal (Quando)', {
            'fields': ('timestamp',)
        }),
        ('Contexto de Localização (Onde)', {
            'fields': ('module', 'view_name', 'url_path')
        }),
        ('Ação (O que)', {
            'fields': ('action', 'method', 'content_type', 'object_id', 'object_repr')
        }),
        ('Detalhes da Ação (Por quê)', {
            'fields': ('description', 'old_values', 'new_values', 'changes')
        }),
        ('Resultado', {
            'fields': ('status_code', 'error_message')
        }),
    )
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False

