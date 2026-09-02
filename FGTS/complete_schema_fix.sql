-- SCRIPT COMPLETO: Adicionar TODAS as colunas faltantes no Supabase
-- Execute tudo de uma vez

-- ============================================================================
-- usuarios_usuario (já tem: id, password, last_login, is_superuser, username, first_name, last_name, email, is_staff, is_active, date_joined, empresa_id)
-- ============================================================================
ALTER TABLE usuarios_usuario ADD COLUMN IF NOT EXISTS manutencao BOOLEAN DEFAULT FALSE;
ALTER TABLE usuarios_usuario ADD COLUMN IF NOT EXISTS is_multi_empresa BOOLEAN DEFAULT FALSE;

-- ============================================================================
-- empresas_empresa (precisa remapear pois SQLite não tem razao_social, tem nome)
-- ============================================================================
ALTER TABLE empresas_empresa ADD COLUMN IF NOT EXISTS nome VARCHAR(255);
ALTER TABLE empresas_empresa ADD COLUMN IF NOT EXISTS cnae VARCHAR(10);
ALTER TABLE empresas_empresa ADD COLUMN IF NOT EXISTS codigo INTEGER;
ALTER TABLE empresas_empresa ADD COLUMN IF NOT EXISTS fone_contato VARCHAR(20);
ALTER TABLE empresas_empresa ADD COLUMN IF NOT EXISTS fpas VARCHAR(10);
ALTER TABLE empresas_empresa ADD COLUMN IF NOT EXISTS nome_contato VARCHAR(255);
ALTER TABLE empresas_empresa ADD COLUMN IF NOT EXISTS optante_simples INTEGER;
ALTER TABLE empresas_empresa ADD COLUMN IF NOT EXISTS outras_entidades VARCHAR(10);
ALTER TABLE empresas_empresa ADD COLUMN IF NOT EXISTS percentual_rat DECIMAL;
ALTER TABLE empresas_empresa ADD COLUMN IF NOT EXISTS uf VARCHAR(2);
ALTER TABLE empresas_empresa ALTER COLUMN razao_social DROP NOT NULL;

-- ============================================================================
-- funcionarios_funcionario
-- ============================================================================
ALTER TABLE funcionarios_funcionario ADD COLUMN IF NOT EXISTS pis VARCHAR(15);
ALTER TABLE funcionarios_funcionario ADD COLUMN IF NOT EXISTS data_demissao DATE;
ALTER TABLE funcionarios_funcionario ADD COLUMN IF NOT EXISTS carteira_profissional VARCHAR(20);
ALTER TABLE funcionarios_funcionario ADD COLUMN IF NOT EXISTS cbo VARCHAR(10);
ALTER TABLE funcionarios_funcionario ADD COLUMN IF NOT EXISTS matricula VARCHAR(20);
ALTER TABLE funcionarios_funcionario ADD COLUMN IF NOT EXISTS observacao TEXT;
ALTER TABLE funcionarios_funcionario ADD COLUMN IF NOT EXISTS serie_carteira VARCHAR(10);
ALTER TABLE funcionarios_funcionario ADD COLUMN IF NOT EXISTS numero_carteira VARCHAR(20);
ALTER TABLE funcionarios_funcionario ADD COLUMN IF NOT EXISTS uf_carteira VARCHAR(2);
ALTER TABLE funcionarios_funcionario ADD COLUMN IF NOT EXISTS pis_tipo VARCHAR(1);

-- ============================================================================
-- lancamentos_lancamento
-- ============================================================================
ALTER TABLE lancamentos_lancamento ADD COLUMN IF NOT EXISTS base_fgts DECIMAL(15,2);
ALTER TABLE lancamentos_lancamento ADD COLUMN IF NOT EXISTS data_pagto DATE;
ALTER TABLE lancamentos_lancamento ADD COLUMN IF NOT EXISTS valor_pago DECIMAL(15,2);
ALTER TABLE lancamentos_lancamento ADD COLUMN IF NOT EXISTS pago_em TIMESTAMP;
ALTER TABLE lancamentos_lancamento ADD COLUMN IF NOT EXISTS desconto_fgts DECIMAL(15,2);
ALTER TABLE lancamentos_lancamento ADD COLUMN IF NOT EXISTS valor_multa DECIMAL(15,2);
ALTER TABLE lancamentos_lancamento ALTER COLUMN valor_fgts DROP NOT NULL;
ALTER TABLE lancamentos_lancamento ALTER COLUMN data_pagamento DROP NOT NULL;

