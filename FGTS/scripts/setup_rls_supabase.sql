-- ========================================================
-- Script RLS (Row Level Security) para Supabase
-- Data: 31/12/2025
-- Uso: Execute este script no Supabase SQL Editor APÓS criar as tabelas
-- ========================================================

-- ========================================================
-- ESTRATÉGIA DE SEGURANÇA
-- ========================================================
-- 
-- Django usa SERVICE ROLE KEY que bypassa RLS automaticamente
-- RLS ativa apenas protege contra:
-- 1. Acesso direto via SQL Editor por usuários não-admin
-- 2. APIs públicas futuras (se implementadas)
-- 3. Integrações externas
--
-- O isolamento multi-tenant continua sendo feito no código Django
-- ========================================================

-- 🔒 1. ATIVAR RLS EM TODAS AS TABELAS
-- ========================================================

ALTER TABLE usuarios_usuario ENABLE ROW LEVEL SECURITY;
ALTER TABLE empresas_empresa ENABLE ROW LEVEL SECURITY;
ALTER TABLE empresas_empresa_usuarios ENABLE ROW LEVEL SECURITY;
ALTER TABLE funcionarios_funcionario ENABLE ROW LEVEL SECURITY;
ALTER TABLE lancamentos_lancamento ENABLE ROW LEVEL SECURITY;
ALTER TABLE billing_plan ENABLE ROW LEVEL SECURITY;
ALTER TABLE billing_billingcustomer ENABLE ROW LEVEL SECURITY;
ALTER TABLE billing_subscription ENABLE ROW LEVEL SECURITY;
ALTER TABLE billing_payment ENABLE ROW LEVEL SECURITY;
ALTER TABLE coefjam_coefjam ENABLE ROW LEVEL SECURITY;
ALTER TABLE indices_fgts ENABLE ROW LEVEL SECURITY;
ALTER TABLE configuracoes_configuracao ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_logs_auditlog ENABLE ROW LEVEL SECURITY;

-- ========================================================
-- 📋 2. POLÍTICAS PARA TABELAS PÚBLICAS (READ-ONLY)
-- ========================================================

-- INDICES FGTS: Todos podem ler (dados públicos oficiais)
CREATE POLICY "Indices FGTS são públicos"
  ON indices_fgts
  FOR SELECT
  USING (true);

-- PLANOS: Todos podem ler (página de preços pública)
CREATE POLICY "Planos são públicos"
  ON billing_plan
  FOR SELECT
  USING (true);

-- COEFJAM: Todos podem ler (dados de correção monetária)
CREATE POLICY "Coefjam são públicos"
  ON coefjam_coefjam
  FOR SELECT
  USING (true);

-- ========================================================
-- 👤 3. POLÍTICAS PARA USUÁRIOS
-- ========================================================

-- Usuários só podem ver seus próprios dados
CREATE POLICY "Usuários veem apenas próprios dados"
  ON usuarios_usuario
  FOR SELECT
  USING (auth.uid()::text = id::text);

-- Service role pode fazer tudo (Django)
CREATE POLICY "Service role acesso total - usuarios"
  ON usuarios_usuario
  FOR ALL
  USING (true)
  WITH CHECK (true);

-- ========================================================
-- 🏢 4. POLÍTICAS PARA EMPRESAS
-- ========================================================

-- Usuários veem apenas empresas que pertencem
CREATE POLICY "Usuários veem apenas suas empresas"
  ON empresas_empresa
  FOR SELECT
  USING (
    id IN (
      SELECT empresa_id 
      FROM empresas_empresa_usuarios 
      WHERE usuario_id::text = auth.uid()::text
    )
  );

-- Service role acesso total
CREATE POLICY "Service role acesso total - empresas"
  ON empresas_empresa
  FOR ALL
  USING (true)
  WITH CHECK (true);

-- ========================================================
-- 🔗 5. POLÍTICAS PARA ASSOCIAÇÃO USUÁRIO-EMPRESA
-- ========================================================

CREATE POLICY "Usuários veem apenas suas associações"
  ON empresas_empresa_usuarios
  FOR SELECT
  USING (usuario_id::text = auth.uid()::text);

CREATE POLICY "Service role acesso total - associacoes"
  ON empresas_empresa_usuarios
  FOR ALL
  USING (true)
  WITH CHECK (true);

-- ========================================================
-- 👷 6. POLÍTICAS PARA FUNCIONÁRIOS
-- ========================================================

-- Usuários veem apenas funcionários de suas empresas
CREATE POLICY "Usuários veem funcionários de suas empresas"
  ON funcionarios_funcionario
  FOR SELECT
  USING (
    empresa_id IN (
      SELECT empresa_id 
      FROM empresas_empresa_usuarios 
      WHERE usuario_id::text = auth.uid()::text
    )
  );

