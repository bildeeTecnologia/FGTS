-- ================================================================
-- CONSULTAS DE ÍNDICES FGTS NO SUPABASE
-- ================================================================
-- 
-- REGRA OBRIGATÓRIA - SELEÇÃO DE TABELA:
-- ======================================
-- Tabela 6: Competências de 01/1967 até 09/1989
-- Tabela 7: Competências de 10/1989 até 09/2025
--
-- IMPORTANTE: Use a tabela CORRETA baseada na competência!
-- Data de corte: 1989-09-01
-- ================================================================

-- 1. VERIFICAR SE EXISTE ÍNDICE PARA COMPETÊNCIA E DATA ESPECÍFICA
-- MAIS PERFORMÁTICA: Usa índice composto (competencia, data_base, tabela)
SELECT 
    competencia,
    data_base,
    tabela,
    indice
FROM indices_fgts
WHERE competencia = '2023-02-01'  -- Competência (sempre dia 1)
  AND data_base = '2025-12-29'    -- Data de pagamento
  AND tabela = 7;                 -- Tabela 7 para competências >= 10/1989

-- ================================================================

-- 2. LISTAR TODOS OS ÍNDICES DISPONÍVEIS PARA UMA COMPETÊNCIA
SELECT 
    competencia,
    data_base,
    tabela,
    indice,
    TO_CHAR(data_base, 'DD/MM/YYYY') as data_formatada
FROM indices_fgts
WHERE competencia = '2023-02-01'
  AND tabela = 7  -- Tabela 7 para competências >= 10/1989
ORDER BY data_base ASC;

-- ================================================================

-- 3. VERIFICAR RANGE DE DATAS DISPONÍVEIS PARA UMA COMPETÊNCIA
SELECT 
    competencia,
    tabela,
    MIN(data_base) as primeira_data,
    MAX(data_base) as ultima_data,
    COUNT(*) as total_indices
FROM indices_fgts
WHERE competencia = '2023-02-01'
  AND tabela = 7  -- Tabela 7 para competências >= 10/1989
GROUP BY competencia, tabela;

-- ================================================================

-- 4. LISTAR TODAS AS COMPETÊNCIAS DISPONÍVEIS (POR TABELA)
SELECT DISTINCT 
    competencia,
    TO_CHAR(competencia, 'MM/YYYY') as competencia_formatada,
    tabela,
    CASE 
        WHEN tabela = 6 THEN '01/1967 a 09/1989'
        WHEN tabela = 7 THEN '10/1989 a 09/2025'
    END as range_competencias,
    COUNT(*) as total_indices
FROM indices_fgts
WHERE tabela IN (6, 7)
GROUP BY competencia, tabela
ORDER BY competencia DESC;

-- ================================================================

-- 5. BUSCAR ÍNDICES MAIS RECENTES (ÚLTIMOS 30 DIAS)
SELECT 
    competencia,
    TO_CHAR(competencia, 'MM/YYYY') as comp_formatada,
    data_base,
    TO_CHAR(data_base, 'DD/MM/YYYY') as data_formatada,
    tabela,
    CASE 
        WHEN tabela = 6 THEN 'Tabela 6 (até 09/1989)'
        WHEN tabela = 7 THEN 'Tabela 7 (10/1989+)'
    END as descricao_tabela,
    indice
FROM indices_fgts
WHERE data_base >= CURRENT_DATE - INTERVAL '30 days'
  AND tabela IN (6, 7)
ORDER BY data_base DESC, competencia DESC
LIMIT 50;

-- ================================================================

-- 6. VERIFICAR SE EXISTE ÍNDICE PARA DATA DE PAGAMENTO ESPECÍFICA
-- (qualquer competência) - OTIMIZADO POR TABELA
SELECT 
    competencia,
    TO_CHAR(competencia, 'MM/YYYY') as comp_formatada,
    data_base,
    TO_CHAR(data_base, 'DD/MM/YYYY') as data_formatada,
    tabela,
    indice
FROM indices_fgts
WHERE data_base = '2025-12-29'
  AND tabela = 7  -- Use tabela correta baseada na competência esperada
ORDER BY competencia;

-- ================================================================

-- 7. BUSCAR ÍNDICES POR INTERVALO DE COMPETÊNCIAS
-- IMPORTANTE: Todas competências 2023 usam Tabela 7
SELECT 
    competencia,
    TO_CHAR(competencia, 'MM/YYYY') as comp_formatada,
    data_base,
    TO_CHAR(data_base, 'DD/MM/YYYY') as data_formatada,
    tabela,
    indice
FROM indices_fgts
WHERE competencia BETWEEN '2023-01-01' AND '2023-12-01'
  AND data_base = '2025-12-23'
  AND tabela = 7  -- Tabela 7 para todas competências de 2023
ORDER BY competencia;

-- ================================================================

-- 8. ESTATÍSTICAS GERAIS POR TABELA
SELECT 
    tabela,
    CASE 
        WHEN tabela = 6 THEN 'Tabela 6 (01/1967 a 09/1989)'
        WHEN tabela = 7 THEN 'Tabela 7 (10/1989 a 09/2025)'
    END as descricao,
    COUNT(*) as total_registros,
    COUNT(DISTINCT competencia) as total_competencias,
    TO_CHAR(MIN(competencia), 'MM/YYYY') as primeira_competencia,
    TO_CHAR(MAX(competencia), 'MM/YYYY') as ultima_competencia,
    TO_CHAR(MIN(data_base), 'DD/MM/YYYY') as primeira_data_base,
    TO_CHAR(MAX(data_base), 'DD/MM/YYYY') as ultima_data_base
