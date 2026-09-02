-- ==============================================================================
-- SCRIPT DE PREPARAÇÃO PARA MIGRAÇÃO (RESET TOTAL)
-- ==============================================================================
-- ATENÇÃO: Execute este script no SQL Editor do Supabase.
-- ELE APAGARÁ TODOS OS DADOS E TABELAS DO SCHEMA 'public'.
-- Use apenas se você quiser limpar o banco para rodar a migração do zero.
-- ==============================================================================

-- 1. Derrubar o schema public (Cascata apaga tabelas, views, triggers)
DROP SCHEMA IF EXISTS public CASCADE;

-- 2. Recriar o schema public limpo
CREATE SCHEMA public;

-- 3. Restaurar permissões padrões do Supabase
GRANT USAGE ON SCHEMA public TO postgres, anon, authenticated, service_role;
GRANT ALL ON SCHEMA public TO postgres, anon, authenticated, service_role;

-- ==============================================================================
-- APÓS EXECUTAR ESTE SCRIPT:
-- 1. Volte para o seu computador.
-- 2. Execute o arquivo 'run_migration_full.bat'.
--    (Ele vai recriar as tabelas via Django e importar os dados do SQLite)
-- ==============================================================================

-- Verificação (Deve retornar 0 linhas)
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public';
