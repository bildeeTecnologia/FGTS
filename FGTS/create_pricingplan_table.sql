-- Criar tabela billing_pricingplan
CREATE TABLE IF NOT EXISTS billing_pricingplan (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(120) NOT NULL DEFAULT 'Plano FGTS Web',
    description VARCHAR(255) NOT NULL DEFAULT '',
    amount NUMERIC(10, 2) NOT NULL DEFAULT 0.00,
    periodicity VARCHAR(10) NOT NULL DEFAULT 'MONTHLY',
    active BOOLEAN NOT NULL DEFAULT TRUE,
    sort_order INTEGER NOT NULL DEFAULT 1,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Criar índice para otimizar queries de ordering
CREATE INDEX IF NOT EXISTS idx_pricingplan_active_sort ON billing_pricingplan(active DESC, sort_order ASC, updated_at DESC);

-- Inserir plano padrão
INSERT INTO billing_pricingplan (name, description, amount, periodicity, active, sort_order, updated_at)
VALUES ('Plano FGTS Web', 'Plano padrão do sistema FGTS Web', 99.90, 'MONTHLY', true, 1, CURRENT_TIMESTAMP)
ON CONFLICT DO NOTHING;
