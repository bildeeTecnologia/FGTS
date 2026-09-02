-- Remover tabela se existir (para recriar limpo)
DROP TABLE IF EXISTS billing_pricingplan CASCADE;

-- Criar tabela billing_pricingplan conforme modelo Django
CREATE TABLE billing_pricingplan (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(120) NOT NULL DEFAULT 'Plano FGTS Web',
    description VARCHAR(255) DEFAULT '',
    amount NUMERIC(10, 2) DEFAULT 0.00,
    periodicity VARCHAR(10) DEFAULT 'MONTHLY',
    active BOOLEAN DEFAULT TRUE,
    sort_order INTEGER DEFAULT 1,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Criar índices
CREATE INDEX idx_billing_pricingplan_active_sort ON billing_pricingplan(active DESC, sort_order ASC, updated_at DESC);

-- Inserir plano padrão
INSERT INTO billing_pricingplan (name, description, amount, periodicity, active, sort_order, updated_at)
VALUES ('Plano FGTS Web', 'Plano padrão do sistema FGTS Web', 99.90, 'MONTHLY', true, 1, CURRENT_TIMESTAMP);
