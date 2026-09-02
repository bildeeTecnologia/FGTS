-- Adicionar coluna faltante
ALTER TABLE audit_logs_auditlog ADD COLUMN IF NOT EXISTS error_message TEXT;

-- Remover constraints de FK temporariamente para importar tudo
ALTER TABLE lancamentos_lancamento DROP CONSTRAINT IF EXISTS fk_lancamento_funcionario;
