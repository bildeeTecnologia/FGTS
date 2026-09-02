from django.contrib import admin
from .models import PerformanceLog


@admin.register(PerformanceLog)
class PerformanceLogAdmin(admin.ModelAdmin):
    list_display = [
        'operacao', 'status', 'usuario', 'empresa_id', 
        'duracao_segundos', 'tempo_inicio', 'tempo_muito_longo_flag'
    ]
    list_filter = ['operacao', 'status', 'empresa_id', 'tempo_inicio']
    search_fields = ['usuario__username', 'mensagem_erro']
    readonly_fields = ['tempo_inicio', 'entrada_dados', 'saida_dados', 'mensagem_erro']
    ordering = ['-tempo_inicio']
    
    fieldsets = (
        ('Operação', {
            'fields': ('operacao', 'status', 'usuario', 'empresa_id')
        }),
        ('Timing', {
            'fields': ('tempo_inicio', 'tempo_final', 'duracao_segundos')
        }),
        ('Detalhes', {
            'fields': ('entrada_dados', 'saida_dados', 'mensagem_erro')
        }),
        ('Contexto', {
            'fields': ('ip_cliente', 'user_agent')
        }),
    )
    
    def tempo_muito_longo_flag(self, obj):
        """Mostra flag se levou muito tempo"""
        from django.utils.html import format_html
        if obj.tempo_muito_longo:
            return format_html('<span style="color: red; font-weight: bold;">⚠️ Muito longo (>15s)</span>')
        elif obj.tempo_longo:
            return format_html('<span style="color: orange;">⚠️ Longo (>5s)</span>')
        return format_html('<span style="color: green;">✅ Rápido</span>')
    tempo_muito_longo_flag.short_description = 'Duração'
