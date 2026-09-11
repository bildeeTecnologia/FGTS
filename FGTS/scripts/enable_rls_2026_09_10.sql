-- ========================================================
-- Habilitar RLS nas tabelas sinalizadas pelo Supabase Linter
-- Data: 10/09/2026
-- Uso: cole e execute este script no Supabase SQL Editor
-- (Project > SQL Editor > New query)
-- ========================================================
--
-- CONTEXTO / POR QUE É SEGURO:
-- - O Django conecta no Postgres com o usuário "postgres" (superusuário),
--   que SEMPRE ignora RLS, independente de existirem políticas.
-- - A única chamada via API REST (indices/services/supabase_client.py)
--   usa a SUPABASE_KEY = service_role, que também ignora RLS.
-- - Logo, habilitar RLS aqui só passa a bloquear acesso das roles
--   "anon" e "authenticated" (PostgREST), que hoje NÃO são usadas
--   por nenhuma dessas tabelas. Ou seja: zero impacto na aplicação.
--
-- Este script é idempotente: pode ser executado mais de uma vez
-- sem erro (tabelas inexistentes são ignoradas, políticas duplicadas
-- não são recriadas).
-- ========================================================

-- ========================================================
-- 1) ATIVAR RLS EM TODAS AS TABELAS SINALIZADAS
-- ========================================================

DO $$
DECLARE
  tabela text;
  tabelas text[] := ARRAY[
    'staging',
    'django_apscheduler_djangojob',
    'django_apscheduler_djangojobexecution',
    'usuarios_usuario',
    'lancamentos_lancamento',
    'billing_pricingplan',
    'empresas_empresa',
    'monitoring_performancelog',
    'coefjam_coefjam',
    'indices_fgts',
    'funcionarios_funcionario',
    'django_migrations',
    'indices_indice',
    'django_content_type',
    'auth_permission',
    'auth_group',
    'auth_group_permissions',
    'billing_subscription',
    'audit_logs_auditlog',
    'billing_billingcustomer',
    'django_admin_log',
    'django_session',
    'billing_plan',
    'empresas_grupoempresa',
    'empresas_empresafeature',
    'lancamentos_importacaoextratoanalitico',
    'configuracoes_configuracao',
    'lancamentos_conferencia',
    'teste_tabela',
    'empresas_relatoriopremium',
    'lancamentos_importacaore',
    'usuarios_usuario_empresas_permitidas',
    'usuarios_usuario_groups',
    'usuarios_usuario_user_permissions',
    'empresas_funcionariovinculo',
    'empresas_tipovinculo',
    'empresas_emaillog',
    'usuarios_empresausuariorole',
    'empresas_transferenciafuncionario',
    'billing_payment',
    'billing_feedback',
    'billing_planobpo',
    'billing_contabpo',
    'billing_empresabpo',
    'lancamentos_importacaoresponsabilidade',
    'billing_faturabpo',
    'empresas_leademailflow',
    'lancamentos_importacaolancamento',
    'lancamentos_relatoriotask'
  ];
BEGIN
  FOREACH tabela IN ARRAY tabelas LOOP
    IF EXISTS (
      SELECT 1 FROM pg_tables
      WHERE schemaname = 'public' AND tablename = tabela
    ) THEN
      EXECUTE format('ALTER TABLE public.%I ENABLE ROW LEVEL SECURITY;', tabela);
    END IF;
  END LOOP;
END $$;

-- ========================================================
-- 2) POLÍTICAS DE LEITURA PÚBLICA PARA DADOS DE REFERÊNCIA
-- (índices oficiais e planos exibidos na página pública de preços)
-- ========================================================

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies WHERE schemaname = 'public'
      AND tablename = 'indices_fgts' AND policyname = 'Leitura publica indices_fgts'
  ) THEN
    CREATE POLICY "Leitura publica indices_fgts" ON public.indices_fgts
      FOR SELECT USING (true);
  END IF;

  IF EXISTS (SELECT 1 FROM pg_tables WHERE schemaname = 'public' AND tablename = 'indices_indice')
     AND NOT EXISTS (
       SELECT 1 FROM pg_policies WHERE schemaname = 'public'
         AND tablename = 'indices_indice' AND policyname = 'Leitura publica indices_indice'
     ) THEN
    CREATE POLICY "Leitura publica indices_indice" ON public.indices_indice
      FOR SELECT USING (true);
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_policies WHERE schemaname = 'public'
      AND tablename = 'coefjam_coefjam' AND policyname = 'Leitura publica coefjam_coefjam'
  ) THEN
    CREATE POLICY "Leitura publica coefjam_coefjam" ON public.coefjam_coefjam
      FOR SELECT USING (true);
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_policies WHERE schemaname = 'public'
      AND tablename = 'billing_plan' AND policyname = 'Leitura publica billing_plan'
  ) THEN
    CREATE POLICY "Leitura publica billing_plan" ON public.billing_plan
      FOR SELECT USING (true);
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_policies WHERE schemaname = 'public'
      AND tablename = 'billing_pricingplan' AND policyname = 'Leitura publica billing_pricingplan'
  ) THEN
    CREATE POLICY "Leitura publica billing_pricingplan" ON public.billing_pricingplan
      FOR SELECT USING (true);
  END IF;
END $$;

-- Todas as demais tabelas ficam com RLS ativo e SEM políticas para
-- anon/authenticated (acesso negado por padrão via API REST).
-- Django (postgres) e o backend (service_role) continuam com acesso
-- total, pois ambos ignoram RLS.

-- ========================================================
-- 3) VERIFICAÇÃO
-- ========================================================
-- Deve retornar rowsecurity = true para todas as linhas.

SELECT schemaname, tablename, rowsecurity
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY tablename;
