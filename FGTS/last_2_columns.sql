-- Adicionar as últimas 2 colunas

-- lancamentos_lancamento  
ALTER TABLE lancamentos_lancamento ADD COLUMN IF NOT EXISTS valor_pago DECIMAL(15,2);

-- audit_logs_auditlog
ALTER TABLE audit_logs_auditlog ADD COLUMN IF NOT EXISTS description TEXT;
