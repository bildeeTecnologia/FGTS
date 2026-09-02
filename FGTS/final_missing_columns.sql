-- Adicionar últimas colunas faltantes

-- funcionarios_funcionario
ALTER TABLE funcionarios_funcionario ADD COLUMN IF NOT EXISTS serie_carteira VARCHAR(10);
ALTER TABLE funcionarios_funcionario ADD COLUMN IF NOT EXISTS numero_carteira VARCHAR(20);
ALTER TABLE funcionarios_funcionario ADD COLUMN IF NOT EXISTS uf_carteira VARCHAR(2);
ALTER TABLE funcionarios_funcionario ADD COLUMN IF NOT EXISTS pis_tipo VARCHAR(1);

-- lancamentos_lancamento  
ALTER TABLE lancamentos_lancamento ADD COLUMN IF NOT EXISTS pago_em DATE;
ALTER TABLE lancamentos_lancamento ADD COLUMN IF NOT EXISTS desconto_fgts DECIMAL(15,2);

-- audit_logs_auditlog (colunas django admin)
ALTER TABLE audit_logs_auditlog ADD COLUMN IF NOT EXISTS content_type_id INTEGER;
ALTER TABLE audit_logs_auditlog ADD COLUMN IF NOT EXISTS object_id INTEGER;
ALTER TABLE audit_logs_auditlog ADD COLUMN IF NOT EXISTS object_repr VARCHAR(200);
ALTER TABLE audit_logs_auditlog ADD COLUMN IF NOT EXISTS object_id_str VARCHAR(255);
