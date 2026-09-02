# REGRAS OFICIAIS - TABELAS DE ÍNDICES FGTS

## 📋 REGRA OBRIGATÓRIA E IMUTÁVEL

**Fonte**: Portaria MTE - Tabelas de coeficientes para recolhimento mensal em atraso, por data de pagamento

## 📊 TABELAS OFICIAIS

### Tabela 6 - Não optantes e optantes após 22/09/1971
**Competências abrangidas**: 01/1967 a 09/1989

### Tabela 7 - Não optantes e optantes após 22/09/1971  
**Competências abrangidas**: 10/1989 a 09/2025

## 🎯 REGRA DE SELEÇÃO AUTOMÁTICA

```python
DATA_CORTE = date(1989, 9, 1)  # 01/09/1989

if competencia <= DATA_CORTE:
    tabela = 6  # Competências até 09/1989
else:
    tabela = 7  # Competências de 10/1989 em diante
```

## ✅ IMPLEMENTAÇÃO NO SISTEMA

### Determinação Automática
O sistema **DETERMINA AUTOMATICAMENTE** qual tabela usar baseado na competência:

```python
# ✅ CORRETO - Tabela automática
indice = IndiceFGTSService.buscar_indice(
    competencia=date(2023, 1, 1),    # 01/2023
    data_pagamento=date(2025, 12, 29)
)
# Sistema usa Tabela 7 automaticamente (10/1989+)

# ✅ CORRETO - Tabela automática
indice = IndiceFGTSService.buscar_indice(
    competencia=date(1985, 6, 1),    # 06/1985
    data_pagamento=date(2025, 12, 29)
)
# Sistema usa Tabela 6 automaticamente (até 09/1989)
```

### Validação SQL
```sql
-- Query otimizada com tabela correta
SELECT indice 
FROM indices_fgts
WHERE competencia = '2023-01-01'
  AND data_base = '2025-12-29'
  AND tabela = 7;  -- Determinada automaticamente para 01/2023
```

## 🚫 PRÁTICAS PROIBIDAS

### ❌ NUNCA fazer:
```python
# ❌ ERRADO - Tabela fixa hardcoded
indice = buscar_indice(competencia, data_pagamento, tabela=1)

# ❌ ERRADO - Buscar todas as tabelas
indice = buscar_indice_qualquer_tabela(competencia, data_pagamento)

# ❌ ERRADO - Intervalo de tabelas no SQL
WHERE tabela IN (6, 7)  # Sem especificar qual
```

### ✅ SEMPRE fazer:
```python
# ✅ CORRETO - Deixar o sistema determinar
indice = IndiceFGTSService.buscar_indice(competencia, data_pagamento)

# ✅ CORRETO - Ou explicitamente se necessário
tabela = IndiceFGTSService.determinar_tabela(competencia)
indice = IndiceFGTSService.buscar_indice(competencia, data_pagamento, tabela)
```

## 📈 PERFORMANCE

### Índices Recomendados no Banco
```sql
-- Índice composto para busca exata (MAIS PERFORMÁTICO)
CREATE INDEX idx_indices_fgts_busca_exata 
ON indices_fgts(competencia, data_base, tabela);

-- Índice para queries por competência
CREATE INDEX idx_indices_fgts_competencia 
ON indices_fgts(competencia, tabela);

-- Índice para queries por data de pagamento
CREATE INDEX idx_indices_fgts_data_base 
ON indices_fgts(data_base, tabela);
```

### Query Otimizada
```sql
-- ✅ MAIS PERFORMÁTICA - Usa os 3 campos do índice composto
SELECT indice 
FROM indices_fgts
WHERE competencia = :competencia      -- 1º campo do índice
  AND data_base = :data_pagamento     -- 2º campo do índice
  AND tabela = :tabela_automatica;    -- 3º campo do índice

-- Explain mostra: Index Scan using idx_indices_fgts_busca_exata
```

## 🔒 IMUTABILIDADE

Esta regra é **CRÍTICA** e **IMUTÁVEL** porque:

1. ✅ **Conformidade Legal**: Baseada em Portaria oficial do MTE
2. ✅ **Precisão Financeira**: Cada tabela tem coeficientes específicos
3. ✅ **Auditabilidade**: Rastreamento correto dos cálculos
4. ✅ **Histórico**: Preserva cálculos de competências antigas (1967-1989)

## 📝 EXEMPLOS PRÁTICOS

### Exemplo 1: Competência Recente
```python
competencia = date(2023, 2, 1)      # 02/2023
data_pagamento = date(2025, 12, 29)
# Sistema usa Tabela 7 (10/1989+)
```

### Exemplo 2: Competência Histórica
```python
competencia = date(1988, 5, 1)      # 05/1988
data_pagamento = date(2025, 12, 29)
# Sistema usa Tabela 6 (até 09/1989)
```

### Exemplo 3: Competência no Corte
```python
competencia = date(1989, 9, 1)      # 09/1989
# Sistema usa Tabela 6 (última do range)

competencia = date(1989, 10, 1)     # 10/1989
# Sistema usa Tabela 7 (primeira do novo range)
```

## 🔍 VERIFICAÇÃO NO SUPABASE

```sql
-- Verificar qual tabela uma competência deve usar
SELECT 
    CASE 
        WHEN '2023-01-01'::date <= '1989-09-01'::date THEN 6
        ELSE 7
    END as tabela_correta;

-- Resultado: 7 (correto para 01/2023)
```

## 📚 REFERÊNCIAS

- **Portaria MTE**: Tabelas de coeficientes FGTS
- **Arquivo**: `REGRA_IMUTAVEL_INDICES_FGTS.md`
- **Código**: `indices/services/indice_service.py`
- **Constante**: `DATA_CORTE_TABELA = date(1989, 9, 1)`

---

**Última atualização**: 30/12/2025  
**Status**: REGRA ATIVA E OBRIGATÓRIA  
**Alterações**: Proibidas sem revisão legal
