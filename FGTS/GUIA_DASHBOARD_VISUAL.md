# 📊 Guia Rápido - Dashboard de Monitoramento

## 🔗 Acesso ao Dashboard

**URL:** `http://127.0.0.1:8000/monitoring/dashboard/`

**Requisitos:**
- ✅ Usuário deve estar logado
- ✅ Usuário deve ser superusuário (`is_staff=True`)

---

## 📈 O Que Você Verá

### **1. Cards de Métricas (6 cards principais)**

```
┌─────────────────────────────────────────────────────────────────┐
│  📊 Total Operações  │  ✅ Taxa Sucesso  │  ⏱️ Tempo Médio    │
│       5              │      100.0%        │      4.50s          │
└─────────────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────────────┐
│  ⚠️ Tempo Máximo    │  🐌 Ops Longas    │  🔴 Ops M. Longas  │
│       5.50s          │        0           │         0           │
└─────────────────────────────────────────────────────────────────┘
```

### **2. Alertas de Gargalos**

Quando há operações problemáticas, você verá:

```
⚠️ GARGALOS IDENTIFICADOS

┌──────────────────────────────────────────────────────────────┐
│ Operação                  │ Tempo Médio │ % Lentas │ Total  │
├──────────────────────────────────────────────────────────────┤
│ Relatório por Competência │   8.5s      │   45%    │   20   │
│ Exportação PDF            │   12.3s     │   70%    │   8    │
└──────────────────────────────────────────────────────────────┘
```

### **3. Tabela: Operações por Tipo**

```
┌────────────────────────────────────────────────────────────────┐
│ Operação             │ Total │ Tempo Médio │ Tempo Max │ Erros │
├────────────────────────────────────────────────────────────────┤
│ Relatório Competência│   45  │    3.2s     │   8.5s    │   0   │
│ Importação Funcions  │   12  │    2.8s     │   5.1s    │   1   │
│ Exportação CSV       │   23  │    1.5s     │   3.2s    │   0   │
│ Exportação PDF       │   8   │    4.7s     │   9.8s    │   0   │
└────────────────────────────────────────────────────────────────┘
```

### **4. Tabela: Top 10 Operações Mais Lentas**

```
┌────────────────────────────────────────────────────────────────┐
│ Operação             │ Duração │ Status  │ Horário         │ IP│
├────────────────────────────────────────────────────────────────┤
│ Exportação PDF       │  9.8s   │ Sucesso │ 03/01 14:23:45  │..│
│ Relatório Competência│  8.5s   │ Sucesso │ 03/01 15:10:12  │..│
│ Importação Funcions  │  5.1s   │ Erro    │ 03/01 16:45:23  │..│
└────────────────────────────────────────────────────────────────┘
```

---

## 🎯 Interpretação das Métricas

### **Total de Operações**
- Quantas operações críticas foram executadas nas últimas 24h
- **Esperado:** Varia conforme uso (pode ser 0 em dias calmos)

### **Taxa de Sucesso**
- Percentual de operações que completaram sem erro
- 🟢 **Saudável:** > 95%
- 🟠 **Atenção:** 90-95%
- 🔴 **Crítico:** < 90%

### **Tempo Médio**
- Média de duração de todas as operações
- 🟢 **Bom:** < 3s
- 🟠 **Aceitável:** 3-5s
- 🔴 **Ruim:** > 5s

### **Tempo Máximo**
- Operação mais demorada nas últimas 24h
- 🟢 **OK:** < 5s
- 🟠 **Preocupante:** 5-15s
- 🔴 **Problema:** > 15s

### **Operações Longas (5-15s)**
- Quantidade de operações que levaram entre 5 e 15 segundos
- 🟢 **Ideal:** 0
- 🟠 **Aceitável:** < 10% do total
- 🔴 **Problema:** > 30% do total

### **Operações Muito Longas (>15s)**
- Quantidade de operações que levaram mais de 15 segundos
- 🟢 **Ideal:** 0
- 🔴 **Crítico:** Qualquer valor > 0 requer investigação

---

## 🔍 Quando Agir

### **Cenário 1: Taxa de Sucesso Baixa (<90%)**
**Problema:** Muitas operações falhando

**Ações:**
1. Verificar mensagens de erro no Admin Django
2. Checar logs de aplicação
3. Validar dados de entrada (planilhas XLSX)
4. Verificar conexão com banco de dados

### **Cenário 2: Tempo Médio Alto (>5s)**
**Problema:** Sistema lento em geral

**Ações:**
1. Identificar operação mais problemática (tabela "Por Tipo")
2. Verificar se há N+1 queries
3. Adicionar índices em campos frequentemente filtrados
4. Considerar cache para dados estáticos

### **Cenário 3: Muitas Operações Longas (>30%)**
**Problema:** Gargalo consistente

