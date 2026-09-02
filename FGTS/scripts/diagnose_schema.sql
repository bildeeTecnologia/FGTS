-- ==============================================================================
-- DIAGNÓSTICO DE ESTRUTURA DO BANCO DE DADOS
-- ==============================================================================
-- Execute este script no Supabase SQL Editor para listar todas as tabelas e colunas
-- existentes no schema 'public'.
-- ==============================================================================

SELECT 
    t.table_name,
    COUNT(c.column_name) as total_columns,
    STRING_AGG(c.column_name || ' (' || c.data_type || ')', ', ') as columns_structure
FROM 
    information_schema.tables t
JOIN 
    information_schema.columns c ON t.table_name = c.table_name
WHERE 
    t.table_schema = 'public'
GROUP BY 
    t.table_name
ORDER BY 
    t.table_name;
