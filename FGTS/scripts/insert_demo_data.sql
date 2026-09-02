-- ========================================================
-- Script SQL para inserir dados DEMO no Supabase
-- Data: 31/12/2025
-- Uso: Execute este script no Supabase SQL Editor
-- ========================================================

-- 1️⃣ INSERIR USUÁRIO DEMO
-- Senha: demo123456
INSERT INTO usuarios_usuario (
  username, email, first_name, last_name, password, 
  is_active, is_staff, is_superuser, date_joined, last_login
) VALUES (
  'demo', 
  'demo@fgtsweb.com', 
  'Cliente', 
  'Demo',
  'pbkdf2_sha256$1200000$ppeNyR56r84DcIjh9EZvFG$Hf8CcDtHIfvrMJ6wBheht0Gp8FUbOXXGRi77fLCxxJw=',
  true, 
  false, 
  false, 
  NOW(), 
  NULL
) ON CONFLICT (username) DO NOTHING;

-- Obter o ID do usuário demo
WITH demo_user AS (
  SELECT id FROM usuarios_usuario WHERE username = 'demo'
)

-- 2️⃣ INSERIR EMPRESA DEMO
INSERT INTO empresas_empresa (
  nome, cnpj, nome_contato, email, fone_contato, 
  cep, endereco, numero, bairro, cidade, uf
) 
SELECT
  'Empresa Demo LTDA',
  '12.345.678/0001-99',
  'João Silva',
  'contato@empresademo.com.br',
  '(11) 98765-4321',
  '01310-100',
  'Avenida Paulista',
  '1000',
  'Bela Vista',
  'São Paulo',
  'SP'
WHERE NOT EXISTS (
  SELECT 1 FROM empresas_empresa WHERE cnpj = '12.345.678/0001-99'
);

-- 3️⃣ ASSOCIAR USUÁRIO À EMPRESA (M2M)
INSERT INTO empresas_empresa_usuarios (empresa_id, usuario_id)
SELECT 
  (SELECT id FROM empresas_empresa WHERE cnpj = '12.345.678/0001-99'),
  (SELECT id FROM usuarios_usuario WHERE username = 'demo')
WHERE NOT EXISTS (
  SELECT 1 FROM empresas_empresa_usuarios 
  WHERE empresa_id = (SELECT id FROM empresas_empresa WHERE cnpj = '12.345.678/0001-99')
  AND usuario_id = (SELECT id FROM usuarios_usuario WHERE username = 'demo')
);

-- 4️⃣ ASSOCIAR PLANO À EMPRESA (BillingCustomer)
INSERT INTO billing_billingcustomer (
  empresa_id, plan_id, email_cobranca, asaas_customer_id, 
  status, active_employees, created_at, updated_at
)
SELECT
  (SELECT id FROM empresas_empresa WHERE cnpj = '12.345.678/0001-99'),
  (SELECT id FROM billing_plan WHERE plan_type = 'PROFESSIONAL' LIMIT 1),
  'contato@empresademo.com.br',
  'demo-customer-id',
  'active',
  0,
  NOW(),
  NOW()
WHERE NOT EXISTS (
  SELECT 1 FROM billing_billingcustomer 
  WHERE empresa_id = (SELECT id FROM empresas_empresa WHERE cnpj = '12.345.678/0001-99')
);

-- 5️⃣ INSERIR FUNCIONÁRIOS DEMO
INSERT INTO funcionarios_funcionario (
  empresa_id, nome, cpf, pis, data_admissao, 
  cbo, carteira_profissional, serie_carteira, 
  data_nascimento, data_demissao, observacao
)
SELECT
  (SELECT id FROM empresas_empresa WHERE cnpj = '12.345.678/0001-99'),
  nome, cpf, pis, '2022-01-15'::date,
  NULL, NULL, NULL, NULL, NULL, NULL
FROM (VALUES
  ('Maria Silva', '123.456.789-00', '10000078900'),
  ('Carlos Santos', '234.567.890-11', '10000089011'),
  ('Ana Oliveira', '345.678.901-22', '10000090122'),
  ('Pedro Costa', '456.789.012-33', '10000001233'),
  ('Fernanda Lima', '567.890.123-44', '10000012344')
) AS t(nome, cpf, pis)
WHERE NOT EXISTS (
  SELECT 1 FROM funcionarios_funcionario 
  WHERE empresa_id = (SELECT id FROM empresas_empresa WHERE cnpj = '12.345.678/0001-99')
  AND cpf = t.cpf
);

-- 6️⃣ INSERIR LANÇAMENTOS FGTS DEMO (últimos 6 meses)
-- Com salários e FGTS calculado corretamente (8%)
INSERT INTO lancamentos_lancamento (
  empresa_id, funcionario_id, competencia, data_lancamento,
  base_fgts, valor_fgts, data_pagto, pago
)
SELECT
  empresa.id,
  func.id,
  data.competencia,
  data.data_lancamento,
  data.base_fgts,
  data.base_fgts * 0.08,  -- FGTS = 8% do salário
  NULL,
  false