**Ações:**
1. Implementar processamento assíncrono (Celery)
2. Dividir operações grandes em chunks menores
3. Otimizar algoritmos de cálculo
4. Adicionar cache para resultados intermediários

### **Cenário 4: Operações Muito Longas Pontuais**
**Problema:** Picos de lentidão esporádicos

**Ações:**
1. Verificar volume de dados sendo processado
2. Checar carga do servidor no horário
3. Investigar queries específicas daquele request
4. Adicionar timeout para operações muito longas

---

## 🛠️ Como Investigar uma Operação Lenta

### **Passo 1: Identificar no Dashboard**
- Encontre a operação problemática na tabela "Top 10 Mais Lentas"
- Anote: timestamp, usuário, empresa

### **Passo 2: Ver Detalhes no Admin**
```
http://127.0.0.1:8000/admin/monitoring/performancelog/
```

1. Filtrar por:
   - Operação específica
   - Data/hora do problema
   - Usuário afetado

2. Abrir o registro individual

3. Analisar:
   - **entrada_dados**: O que foi enviado?
   - **saida_dados**: O que foi retornado?
   - **mensagem_erro**: Houve erro?
   - **duracao_segundos**: Quanto tempo levou exatamente?
   - **ip_cliente**: De onde veio a requisição?

### **Passo 3: Reproduzir Localmente**
Com os dados de `entrada_dados`, tente reproduzir:

```python
# Exemplo: testar importação que demorou 12s
from funcionarios.services import FuncionarioImportService

# Usar mesmos dados do log
service = FuncionarioImportService()
resultado = service.processar_arquivo(mesmo_arquivo_do_log)
```

### **Passo 4: Perfilar com Django Debug Toolbar**
Se necessário, instale Django Debug Toolbar para ver:
- Queries SQL executadas
- Tempo de cada query
- Templates renderizados
- Cache hits/misses

---

## 📅 Rotina de Monitoramento Sugerida

### **Diário (5 minutos)**
1. Acessar dashboard
2. Verificar se taxa de sucesso está > 95%
3. Checar se há alertas de gargalos

### **Semanal (15 minutos)**
1. Revisar tendência de performance
2. Identificar padrões (dias/horários de pico)
3. Limpar logs antigos se necessário:
   ```python
   from monitoring.services import PerformanceAnalyzer
   PerformanceAnalyzer.limpar_logs_antigos(dias=30)
   ```

### **Mensal (30 minutos)**
1. Análise profunda de gargalos recorrentes
2. Planejar otimizações necessárias
3. Documentar melhorias implementadas
4. Exportar métricas para relatório gerencial

---

## 🚨 Alertas Importantes

### **🔴 CRÍTICO - Ação Imediata**
- Taxa de sucesso < 80%
- Mais de 5 operações falhando na última hora
- Qualquer operação > 30 segundos

### **🟠 ATENÇÃO - Investigar Hoje**
- Taxa de sucesso 80-95%
- Mais de 30% operações lentas (>5s)
- Tempo médio aumentando consistentemente

### **🟡 OBSERVAR - Monitorar Próximos Dias**
- Taxa de sucesso 95-98%
- 10-30% operações lentas
- Operações específicas demorando ocasionalmente

### **🟢 SAUDÁVEL - Tudo OK**
- Taxa de sucesso > 98%
- < 10% operações lentas
- Tempo médio estável

---

## 💡 Dicas Extras

### **Adicionar Mais Operações ao Monitoramento**
Edite `monitoring/middleware.py`:

```python
OPERACOES_RASTREADAS = {
    'relatorio-competencia': 'relatorio_competencia',
    # ... existentes ...
    
    # ADICIONAR NOVOS:
    'nova-operacao': 'codigo_operacao',
}
```

E adicione à lista de choices em `monitoring/models.py`.

### **Ajustar Threshold de Tempo**
Por padrão, só registra operações > 1 segundo.

Para mudar, edite `monitoring/middleware.py`:

```python
# Linha ~45
if operacao_key and duracao > 1.0:  # ← Mudar este valor
```

### **Exportar Dados para Excel**
Use o Admin Django:
1. Ir para `/admin/monitoring/performancelog/`
2. Selecionar logs desejados
3. Ação: "Exportar para CSV"
4. Abrir CSV no Excel

---

## 📚 Documentação Adicional

- **Guia Completo:** `GUIA_MONITORAMENTO_PERFORMANCE.md` (400+ linhas)
- **Resumo de Implementação:** `SISTEMA_MONITORAMENTO_IMPLEMENTADO.md`
- **Código-fonte:** Pasta `monitoring/`

---

**🎯 Lembre-se:** O objetivo é MONITORAR por 2-4 semanas antes de otimizar!

**Não otimize prematuramente.** Deixe os dados te guiarem para onde está o **verdadeiro** gargalo.