-- ============================================================================
-- indices_indice
-- ============================================================================
ALTER TABLE indices_indice ADD COLUMN IF NOT EXISTS data_indice DATE;
ALTER TABLE indices_indice ALTER COLUMN mes DROP NOT NULL;
ALTER TABLE indices_indice ALTER COLUMN ano DROP NOT NULL;

-- ============================================================================
-- billing_subscription (remapear colunas)
-- ============================================================================
ALTER TABLE billing_subscription ADD COLUMN IF NOT EXISTS asaas_subscription_id VARCHAR(100);
ALTER TABLE billing_subscription ADD COLUMN IF NOT EXISTS plan_name VARCHAR(120);
ALTER TABLE billing_subscription ADD COLUMN IF NOT EXISTS amount DECIMAL(15,2);
ALTER TABLE billing_subscription ADD COLUMN IF NOT EXISTS periodicity VARCHAR(10);
ALTER TABLE billing_subscription ADD COLUMN IF NOT EXISTS next_due_date DATE;
ALTER TABLE billing_subscription ADD COLUMN IF NOT EXISTS customer_id BIGINT;
ALTER TABLE billing_subscription ALTER COLUMN plano DROP NOT NULL;
ALTER TABLE billing_subscription ALTER COLUMN status DROP NOT NULL;

-- ============================================================================
-- audit_logs_auditlog
-- ============================================================================
ALTER TABLE audit_logs_auditlog ADD COLUMN IF NOT EXISTS timestamp TIMESTAMP;
ALTER TABLE audit_logs_auditlog ADD COLUMN IF NOT EXISTS module VARCHAR(20);
ALTER TABLE audit_logs_auditlog ADD COLUMN IF NOT EXISTS view_name VARCHAR(255);
ALTER TABLE audit_logs_auditlog ADD COLUMN IF NOT EXISTS url_path VARCHAR(500);
ALTER TABLE audit_logs_auditlog ADD COLUMN IF NOT EXISTS action VARCHAR(20);
ALTER TABLE audit_logs_auditlog ADD COLUMN IF NOT EXISTS object_id INTEGER;
ALTER TABLE audit_logs_auditlog ADD COLUMN IF NOT EXISTS object_repr VARCHAR(500);
ALTER TABLE audit_logs_auditlog ADD COLUMN IF NOT EXISTS description TEXT;
ALTER TABLE audit_logs_auditlog ADD COLUMN IF NOT EXISTS old_values TEXT;
ALTER TABLE audit_logs_auditlog ADD COLUMN IF NOT EXISTS new_values TEXT;
ALTER TABLE audit_logs_auditlog ADD COLUMN IF NOT EXISTS changes TEXT;
ALTER TABLE audit_logs_auditlog ADD COLUMN IF NOT EXISTS ip_address CHAR(39);
ALTER TABLE audit_logs_auditlog ADD COLUMN IF NOT EXISTS user_agent TEXT;
ALTER TABLE audit_logs_auditlog ADD COLUMN IF NOT EXISTS method VARCHAR(10);
ALTER TABLE audit_logs_auditlog ADD COLUMN IF NOT EXISTS status_code INTEGER;
ALTER TABLE audit_logs_auditlog ADD COLUMN IF NOT EXISTS error_message TEXT;
ALTER TABLE audit_logs_auditlog ADD COLUMN IF NOT EXISTS content_type_id INTEGER;
ALTER TABLE audit_logs_auditlog ADD COLUMN IF NOT EXISTS user_id BIGINT;
ALTER TABLE audit_logs_auditlog RENAME COLUMN usuario_id TO user_id_old;
ALTER TABLE audit_logs_auditlog ALTER COLUMN tabela DROP NOT NULL;
ALTER TABLE audit_logs_auditlog ALTER COLUMN registro_id DROP NOT NULL;

-- ============================================================================
-- Remover constraints de FK que causam problemas
-- ============================================================================
ALTER TABLE lancamentos_lancamento DROP CONSTRAINT IF EXISTS fk_lancamento_funcionario;
ALTER TABLE lancamentos_lancamento DROP CONSTRAINT IF EXISTS fk_lancamento_empresa;
ALTER TABLE funcionarios_funcionario DROP CONSTRAINT IF EXISTS fk_funcionario_empresa;
ALTER TABLE billing_subscription DROP CONSTRAINT IF EXISTS fk_subscription_empresa;
ALTER TABLE usuarios_usuario DROP CONSTRAINT IF EXISTS fk_usuarios_empresa;
