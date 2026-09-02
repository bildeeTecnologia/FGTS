# ⚡ Sistema de Monitoramento - Quick Reference

## 🚀 Links Rápidos

| Item | URL | Requisito |
|------|-----|-----------|
| **Dashboard** | `/monitoring/dashboard/` | Superusuário |
| **Admin Logs** | `/admin/monitoring/performancelog/` | Staff |
| **Documentação Completa** | `GUIA_MONITORAMENTO_PERFORMANCE.md` | - |
| **Guia Visual** | `GUIA_DASHBOARD_VISUAL.md` | - |

---

## 📊 Métricas em 1 Minuto

### ✅ Sistema Saudável
```
Taxa Sucesso:    > 98%
Tempo Médio:     < 3s
Ops Longas:      < 10% do total
Gargalos:        0
```

### ⚠️ Precisa Atenção
```
Taxa Sucesso:    90-98%
Tempo Médio:     3-5s
Ops Longas:      10-30%
Gargalos:        1-2
```

### 🔴 Crítico
```
Taxa Sucesso:    < 90%
Tempo Médio:     > 5s
Ops Longas:      > 30%
Gargalos:        3+
```

---

## 🛠️ Comandos Úteis

### Ver Logs no Terminal
```bash
python manage.py shell
>>> from monitoring.models import PerformanceLog
>>> PerformanceLog.objects.filter(status='erro').count()
```

### Limpar Logs Antigos
```bash
python manage.py shell
>>> from monitoring.services import PerformanceAnalyzer
>>> PerformanceAnalyzer.limpar_logs_antigos(dias=30)
```

### Análise Rápida
```bash
python manage.py shell
>>> from monitoring.services import PerformanceAnalyzer
>>> resumo = PerformanceAnalyzer.resumo_ultima_24h()
>>> print(resumo)
```

### Ver Gargalos
```bash
python manage.py shell
>>> from monitoring.services import PerformanceAnalyzer
>>> for g in PerformanceAnalyzer.gargalos_identifıcados():
...     print(f"{g['operacao']}: {g['tempo_medio']:.2f}s")
```

---

## 🎯 Operações Rastreadas

| Operação | Código | Threshold |
|----------|--------|-----------|
| Relatório Competência | `relatorio_competencia` | > 1s |
| Relatório Funcionário | `relatorio_funcionario` | > 1s |
| Relatório Empresa | `relatorio_empresa` | > 1s |
| Consolidado Geral | `consolidado_geral` | > 1s |
| Importação Funcionários | `importacao_funcionarios` | > 1s |
| Importação Lançamentos | `importacao_lancamentos` | > 1s |
| Exportação CSV | `exportacao_csv` | > 1s |
| Exportação PDF | `exportacao_pdf` | > 1s |

---

## 🔍 Troubleshooting

### Problema: Dashboard não carrega
**Solução:**
1. Verificar se usuário é superusuário: `/admin/`
2. Checar se middleware está ativo em `settings.py`
3. Ver erro no terminal do runserver

### Problema: Nenhum log aparece
**Possíveis causas:**
- Nenhuma operação levou > 1s ainda (normal!)
- Middleware não está na lista em `settings.py`
- URL da operação não está mapeada em `OPERACOES_RASTREADAS`

**Solução:**
1. Gerar dados de teste: `python test_monitoring.py`
2. Verificar `settings.MIDDLEWARE` tem `PerformanceTrackingMiddleware`
3. Ver `monitoring/middleware.py` → `OPERACOES_RASTREADAS`

### Problema: Muitos logs acumulados
**Solução:**
```python
from monitoring.services import PerformanceAnalyzer
# Manter apenas últimos 30 dias
PerformanceAnalyzer.limpar_logs_antigos(dias=30)
# Ou últimos 7 dias
PerformanceAnalyzer.limpar_logs_antigos(dias=7)
```

