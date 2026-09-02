"""
Service para análise de performance
"""
from datetime import timedelta
from django.utils.timezone import now
from django.db.models import Avg, Count, Q, Max, Min
from .models import PerformanceLog


class PerformanceAnalyzer:
    """Analisa dados de performance do sistema"""
    
    @staticmethod
    def resumo_ultima_24h():
        """Resumo de performance das últimas 24 horas"""
        limite = now() - timedelta(hours=24)
        
        logs = PerformanceLog.objects.filter(tempo_inicio__gte=limite)
        
        return {
            'total_operacoes': logs.count(),
            'taxa_sucesso': f"{(logs.filter(status='sucesso').count() / max(logs.count(), 1) * 100):.1f}%",
            'tempo_medio': logs.aggregate(Avg('duracao_segundos'))['duracao_segundos__avg'],
            'tempo_maximo': logs.aggregate(Max('duracao_segundos'))['duracao_segundos__max'],
            'operacoes_longas': logs.filter(duracao_segundos__gt=5).count(),
            'operacoes_muito_longas': logs.filter(duracao_segundos__gt=15).count(),
            'erros': logs.filter(status='erro').count(),
        }
    
    @staticmethod
    def top_operacoes_lentas(limite=10, horas=24):
        """Top operações mais lentas"""
        limite_tempo = now() - timedelta(hours=horas)
        
        return PerformanceLog.objects.filter(
            tempo_inicio__gte=limite_tempo,
            status='sucesso'
        ).order_by('-duracao_segundos')[:limite]
    
    @staticmethod
    def operacoes_por_tipo(horas=24):
        """Breakdown de operações por tipo"""
        limite_tempo = now() - timedelta(hours=horas)
        
        operacoes = PerformanceLog.objects.filter(
            tempo_inicio__gte=limite_tempo
        ).values('operacao').annotate(
            total=Count('id'),
            tempo_medio=Avg('duracao_segundos'),
            tempo_maximo=Max('duracao_segundos'),
            erros=Count('id', filter=Q(status='erro'))
        ).order_by('-total')
        
        return operacoes
    
    @staticmethod
    def tendencia_performance(dias=7):
        """Tendência de performance nos últimos N dias"""
        limite_tempo = now() - timedelta(days=dias)
        
        logs = PerformanceLog.objects.filter(
            tempo_inicio__gte=limite_tempo,
            status='sucesso'
        ).values('operacao').annotate(
            tempo_medio=Avg('duracao_segundos'),
            dia=Count('id')
        )
        
        # Agrupar por dia
        tendencia = {}
        for log in logs:
            dia = log['tempo_inicio'].date()
            if dia not in tendencia:
                tendencia[dia] = {
                    'operacoes': 0,
                    'tempo_medio': 0
                }
            tendencia[dia]['operacoes'] += log['dia']
            tendencia[dia]['tempo_medio'] = log['tempo_medio']
        
        return dict(sorted(tendencia.items()))
    
    @staticmethod
    def gargalos_identifıcados():
        """Identifica gargalos (operações que consistentemente demoram)"""
        limite_tempo = now() - timedelta(hours=24)
        
        gargalos = []
        
        operacoes = PerformanceLog.objects.filter(
            tempo_inicio__gte=limite_tempo,
            status='sucesso'
        ).values('operacao').annotate(
            total=Count('id'),
            tempo_medio=Avg('duracao_segundos'),
            tempo_maximo=Max('duracao_segundos'),
            operacoes_lentas=Count('id', filter=Q(duracao_segundos__gt=5))
        ).filter(total__gte=3)  # Pelo menos 3 execuções
        
        for op in operacoes:
            percentual_lento = (op['operacoes_lentas'] / op['total'] * 100) if op['total'] > 0 else 0
            
            if percentual_lento > 30 or op['tempo_medio'] > 5:
                gargalos.append({
                    'operacao': PerformanceLog.OPERACAO_CHOICES[
                        [c[0] for c in PerformanceLog.OPERACAO_CHOICES].index(op['operacao'])
                    ][1],
                    'tempo_medio': op['tempo_medio'],
                    'tempo_maximo': op['tempo_maximo'],
                    'percentual_lento': percentual_lento,
                    'total_execucoes': op['total'],
                    'operacoes_lentas': op['operacoes_lentas']
                })
        
        return sorted(gargalos, key=lambda x: x['tempo_medio'], reverse=True)
    
    @staticmethod
    def limpar_logs_antigos(dias=30):
        """Remove logs mais antigos que N dias"""
        limite_tempo = now() - timedelta(days=dias)
        total_deletado = PerformanceLog.objects.filter(
            tempo_inicio__lt=limite_tempo
        ).delete()[0]
        
        return total_deletado