FROM indices_fgts
WHERE tabela IN (6, 7)
GROUP BY tabela
ORDER BY tabela;

-- ================================================================

-- 9. VERIFICAR ÍNDICES PRÓXIMOS À DATA (CASO NÃO ENCONTRE EXATO)
-- ATENÇÃO: Use apenas para análise, NUNCA para cálculos reais
SELECT 
    competencia,
    TO_CHAR(competencia, 'MM/YYYY') as comp_formatada,
    data_base,
    TO_CHAR(data_base, 'DD/MM/YYYY') as data_formatada,
    tabela,
    indice,
    ABS(EXTRACT(DAY FROM (data_base - '2025-12-29'::date))) as dias_diferenca
FROM indices_fgts
WHERE competencia = '2023-02-01'
  AND tabela = 7  -- Tabela 7 para 02/2023 (>= 10/1989)
ORDER BY dias_diferenca ASC
LIMIT 10;

-- ================================================================

-- 10. BUSCAR ÍNDICE PARA MÚLTIPLAS COMPETÊNCIAS (EXEMPLO DE RELATÓRIO)
-- Útil para gerar relatórios consolidados - Todas 2023 usam Tabela 7
SELECT 
    competencia,
    TO_CHAR(competencia, 'MM/YYYY') as comp_formatada,
    data_base,
    TO_CHAR(data_base, 'DD/MM/YYYY') as data_formatada,
    tabela,
    indice
FROM indices_fgts
WHERE competencia IN ('2023-01-01', '2023-02-01', '2023-03-01', '2023-04-01', '2023-05-01')
  AND data_base = '2025-12-23'
  AND tabela = 7  -- Tabela 7 para todas competências de 2023
ORDER BY competencia;

-- ================================================================

-- 11. VERIFICAR SE HÁ DUPLICATAS (NÃO DEVERIA EXISTIR)
SELECT 
    competencia,
    TO_CHAR(competencia, 'MM/YYYY') as comp_formatada,
    data_base,
    TO_CHAR(data_base, 'DD/MM/YYYY') as data_formatada,
    tabela,
    COUNT(*) as ocorrencias
FROM indices_fgts
GROUP BY competencia, data_base, tabela
HAVING COUNT(*) > 1;

-- ================================================================

-- 12. FUNÇÃO AUXILIAR: DETERMINAR TABELA CORRETA
-- Use para saber qual tabela uma competência deve usar
SELECT 
    '2023-02-01'::date as competencia,
    CASE 
        WHEN '2023-02-01'::date <= '1989-09-01'::date THEN 6
        ELSE 7
    END as tabela_correta,
    CASE 
        WHEN '2023-02-01'::date <= '1989-09-01'::date 
        THEN 'Tabela 6: 01/1967 a 09/1989'
        ELSE 'Tabela 7: 10/1989 a 09/2025'
    END as descricao;

-- ================================================================

-- EXEMPLO PRÁTICO: Buscar índice para o teste que você estava fazendo
-- Competência: 02/2023 (2023-02-01)
-- Data Pagamento: 29/12/2025
-- Tabela: 7 (determinada automaticamente pois 02/2023 >= 10/1989)
SELECT 
    CASE 
        WHEN COUNT(*) > 0 THEN 'ÍNDICE ENCONTRADO ✓'
        ELSE 'ÍNDICE NÃO ENCONTRADO ✗'
    END as status,
    competencia,
    TO_CHAR(competencia, 'MM/YYYY') as comp_formatada,
    data_base,
    TO_CHAR(data_base, 'DD/MM/YYYY') as data_formatada,
    tabela,
    indice
FROM indices_fgts
WHERE competencia = '2023-02-01'
  AND data_base = '2025-12-29'
  AND tabela = 7  -- Tabela 7 (determinada: 02/2023 >= 10/1989)
GROUP BY competencia, data_base, tabela, indice;

-- ================================================================
-- EXEMPLO: Buscar índice para competência histórica
-- Competência: 05/1988 (1988-05-01)
-- Data Pagamento: 29/12/2025
-- Tabela: 6 (determinada automaticamente pois 05/1988 <= 09/1989)
SELECT 
    CASE 
        WHEN COUNT(*) > 0 THEN 'ÍNDICE ENCONTRADO ✓'
        ELSE 'ÍNDICE NÃO ENCONTRADO ✗'
    END as status,
    competencia,
    TO_CHAR(competencia, 'MM/YYYY') as comp_formatada,
    data_base,
    TO_CHAR(data_base, 'DD/MM/YYYY') as data_formatada,
    tabela,
    indice
FROM indices_fgts
WHERE competencia = '1988-05-01'
  AND data_base = '2025-12-29'
  AND tabela = 6  -- Tabela 6 (determinada: 05/1988 <= 09/1989)
GROUP BY competencia, data_base, tabela, indice;
