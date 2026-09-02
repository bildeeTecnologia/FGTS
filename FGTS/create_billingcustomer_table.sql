-- Criar tabela billing_plan primeiro
CREATE TABLE IF NOT EXISTS billing_plan (
    id BIGSERIAL PRIMARY KEY,
    plan_type VARCHAR(20) NOT NULL UNIQUE,
    max_employees INTEGER,
    has_advanced_dashboard BOOLEAN DEFAULT FALSE,
    has_custom_reports BOOLEAN DEFAULT FALSE,
    has_pdf_export BOOLEAN DEFAULT FALSE,
    has_api BOOLEAN DEFAULT FALSE,
    support_level VARCHAR(20) DEFAULT 'EMAIL',
    price_monthly NUMERIC(10, 2) DEFAULT 0.00,
    price_yearly NUMERIC(10, 2) DEFAULT 0.00,
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Criar índices para billing_plan
CREATE INDEX IF NOT EXISTS idx_billing_plan_active ON billing_plan(active);
CREATE INDEX IF NOT EXISTS idx_billing_plan_plan_type ON billing_plan(plan_type);

-- Inserir planos padrão
INSERT INTO billing_plan (plan_type, max_employees, has_advanced_dashboard, has_custom_reports, has_pdf_export, has_api, support_level, price_monthly, price_yearly, active)
VALUES 
    ('BASIC', 50, FALSE, FALSE, FALSE, FALSE, 'EMAIL', 99.00, 990.00, TRUE),
    ('PROFESSIONAL', 200, TRUE, TRUE, TRUE, FALSE, 'PRIORITY', 199.00, 1990.00, TRUE),
    ('ENTERPRISE', NULL, TRUE, TRUE, TRUE, TRUE, '24_7', 399.00, 3990.00, TRUE)
ON CONFLICT (plan_type) DO NOTHING;

-- Criar tabela billing_billingcustomer
CREATE TABLE IF NOT EXISTS billing_billingcustomer (
    id BIGSERIAL PRIMARY KEY,
    empresa_id BIGINT NOT NULL UNIQUE REFERENCES empresas_empresa(id) ON DELETE CASCADE,
    plan_id BIGINT REFERENCES billing_plan(id) ON DELETE SET NULL,
    active_employees INTEGER DEFAULT 0,
    email_cobranca VARCHAR(254),
    asaas_customer_id VARCHAR(100),
    status VARCHAR(20) DEFAULT 'pending',
    trial_active BOOLEAN DEFAULT TRUE,
    trial_expires DATE,
    trial_used BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Criar índices
CREATE INDEX IF NOT EXISTS idx_billing_billingcustomer_empresa_id ON billing_billingcustomer(empresa_id);
CREATE INDEX IF NOT EXISTS idx_billing_billingcustomer_plan_id ON billing_billingcustomer(plan_id);
CREATE INDEX IF NOT EXISTS idx_billing_billingcustomer_status ON billing_billingcustomer(status);