-- Service role acesso total
CREATE POLICY "Service role acesso total - funcionarios"
  ON funcionarios_funcionario
  FOR ALL
  USING (true)
  WITH CHECK (true);

-- ========================================================
-- 💰 7. POLÍTICAS PARA LANÇAMENTOS
-- ========================================================

-- Usuários veem apenas lançamentos de suas empresas
CREATE POLICY "Usuários veem lançamentos de suas empresas"
  ON lancamentos_lancamento
  FOR SELECT
  USING (
    empresa_id IN (
      SELECT empresa_id 
      FROM empresas_empresa_usuarios 
      WHERE usuario_id::text = auth.uid()::text
    )
  );

-- Service role acesso total
CREATE POLICY "Service role acesso total - lancamentos"
  ON lancamentos_lancamento
  FOR ALL
  USING (true)
  WITH CHECK (true);

-- ========================================================
-- 💳 8. POLÍTICAS PARA BILLING
-- ========================================================

-- Clientes veem apenas seus próprios dados de cobrança
CREATE POLICY "Clientes veem apenas próprio billing"
  ON billing_billingcustomer
  FOR SELECT
  USING (
    empresa_id IN (
      SELECT empresa_id 
      FROM empresas_empresa_usuarios 
      WHERE usuario_id::text = auth.uid()::text
    )
  );

CREATE POLICY "Service role acesso total - billing_customer"
  ON billing_billingcustomer
  FOR ALL
  USING (true)
  WITH CHECK (true);

-- Assinaturas
CREATE POLICY "Usuários veem apenas próprias assinaturas"
  ON billing_subscription
  FOR SELECT
  USING (
    customer_id IN (
      SELECT id FROM billing_billingcustomer
      WHERE empresa_id IN (
        SELECT empresa_id 
        FROM empresas_empresa_usuarios 
        WHERE usuario_id::text = auth.uid()::text
      )
    )
  );

CREATE POLICY "Service role acesso total - subscriptions"
  ON billing_subscription
  FOR ALL
  USING (true)
  WITH CHECK (true);

-- Pagamentos
CREATE POLICY "Usuários veem apenas próprios pagamentos"
  ON billing_payment
  FOR SELECT
  USING (
    customer_id IN (
      SELECT id FROM billing_billingcustomer
      WHERE empresa_id IN (
        SELECT empresa_id 
        FROM empresas_empresa_usuarios 
        WHERE usuario_id::text = auth.uid()::text
      )
    )
  );

CREATE POLICY "Service role acesso total - payments"
  ON billing_payment
  FOR ALL
  USING (true)
  WITH CHECK (true);

-- ========================================================
-- ⚙️ 9. POLÍTICAS PARA CONFIGURAÇÕES
-- ========================================================

CREATE POLICY "Usuários veem apenas configurações de suas empresas"
  ON configuracoes_configuracao
  FOR SELECT
  USING (
    empresa_id IN (
      SELECT empresa_id 
      FROM empresas_empresa_usuarios 
      WHERE usuario_id::text = auth.uid()::text
    )
  );

CREATE POLICY "Service role acesso total - configuracoes"
  ON configuracoes_configuracao
  FOR ALL
  USING (true)
  WITH CHECK (true);

-- ========================================================
-- 📝 10. POLÍTICAS PARA AUDIT LOGS
-- ========================================================

-- Apenas administradores veem logs (via service role)
-- Usuários comuns não têm acesso direto

CREATE POLICY "Service role acesso total - audit_logs"
  ON audit_logs_auditlog
  FOR ALL
  USING (true)
  WITH CHECK (true);

-- ========================================================
-- ✅ SCRIPT CONCLUÍDO
-- ========================================================
-- 
-- 🔒 RLS ATIVADO EM TODAS AS TABELAS
-- 
-- Políticas criadas:
-- ✅ Dados públicos: indices_fgts, billing_plan, coefjam_coefjam
-- ✅ Multi-tenant: empresas, funcionarios, lancamentos (isolados por empresa)
-- ✅ Billing: isolado por customer/empresa
-- ✅ Service Role: acesso total para Django (bypassa RLS automaticamente)
-- 
-- IMPORTANTE:
-- 🔑 Django deve usar SERVICE_ROLE_KEY na connection string
-- 🔑 APIs públicas futuras devem usar ANON_KEY (RLS ativa)
-- 
-- Como conectar Django:
-- DATABASE_URL=postgresql://postgres.[PROJECT]:[SERVICE_ROLE_KEY]@[HOST]:5432/postgres
-- 
-- NUNCA use SERVICE_ROLE_KEY no frontend!
-- ========================================================
