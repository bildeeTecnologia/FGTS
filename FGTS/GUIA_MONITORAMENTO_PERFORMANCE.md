# 📊 Guia de Monitoramento e Performance

## 📌 O Que Foi Implementado

Um **sistema completo de logging e monitoramento** para rastrear performance de operações críticas do seu sistema:

- ✅ **Middleware de Rastreamento** - Captura tempo de todas as operações críticas
- ✅ **Modelo de Logs** - Armazena dados detalhados em banco de dados
- ✅ **Dashboard de Performance** - Visualiza métricas em tempo real
- ✅ **Análise Automatizada** - Identifica gargalos e problemas
- ✅ **Admin Django** - Consulte todos os logs detalhadamente

---

## 🎯 Operações Rastreadas

O middleware automaticamente registra:

| Operação | Descrição |
|----------|-----------|
| **relatorio_competencia** | Cálculo de relatórios por competência |
| **exportacao_csv** | Exportação para CSV |
| **exportacao_pdf** | Exportação para PDF |
| **importacao_funcionarios** | Importação em lote de funcionários |
| **importacao_lancamentos** | Importação em lote de lançamentos |
| **calculo_fgts** | Cálculos FGTS diretos |
| **geracao_lancamentos** | Geração automática de lançamentos |

---

## 🚀 Como Usar

### 1️⃣ Acessar o Dashboard

1. Acesse: `http://seu-site.com/monitoring/dashboard/`
2. **Requer permissão**: Apenas superuser ou staff
3. Visualize em tempo real:
   - Resumo de operações (últimas 24h)
   - Gargalos identificados
   - Operações mais lentas
   - Taxa de sucesso

### 2️⃣ Consultar Logs Detalhados

Admin Django: `http://seu-site.com/admin/monitoring/performancelog/`

Filtros disponíveis:
- Por operação
- Por status (sucesso/erro/timeout)
- Por empresa
- Por período

### 3️⃣ Interpretar os Dados

**Cores e Badges:**
- 🟢 **Verde** (< 5s) - Desempenho normal
- 🟠 **Laranja** (5-15s) - Operação lenta
- 🔴 **Vermelho** (> 15s) - Operação muito lenta

**Gargalos:**
- Identificados automaticamente
- Quando: tempo médio > 5s OU > 30% das execuções são lentas
- Recomendação: Otimizar com cache ou Celery

---

## 📈 Métricas Disponíveis

### Resumo 24h
```
- Total de operações
- Taxa de sucesso (%)
- Tempo médio (segundos)
- Máximo (segundos)
- Operações lentas (5-15s)
- Operações muito lentas (>15s)
- Quantidade de erros
```

### Por Operação
```
- Total de execuções
- Tempo médio
- Tempo máximo
- Quantidade de erros
- Taxa de sucesso
```

### Top 10 Mais Lentas
```
- Nome da operação
- Duração exata
- Usuário que executou
- Empresa envolvida
- Status (sucesso/erro)
- Horário exato
```

---

## 🔍 Analisando Gargalos

### Exemplo: Relatório muito lento

```
Dashboard mostra:
- Operação: "Relatório por Competência"
- Tempo médio: 18.5s
- Máximo: 35.2s
- 60% das execuções > 5s
- Status: 🔴 GARGALO IDENTIFICADO
```

**Ações recomendadas:**
1. ✅ Revisar competências múltiplas (quantas são?)
2. ✅ Verificar se 50+ funcionários (limite sugerido)
3. ✅ Se recorrente: implementar **Celery + Cache**
4. ✅ Se raro: talvez indexação melhor no BD

---

## 🛠️ Manutenção

### Limpar Logs Antigos

Por padrão, logs acumulam-se indefinidamente. Para manutenção do BD:

```python
# No Django shell
python manage.py shell

from monitoring.services import PerformanceAnalyzer

# Remover logs > 30 dias
PerformanceAnalyzer.limpar_logs_antigos(dias=30)
# Retorna: quantidade deletada

# Sugestão: Agendar task diária (cron)
```

### Monitorar em Tempo Real

```python
from monitoring.services import PerformanceAnalyzer

# Último dia
resumo = PerformanceAnalyzer.resumo_ultima_24h()
print(f"Taxa sucesso: {resumo['taxa_sucesso']}")

# Gargalos atuais
gargalos = PerformanceAnalyzer.gargalos_identifıcados()
for g in gargalos:
    print(f"{g['operacao']}: {g['tempo_medio']}s")
```

---

## 📊 Interpretando Resultados

### Cenário 1: Sistema Rápido ✅

```
Total Operações: 250
Taxa Sucesso: 100%
Tempo Médio: 1.2s
Operações Lentas: 3
Muito Lentas: 0
Gargalos: Nenhum

✅ Seu sistema está com bom desempenho!
```

### Cenário 2: Gargalo Detectado 🔴

```
Total Operações: 150
Taxa Sucesso: 95%
Tempo Médio: 3.5s
Operações Lentas: 45
Muito Lentas: 12
Gargalos: 2 operações identificadas

⚠️ Recomendação: Implementar Celery + Cache
```

### Cenário 3: Erros Frequentes ❌

```
Total Operações: 100
Taxa Sucesso: 80%
Tempo Médio: 2.1s
Operações Lentas: 5
Muito Lentas: 0
Erros: 20

🔴 Problema: Alta taxa de erro
- Verificar logs de erro no admin
- Revisar permissões de usuários
- Validar integridade de dados
```

---

## 🎯 Próximos Passos (Quando Necessário)

Com base nos dados do Dashboard:

### Se 60% das operações demoram > 5s
→ **Implementar Celery + Redis**
- Libera requisição HTTP imediatamente
- Processamento em background

### Se mesmas operações são executadas frequentemente
→ **Adicionar Cache (Redis/Memcached)**
- Reutilizar resultados
- Reduz tempo em 100-1000x

### Se erros específicos recorrem
→ **Aumentar recursos ou otimizar BD**
- Adicionar índices
- Revisar queries N+1
- Normalizar schema

---

## 📝 Logs do Sistema

### O que é registrado por operação:

```python
{
    "operacao": "relatorio_competencia",
    "status": "sucesso",
    "usuario": "username",
    "empresa": "Empresa A",
    "tempo_inicio": "2026-01-03 15:30:00",
    "duracao_segundos": 5.234,
    "entrada_dados": {
        "metodo": "POST",
        "url": "/lancamentos/relatorio/",
        "params": {"empresa": "3"}
    },
    "ip_cliente": "192.168.1.100",
    "status": "sucesso"
}
```

---

## ⚠️ Alertas Automáticos

O sistema **NÃO envia alertas** por enquanto, mas você pode:

1. **Verificar Dashboard diariamente** (2min)
2. **Consultar Admin** quando suspeitar de problemas
3. **Usar scripts** para análise automática

---

## 🎓 Resumo de Melhores Práticas

✅ **Faça:**
- Monitore regularmente (1x por semana)
- Identifique padrões de lentidão
- Documente mudanças após otimizações
- Limpe logs > 30 dias

❌ **Evite:**
- Ignorar gargalos recorrentes
- Esperar reclamações de usuários
- Manter logs indefinidamente
- Implementar Celery sem dados

---

## 📞 Suporte

Dúvidas sobre os dados?

1. Consulte documentação acima
2. Verifique logs no admin Django
3. Execute análises no shell Django
4. Implemente otimizações conforme recomendações

---

**Data de Implementação:** 03/01/2026  
**Versão:** 1.0  
**Status:** ✅ Pronto para Produção