### Problema: Operação específica não rastreada
**Solução:**
Adicionar em `monitoring/middleware.py`:
```python
OPERACOES_RASTREADAS = {
    # ... existentes ...
    'nome-da-url': 'codigo_operacao',  # ← ADICIONAR
}
```

E adicionar choice em `monitoring/models.py`:
```python
OPERACAO_CHOICES = [
    # ... existentes ...
    ('codigo_operacao', 'Nome Descritivo'),  # ← ADICIONAR
]
```

---

## 📈 Quando Otimizar?

### ❌ NÃO otimize agora se:
- Taxa de sucesso > 95%
- Tempo médio < 5s
- Usuários não reclamam
- Sistema está estável

### ✅ OTIMIZE quando:
- Taxa de sucesso < 90% (muitos erros)
- Tempo médio > 5s (consistentemente)
- > 30% operações lentas
- Usuários reportando lentidão

### 🎯 Estratégia:
1. **Monitorar:** 2-4 semanas de dados reais
2. **Analisar:** Identificar padrões e gargalos
3. **Priorizar:** Focar no que mais impacta
4. **Implementar:** Otimizar 1 item por vez
5. **Medir:** Comparar antes/depois
6. **Repetir:** Próximo gargalo

---

## 🔧 Manutenção Mensal

### Checklist (15 minutos/mês)

- [ ] Limpar logs > 30 dias
- [ ] Exportar resumo mensal para relatório
- [ ] Revisar top 5 operações mais lentas
- [ ] Documentar otimizações feitas (se houver)
- [ ] Ajustar thresholds se necessário
- [ ] Adicionar novas operações ao rastreamento (se necessário)

### Script de Manutenção
```python
# maintenance.py
from monitoring.services import PerformanceAnalyzer
from datetime import datetime

print("=== MANUTENÇÃO MENSAL - " + datetime.now().strftime('%B %Y') + " ===\n")

# 1. Resumo do mês
print("1. Resumo das últimas 24h (amostra):")
resumo = PerformanceAnalyzer.resumo_ultima_24h()
for key, val in resumo.items():
    print(f"   {key}: {val}")

# 2. Top 5 mais lentas
print("\n2. Top 5 operações mais lentas:")
for log in PerformanceAnalyzer.top_operacoes_lentas(limite=5, horas=24*30):
    print(f"   - {log.get_operacao_display()}: {log.duracao_segundos}s")

# 3. Gargalos
print("\n3. Gargalos identificados:")
gargalos = PerformanceAnalyzer.gargalos_identifıcados()
if gargalos:
    for g in gargalos:
        print(f"   ⚠️  {g['operacao']}: {g['tempo_medio']:.2f}s")
else:
    print("   ✅ Nenhum gargalo!")

# 4. Limpeza
print("\n4. Limpando logs antigos...")
deletados = PerformanceAnalyzer.limpar_logs_antigos(dias=30)
print(f"   ✅ Deletados {deletados} logs")

print("\n=== MANUTENÇÃO CONCLUÍDA ===")
```

---

## 📞 Suporte

### Documentação
- **Completa:** `GUIA_MONITORAMENTO_PERFORMANCE.md` (400+ linhas)
- **Visual:** `GUIA_DASHBOARD_VISUAL.md` (cenários e exemplos)
- **Implementação:** `SISTEMA_MONITORAMENTO_IMPLEMENTADO.md` (resumo técnico)

### Código
- **Modelos:** `monitoring/models.py`
- **Middleware:** `monitoring/middleware.py`
- **Services:** `monitoring/services.py`
- **Views:** `monitoring/views.py`
- **Admin:** `monitoring/admin.py`
- **Template:** `monitoring/templates/monitoring/dashboard.html`

### Teste
```bash
python test_monitoring.py
```

---

**💡 Lembre-se:** Monitor first, optimize later!

**Data de Implementação:** 03/01/2026  
**Versão:** 1.0.0  
**Status:** ✅ Operacional
