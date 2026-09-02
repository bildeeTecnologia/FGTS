-- Resetar sequences para todas as tabelas que existem
SELECT setval('audit_logs_auditlog_id_seq', COALESCE((SELECT MAX(id) FROM audit_logs_auditlog), 0) + 1);
SELECT setval('usuarios_usuario_id_seq', COALESCE((SELECT MAX(id) FROM usuarios_usuario), 0) + 1);
SELECT setval('empresas_empresa_id_seq', COALESCE((SELECT MAX(id) FROM empresas_empresa), 0) + 1);
SELECT setval('funcionarios_funcionario_id_seq', COALESCE((SELECT MAX(id) FROM funcionarios_funcionario), 0) + 1);
SELECT setval('lancamentos_lancamento_id_seq', COALESCE((SELECT MAX(id) FROM lancamentos_lancamento), 0) + 1);
SELECT setval('indices_indice_id_seq', COALESCE((SELECT MAX(id) FROM indices_indice), 0) + 1);
SELECT setval('billing_pricingplan_id_seq', COALESCE((SELECT MAX(id) FROM billing_pricingplan), 0) + 1);
