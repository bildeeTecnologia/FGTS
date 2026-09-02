-- 🚀 SCRIPT DE INDEXAÇÃO PARA SUPABASE
-- Executar isto na console SQL do Supabase para máxima performance
-- Data: 2026-01-02

-- ============================================================================
-- PARTE 1: Tabela `indices_fgts` (CRÍTICO - Gargalo Principal)
-- ============================================================================

-- 🔥 ÍNDICE MAIS IMPORTANTE: Competência + Data Base
-- Acelera a busca de índices que é feita a cada cálculo
CREATE INDEX IF NOT EXISTS idx_indices_fgts_comp_data
  ON indices_fgts (competencia, data_base)
  WHERE competencia IS NOT NULL AND data_base IS NOT NULL;

-- ✅ Busca simples por competência
CREATE INDEX IF NOT EXISTS idx_indices_fgts_competencia
  ON indices_fgts (competencia)
  WHERE competencia IS NOT NULL;

-- ✅ Ordenação descendente (recentes primeiro)
CREATE INDEX IF NOT EXISTS idx_indices_fgts_data_desc
  ON indices_fgts (data_base DESC)
  WHERE data_base IS NOT NULL;

-- ✅ Filtro por tabela (6 ou 7) + competência
CREATE INDEX IF NOT EXISTS idx_indices_fgts_tabela_comp
  ON indices_fgts (tabela, competencia)
  WHERE tabela IS NOT NULL AND competencia IS NOT NULL;

-- ============================================================================
-- PARTE 2: Estatísticas da Tabela indices_fgts
-- ============================================================================

-- Atualizar estatísticas para otimizador de queries
ANALYZE indices_fgts;

-- ============================================================================
-- PARTE 3: Verificar Índices Criados
-- ============================================================================

-- Verificar quais índices existem na tabela indices_fgts
SELECT
  schemaname,
  tablename,
  indexname,
  indexdef
FROM pg_indexes
WHERE tablename = 'indices_fgts'
ORDER BY indexname;

-- Verificar tamanho dos índices
SELECT
  schemaname,
  tablename,
  indexname,
  pg_size_pretty(pg_relation_size(indexrelid)) AS index_size
FROM pg_indexes
JOIN pg_class ON pg_class.relname = indexname
WHERE tablename = 'indices_fgts'
ORDER BY pg_relation_size(indexrelid) DESC;

-- ============================================================================
-- PARTE 4: Query de Teste (Executar ANTES e DEPOIS para comparar)
-- ============================================================================

-- ANTES (sem índice): Pode levar segundos
-- DEPOIS (com índice): Deve ser instantâneo
EXPLAIN ANALYZE
SELECT * FROM indices_fgts
WHERE competencia = DATE '2024-01-01'
  AND data_base = DATE '2026-01-19'
  AND tabela = 7;

-- ============================================================================
-- PARTE 5: Monitoramento Contínuo
-- ============================================================================

-- Ver size da tabela vs índices
SELECT
  pg_size_pretty(pg_total_relation_size('indices_fgts')) AS total_size,
  pg_size_pretty(pg_relation_size('indices_fgts')) AS table_size,
  pg_size_pretty(
    pg_total_relation_size('indices_fgts') - pg_relation_size('indices_fgts')
  ) AS indexes_size;

-- Ver índices não utilizados (podem ser removidos)
SELECT
  schemaname,
  tablename,
  indexname,
  idx_scan
FROM pg_stat_user_indexes
WHERE tablename = 'indices_fgts'
ORDER BY idx_scan DESC;

-- ============================================================================
-- PARTE 6: Dicas de Manutenção (executar mensalmente)
-- ============================================================================

-- VACUUM: Limpeza de espaço desperdiçado
VACUUM ANALYZE indices_fgts;

-- REINDEX: Reconstruir índices se ficarem fragmentados
-- (usar apenas se houver degradação de performance)
-- REINDEX TABLE CONCURRENTLY indices_fgts;
