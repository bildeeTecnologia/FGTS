-- Execute cada comando SEPARADAMENTE no SQL Editor do Supabase

-- 1. Empresas
CREATE TABLE empresas_empresa (id SERIAL PRIMARY KEY, razao_social VARCHAR(255) NOT NULL, nome_fantasia VARCHAR(255), cnpj VARCHAR(20) UNIQUE, ie VARCHAR(30), endereco VARCHAR(255), numero VARCHAR(10), complemento VARCHAR(255), bairro VARCHAR(100), cidade VARCHAR(100), estado VARCHAR(2), cep VARCHAR(9), telefone VARCHAR(20), email VARCHAR(254), responsavel VARCHAR(150), ativa BOOLEAN NOT NULL DEFAULT TRUE, criada_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP, atualizada_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP);

-- 2. Usuarios
CREATE TABLE usuarios_usuario (id SERIAL PRIMARY KEY, password VARCHAR(128) NOT NULL, last_login TIMESTAMP, is_superuser BOOLEAN NOT NULL DEFAULT FALSE, username VARCHAR(150) NOT NULL UNIQUE, first_name VARCHAR(150), last_name VARCHAR(150), email VARCHAR(254), is_staff BOOLEAN NOT NULL DEFAULT FALSE, is_active BOOLEAN NOT NULL DEFAULT TRUE, date_joined TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP, empresa_id INTEGER);

-- 3. Funcionarios
CREATE TABLE funcionarios_funcionario (id SERIAL PRIMARY KEY, empresa_id INTEGER NOT NULL, nome VARCHAR(255) NOT NULL, cpf VARCHAR(14) UNIQUE, data_nascimento DATE, genero VARCHAR(1), email VARCHAR(254), telefone VARCHAR(20), endereco VARCHAR(255), numero VARCHAR(10), complemento VARCHAR(255), bairro VARCHAR(100), cidade VARCHAR(100), estado VARCHAR(2), cep VARCHAR(9), data_admissao DATE, cargo VARCHAR(100), salario DECIMAL(15,2), ativo BOOLEAN NOT NULL DEFAULT TRUE, criado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP, atualizado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP, CONSTRAINT fk_funcionario_empresa FOREIGN KEY (empresa_id) REFERENCES empresas_empresa(id) ON DELETE CASCADE);

-- 4. Lancamentos
CREATE TABLE lancamentos_lancamento (id SERIAL PRIMARY KEY, empresa_id INTEGER NOT NULL, funcionario_id INTEGER NOT NULL, competencia VARCHAR(7), mes_referencia INTEGER, ano_referencia INTEGER, valor_fgts DECIMAL(15,2), valor_multa DECIMAL(15,2), pago BOOLEAN NOT NULL DEFAULT FALSE, data_pagamento DATE, criado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP, atualizado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP, CONSTRAINT fk_lancamento_empresa FOREIGN KEY (empresa_id) REFERENCES empresas_empresa(id) ON DELETE CASCADE, CONSTRAINT fk_lancamento_funcionario FOREIGN KEY (funcionario_id) REFERENCES funcionarios_funcionario(id) ON DELETE CASCADE);

-- 5. Indices
CREATE TABLE indices_indice (id SERIAL PRIMARY KEY, competencia VARCHAR(7), mes INTEGER, ano INTEGER, valor DECIMAL(15,6), criado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP, atualizado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP);

-- 6. Billing
CREATE TABLE billing_subscription (id SERIAL PRIMARY KEY, empresa_id INTEGER NOT NULL, plano VARCHAR(50), status VARCHAR(20), data_inicio DATE, data_fim DATE, valor_mensal DECIMAL(15,2), criada_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP, atualizada_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP, CONSTRAINT fk_subscription_empresa FOREIGN KEY (empresa_id) REFERENCES empresas_empresa(id) ON DELETE CASCADE);

-- 7. Audit Logs
CREATE TABLE audit_logs_auditlog (id SERIAL PRIMARY KEY, usuario_id INTEGER, acao VARCHAR(50), tabela VARCHAR(100), registro_id INTEGER, dados_antigos TEXT, dados_novos TEXT, endereco_ip VARCHAR(45), user_agent TEXT, criado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP, CONSTRAINT fk_auditlog_usuario FOREIGN KEY (usuario_id) REFERENCES usuarios_usuario(id) ON DELETE SET NULL);

-- 8. Indices (todos de uma vez)
CREATE INDEX idx_usuarios_empresa ON usuarios_usuario(empresa_id);
CREATE INDEX idx_usuarios_username ON usuarios_usuario(username);
CREATE INDEX idx_empresas_cnpj ON empresas_empresa(cnpj);
CREATE INDEX idx_empresas_ativa ON empresas_empresa(ativa);
CREATE INDEX idx_funcionarios_empresa ON funcionarios_funcionario(empresa_id);
CREATE INDEX idx_funcionarios_cpf ON funcionarios_funcionario(cpf);
CREATE INDEX idx_funcionarios_ativo ON funcionarios_funcionario(ativo);
CREATE INDEX idx_lancamentos_empresa ON lancamentos_lancamento(empresa_id);
CREATE INDEX idx_lancamentos_funcionario ON lancamentos_lancamento(funcionario_id);
CREATE INDEX idx_lancamentos_competencia ON lancamentos_lancamento(competencia);
CREATE INDEX idx_lancamentos_pago ON lancamentos_lancamento(pago);
CREATE INDEX idx_lancamentos_empresa_competencia ON lancamentos_lancamento(empresa_id, competencia);
CREATE INDEX idx_indices_competencia ON indices_indice(competencia);
CREATE INDEX idx_indices_mes_ano ON indices_indice(mes, ano);
CREATE INDEX idx_billing_empresa ON billing_subscription(empresa_id);
CREATE INDEX idx_billing_status ON billing_subscription(status);
CREATE INDEX idx_audit_usuario ON audit_logs_auditlog(usuario_id);
CREATE INDEX idx_audit_tabela ON audit_logs_auditlog(tabela);
CREATE INDEX idx_audit_criado_em ON audit_logs_auditlog(criado_em);