FROM (
  SELECT id FROM empresas_empresa WHERE cnpj = '12.345.678/0001-99'
) empresa
CROSS JOIN (
  SELECT id, nome FROM funcionarios_funcionario 
  WHERE empresa_id = (SELECT id FROM empresas_empresa WHERE cnpj = '12.345.678/0001-99')
) func
CROSS JOIN (
  -- Gerar últimos 6 meses de competências com salários
  VALUES
    ('12/2024', NOW() - INTERVAL '0 days', 3853.00::numeric),   -- Maria Silva
    ('11/2024', NOW() - INTERVAL '30 days', 3853.00::numeric),
    ('10/2024', NOW() - INTERVAL '60 days', 3853.00::numeric),
    ('09/2024', NOW() - INTERVAL '90 days', 3853.00::numeric),
    ('08/2024', NOW() - INTERVAL '120 days', 3853.00::numeric),
    ('07/2024', NOW() - INTERVAL '150 days', 3853.00::numeric)
) data(competencia, data_lancamento, base_fgts)
WHERE func.nome = 'Maria Silva'
AND NOT EXISTS (
  SELECT 1 FROM lancamentos_lancamento 
  WHERE empresa_id = empresa.id
  AND funcionario_id = func.id
  AND competencia = data.competencia
)

UNION ALL

SELECT
  empresa.id,
  func.id,
  data.competencia,
  data.data_lancamento,
  data.base_fgts,
  data.base_fgts * 0.08,
  NULL,
  false
FROM (
  SELECT id FROM empresas_empresa WHERE cnpj = '12.345.678/0001-99'
) empresa
CROSS JOIN (
  SELECT id, nome FROM funcionarios_funcionario 
  WHERE empresa_id = (SELECT id FROM empresas_empresa WHERE cnpj = '12.345.678/0001-99')
) func
CROSS JOIN (
  VALUES
    ('12/2024', NOW() - INTERVAL '0 days', 3099.00::numeric),   -- Carlos Santos
    ('11/2024', NOW() - INTERVAL '30 days', 3099.00::numeric),
    ('10/2024', NOW() - INTERVAL '60 days', 3099.00::numeric),
    ('09/2024', NOW() - INTERVAL '90 days', 3099.00::numeric),
    ('08/2024', NOW() - INTERVAL '120 days', 3099.00::numeric),
    ('07/2024', NOW() - INTERVAL '150 days', 3099.00::numeric)
) data(competencia, data_lancamento, base_fgts)
WHERE func.nome = 'Carlos Santos'
AND NOT EXISTS (
  SELECT 1 FROM lancamentos_lancamento 
  WHERE empresa_id = empresa.id
  AND funcionario_id = func.id
  AND competencia = data.competencia
)

UNION ALL

SELECT
  empresa.id,
  func.id,
  data.competencia,
  data.data_lancamento,
  data.base_fgts,
  data.base_fgts * 0.08,
  NULL,
  false
FROM (
  SELECT id FROM empresas_empresa WHERE cnpj = '12.345.678/0001-99'
) empresa
CROSS JOIN (
  SELECT id, nome FROM funcionarios_funcionario 
  WHERE empresa_id = (SELECT id FROM empresas_empresa WHERE cnpj = '12.345.678/0001-99')
) func
CROSS JOIN (
  VALUES
    ('12/2024', NOW() - INTERVAL '0 days', 4674.00::numeric),   -- Ana Oliveira
    ('11/2024', NOW() - INTERVAL '30 days', 4674.00::numeric),
    ('10/2024', NOW() - INTERVAL '60 days', 4674.00::numeric),
    ('09/2024', NOW() - INTERVAL '90 days', 4674.00::numeric),
    ('08/2024', NOW() - INTERVAL '120 days', 4674.00::numeric),
    ('07/2024', NOW() - INTERVAL '150 days', 4674.00::numeric)
) data(competencia, data_lancamento, base_fgts)
WHERE func.nome = 'Ana Oliveira'
AND NOT EXISTS (
  SELECT 1 FROM lancamentos_lancamento 
  WHERE empresa_id = empresa.id
  AND funcionario_id = func.id
  AND competencia = data.competencia
);

-- ========================================================
-- ✅ SCRIPT CONCLUÍDO
-- ========================================================
-- 
-- Credenciais Demo criadas:
-- Usuário: demo
-- Senha: demo123456
-- Email: demo@fgtsweb.com
-- 
-- Dados inseridos:
-- ✅ 1 Usuário demo
-- ✅ 1 Empresa demo (CNPJ: 12.345.678/0001-99)
-- ✅ 1 Associação usuário-empresa
-- ✅ 1 Plano Profissional atribuído
-- ✅ 5 Funcionários
-- ✅ 18 Lançamentos FGTS (6 meses × 3 funcionários)
--
-- O usuário pode fazer login imediatamente com:
-- URL: https://seu-dominio.com/login
-- Usuário: demo
-- Senha: demo123456
-- ========================================================
