-- Adicionar colunas faltantes restantes

-- funcionarios_funcionario
ALTER TABLE funcionarios_funcionario ADD COLUMN IF NOT EXISTS observacao TEXT;

-- lancamentos_lancamento  
ALTER TABLE lancamentos_lancamento ADD COLUMN IF NOT EXISTS data_pagto DATE;

-- audit_logs_auditlog
ALTER TABLE audit_logs_auditlog ADD COLUMN IF NOT EXISTS changes TEXT;

-- empresas_empresa: remover NOT NULL de razao_social
ALTER TABLE empresas_empresa ALTER COLUMN razao_social DROP NOT NULL;
