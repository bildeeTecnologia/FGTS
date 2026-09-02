-- ==============================================================================
-- SCRIPT DE LIMPEZA SELETIVA (PRESERVA DADOS EXTERNOS)
-- ==============================================================================
-- ATENÇÃO: Execute este script no SQL Editor do Supabase.
-- Ele apagará APENAS as tabelas que conflitam com o Django, mantendo outras.
-- ==============================================================================

-- 1. Remover APENAS tabelas de lixo/teste
DROP TABLE IF EXISTS public."TesteConexao" CASCADE;

-- ==============================================================================
-- TABELAS PRESERVADAS (NÃO SERÃO TOCADAS):
-- 1. indices_fgts (Fonte da verdade / Externa)
-- 2. n8n_chat_histories (Automação)
-- ==============================================================================

-- 2. Garantir que o Django possa criar suas tabelas
-- (Nenhuma ação extra necessária, o migrate cuidará do resto)

-- Verificação final (Deve listar apenas 'n8n_chat_histories')
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public';
