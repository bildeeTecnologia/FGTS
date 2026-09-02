-- Adicionar colunas faltantes nas tabelas do Supabase
-- Execute cada bloco no SQL Editor

-- usuarios_usuario
ALTER TABLE usuarios_usuario ADD COLUMN IF NOT EXISTS manutencao BOOLEAN DEFAULT FALSE;
ALTER TABLE usuarios_usuario ADD COLUMN IF NOT EXISTS is_multi_empresa BOOLEAN DEFAULT FALSE;

-- empresas_empresa (ajustar campos existentes + novos)
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

-- funcionarios_funcionario
ALTER TABLE funcionarios_funcionario ADD COLUMN IF NOT EXISTS pis VARCHAR(15);
ALTER TABLE funcionarios_funcionario ADD COLUMN IF NOT EXISTS data_demissao DATE;
ALTER TABLE funcionarios_funcionario ADD COLUMN IF NOT EXISTS carteira_profissional VARCHAR(20);
ALTER TABLE funcionarios_funcionario ADD COLUMN IF NOT EXISTS cbo VARCHAR(10);
ALTER TABLE funcionarios_funcionario ADD COLUMN IF NOT EXISTS matricula VARCHAR(20);

-- lancamentos_lancamento
ALTER TABLE lancamentos_lancamento ADD COLUMN IF NOT EXISTS base_fgts DECIMAL(15,2);

-- indices_indice
ALTER TABLE indices_indice ADD COLUMN IF NOT EXISTS data_indice DATE;

-- audit_logs_auditlog
ALTER TABLE audit_logs_auditlog ADD COLUMN IF NOT EXISTS action VARCHAR(50);
