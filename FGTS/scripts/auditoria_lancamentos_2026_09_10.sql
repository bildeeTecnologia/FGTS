-- ========================================================
-- Auditoria de Lançamentos FGTS por Empresa/Vínculo
-- Data: 10/09/2026
-- Script é SOMENTE LEITURA (só cria/derruba uma tabela TEMP, que existe
-- apenas durante esta sessão). Não altera nenhum dado de produção.
--
-- COMO EXECUTAR (IMPORTANTE):
-- O Supabase SQL Editor só exibe o resultado do ÚLTIMO comando quando você
-- roda o script inteiro de uma vez. Para ver cada seção, execute em duas
-- etapas:
--   1) Selecione (Ctrl+A) e rode o script INTEIRO uma vez — isso cria a
--      tabela temporária _auditoria_vinculo e a mantém na sessão.
--   2) Depois, selecione o texto de UMA seção por vez (do comentário
--      "SEÇÃO X" até o ";" da consulta) e rode só aquele trecho (Ctrl+Enter
--      com o cursor dentro do bloco selecionado). Repita para cada seção
--      que quiser ver.
-- A tabela temporária continua disponível na mesma aba/sessão até você
-- fechar a aba ou rodar o "DROP TABLE" do final. Não vai aparecer na lista
-- de tabelas do projeto (schema pg_temp, visível só nesta sessão).
-- ========================================================
--
-- REGRAS ADOTADAS (confirmadas com o usuário em 10/09/2026):
-- 1) Vínculo é considerado ativo numa competência C se:
--    mês(data_admissao) <= C E (data_demissao é nula OU mês(data_demissao) >= C)
--    (mesma regra já usada em LancamentoListView / is_ativo_em_competencia)
-- 2) Para vínculos ainda ativos, o corte de "esperado" é o mês ANTERIOR ao
--    atual (o mês corrente ainda não venceu).
-- 3) 13º esperado = 2 parcelas por ano em que o vínculo estava ativo no mês
--    da parcela (1ª: novembro, ou mês de aniversário se
--    empresa.paga_13_aniversario=true; 2ª: sempre dezembro).
-- 4) Se o vínculo foi encerrado ANTES do mês de uma parcela do 13º, essa
--    parcela NÃO é contada como esperada (13º rescisório é tratado fora do
--    módulo de lançamentos).
-- 5) Alíquota FGTS considerada: tipo_vinculo.percentual_fgts, ou 8% se o
--    vínculo não tiver tipo_vinculo definido (CLT padrão).
-- ========================================================

DROP TABLE IF EXISTS _auditoria_vinculo;

-- ========================================================
-- TABELA TEMPORÁRIA: métricas esperado x realizado por vínculo
-- ========================================================
CREATE TEMP TABLE _auditoria_vinculo AS
WITH vinculos_base AS (
  SELECT
    v.id AS vinculo_id,
    v.empresa_id,
    e.nome AS empresa_nome,
    v.funcionario_id,
    f.nome AS funcionario_nome,
    v.matricula,
    v.data_admissao,
    v.data_demissao,
    v.status,
    date_trunc('month', v.data_admissao)::date AS mes_admissao,
    CASE
      WHEN v.data_demissao IS NOT NULL THEN date_trunc('month', v.data_demissao)::date
      ELSE date_trunc('month', CURRENT_DATE - INTERVAL '1 month')::date
    END AS mes_cutoff,
    e.paga_13_aniversario,
    f.data_nascimento,
    COALESCE(tv.percentual_fgts, 8.00) / 100.0 AS aliquota
  FROM empresas_funcionariovinculo v
  JOIN empresas_empresa e ON e.id = v.empresa_id
  JOIN funcionarios_funcionario f ON f.id = v.funcionario_id
  LEFT JOIN empresas_tipovinculo tv ON tv.id = v.tipo_vinculo_id
),
esperado_normal AS (
  SELECT
    vinculo_id,
    GREATEST(
      0,
      (EXTRACT(YEAR FROM mes_cutoff)::int * 12 + EXTRACT(MONTH FROM mes_cutoff)::int)
      - (EXTRACT(YEAR FROM mes_admissao)::int * 12 + EXTRACT(MONTH FROM mes_admissao)::int)
      + 1
    ) AS qtd_normal_esperado
  FROM vinculos_base
),
anos_vinculo AS (
  SELECT vb.vinculo_id, gs.ano
  FROM vinculos_base vb,
  LATERAL generate_series(
    EXTRACT(YEAR FROM vb.mes_admissao)::int,
    EXTRACT(YEAR FROM vb.mes_cutoff)::int
  ) AS gs(ano)
),
esperado_13 AS (
  SELECT
    vb.vinculo_id,
    SUM(
      CASE WHEN make_date(
             av.ano,
             CASE WHEN vb.paga_13_aniversario AND vb.data_nascimento IS NOT NULL
                  THEN EXTRACT(MONTH FROM vb.data_nascimento)::int
                  ELSE 11 END,
             1
           ) BETWEEN vb.mes_admissao AND vb.mes_cutoff
      THEN 1 ELSE 0 END
      +
      CASE WHEN make_date(av.ano, 12, 1) BETWEEN vb.mes_admissao AND vb.mes_cutoff
      THEN 1 ELSE 0 END
    ) AS qtd_13_esperado
  FROM anos_vinculo av
  JOIN vinculos_base vb ON vb.vinculo_id = av.vinculo_id
  GROUP BY vb.vinculo_id
),
realizado AS (
  SELECT
    vinculo_id,
    COUNT(*) AS qtd_lancamentos,
    COUNT(*) FILTER (WHERE pago) AS qtd_pagos,
    COUNT(*) FILTER (WHERE NOT pago) AS qtd_nao_pagos,
    SUM(base_fgts) AS soma_base_fgts
  FROM lancamentos_lancamento
  WHERE vinculo_id IS NOT NULL
  GROUP BY vinculo_id
)
SELECT
  vb.empresa_id,
  vb.empresa_nome,
  vb.funcionario_id,
  vb.funcionario_nome,
  vb.matricula,
  vb.vinculo_id,
  vb.data_admissao,
  vb.data_demissao,
  vb.status,
  COALESCE(en.qtd_normal_esperado, 0) + COALESCE(e13.qtd_13_esperado, 0) AS qtd_lancamentos_esperados,
  COALESCE(r.qtd_lancamentos, 0) AS qtd_lancamentos_realizados,
  (COALESCE(en.qtd_normal_esperado, 0) + COALESCE(e13.qtd_13_esperado, 0)) - COALESCE(r.qtd_lancamentos, 0) AS diferenca,
  COALESCE(r.qtd_pagos, 0) AS qtd_pagos,
  COALESCE(r.qtd_nao_pagos, 0) AS qtd_nao_pagos,
  COALESCE(r.soma_base_fgts, 0) AS soma_base_fgts
FROM vinculos_base vb
LEFT JOIN esperado_normal en ON en.vinculo_id = vb.vinculo_id
LEFT JOIN esperado_13 e13 ON e13.vinculo_id = vb.vinculo_id
LEFT JOIN realizado r ON r.vinculo_id = vb.vinculo_id;

-- ========================================================
-- SEÇÃO 1: VÍNCULOS POR EMPRESA (visão consolidada)
-- ========================================================
SELECT
  empresa_nome AS empresa,
  COUNT(*) AS qtd_vinculos,
  SUM(qtd_lancamentos_realizados) AS total_lancamentos_realizados,
  SUM(qtd_lancamentos_esperados) AS total_lancamentos_esperados,
  SUM(diferenca) AS total_diferenca,
  SUM(soma_base_fgts) AS soma_base_fgts_total
FROM _auditoria_vinculo
GROUP BY empresa_nome
ORDER BY empresa_nome;

-- ========================================================
-- SEÇÃO 2: DETALHE POR VÍNCULO (esperado x realizado x base FGTS)
-- ========================================================
SELECT
  empresa_nome AS empresa,
  funcionario_nome AS funcionario,
  matricula,
  vinculo_id,
  data_admissao,
  data_demissao,
  status,
  qtd_lancamentos_esperados,
  qtd_lancamentos_realizados,
  diferenca,
  qtd_pagos,
  qtd_nao_pagos,
  soma_base_fgts
FROM _auditoria_vinculo
ORDER BY empresa_nome, funcionario_nome, data_admissao;

-- ========================================================
-- SEÇÃO 3: DIVERGÊNCIAS EM LANÇAMENTOS (pagos e não pagos)
-- ========================================================
WITH achados AS (
  SELECT l.id AS lancamento_id, l.empresa_id, l.vinculo_id, l.competencia,
    'PAGO_SEM_DATA_PAGAMENTO' AS tipo_divergencia,
    'Lançamento marcado como pago mas sem data_pagto preenchida' AS detalhe
  FROM lancamentos_lancamento l
  WHERE l.pago = true AND l.data_pagto IS NULL

  UNION ALL
  SELECT l.id, l.empresa_id, l.vinculo_id, l.competencia,
    'PAGO_SEM_VALOR_PAGO',
    'Lançamento marcado como pago mas sem valor_pago preenchido'
  FROM lancamentos_lancamento l
  WHERE l.pago = true AND l.valor_pago IS NULL

  UNION ALL
  SELECT l.id, l.empresa_id, l.vinculo_id, l.competencia,
    'PAGO_VALOR_PAGO_ZERADO_OU_NEGATIVO',
    'valor_pago <= 0 em lançamento marcado como pago'
  FROM lancamentos_lancamento l
  WHERE l.pago = true AND l.valor_pago IS NOT NULL AND l.valor_pago <= 0

  UNION ALL
  SELECT l.id, l.empresa_id, l.vinculo_id, l.competencia,
    'PAGO_DATA_ANTERIOR_A_COMPETENCIA',
    format('data_pagto (%s) é anterior ao início da competência (%s)', l.data_pagto, l.competencia)
  FROM lancamentos_lancamento l
  WHERE l.pago = true AND l.data_pagto IS NOT NULL
    AND l.competencia ~ '^\d{2}/\d{4}$'
    AND l.data_pagto < to_date(l.competencia, 'MM/YYYY')

  UNION ALL
  SELECT l.id, l.empresa_id, l.vinculo_id, l.competencia,
    'PAGO_VALOR_PAGO_DIVERGENTE_DO_CALCULADO',
    format('valor_pago (%s) difere de valor_fgts (%s) em mais de R$5 ou 20%%', l.valor_pago, l.valor_fgts)
  FROM lancamentos_lancamento l
  WHERE l.pago = true AND l.valor_pago IS NOT NULL AND l.valor_fgts IS NOT NULL
    AND ABS(l.valor_pago - l.valor_fgts) > GREATEST(5, l.valor_fgts * 0.20)

  UNION ALL
  SELECT l.id, l.empresa_id, l.vinculo_id, l.competencia,
    'NAO_PAGO_COM_DATA_OU_VALOR_PREENCHIDO',
    'Lançamento NÃO pago mas possui data_pagto e/ou valor_pago preenchidos (estado inconsistente)'
  FROM lancamentos_lancamento l
  WHERE l.pago = false AND (l.data_pagto IS NOT NULL OR l.valor_pago IS NOT NULL)

  UNION ALL
  SELECT l.id, l.empresa_id, l.vinculo_id, l.competencia,
    'BASE_FGTS_INVALIDA',
    'base_fgts é nula, zero ou negativa'
  FROM lancamentos_lancamento l
  WHERE l.base_fgts IS NULL OR l.base_fgts <= 0

  UNION ALL
  SELECT l.id, l.empresa_id, l.vinculo_id, l.competencia,
    'VALOR_FGTS_DIVERGENTE_DA_ALIQUOTA',
    format('valor_fgts (%s) não bate com base_fgts × alíquota esperada (%s)',
           l.valor_fgts, ROUND(l.base_fgts * COALESCE(tv.percentual_fgts, 8.00) / 100.0, 2))
  FROM lancamentos_lancamento l
  LEFT JOIN empresas_funcionariovinculo v ON v.id = l.vinculo_id
  LEFT JOIN empresas_tipovinculo tv ON tv.id = v.tipo_vinculo_id
  WHERE l.base_fgts IS NOT NULL AND l.valor_fgts IS NOT NULL
    AND ABS(l.valor_fgts - (l.base_fgts * COALESCE(tv.percentual_fgts, 8.00) / 100.0)) > 1.00
)
SELECT
  e.nome AS empresa,
  a.tipo_divergencia,
  a.lancamento_id,
  a.vinculo_id,
  a.competencia,
  a.detalhe
FROM achados a
JOIN empresas_empresa e ON e.id = a.empresa_id
ORDER BY e.nome, a.tipo_divergencia, a.competencia;

-- ========================================================
-- SEÇÃO 4: INTEGRIDADE REFERENCIAL (checks extras sugeridos)
-- ========================================================

-- 4a) Lançamento cujo vínculo não pertence à mesma empresa/funcionário do lançamento
SELECT
  e.nome AS empresa,
  l.id AS lancamento_id,
  l.vinculo_id,
  l.empresa_id AS lancamento_empresa_id,
  v.empresa_id AS vinculo_empresa_id,
  l.funcionario_id AS lancamento_funcionario_id,
  v.funcionario_id AS vinculo_funcionario_id
FROM lancamentos_lancamento l
JOIN empresas_funcionariovinculo v ON v.id = l.vinculo_id
JOIN empresas_empresa e ON e.id = l.empresa_id
WHERE l.empresa_id <> v.empresa_id OR l.funcionario_id <> v.funcionario_id
ORDER BY e.nome;

-- 4b) Vínculos sobrepostos do mesmo funcionário na mesma empresa
SELECT
  e.nome AS empresa,
  f.nome AS funcionario,
  v1.id AS vinculo_1, v1.data_admissao AS adm_1, v1.data_demissao AS dem_1,
  v2.id AS vinculo_2, v2.data_admissao AS adm_2, v2.data_demissao AS dem_2
FROM empresas_funcionariovinculo v1
JOIN empresas_funcionariovinculo v2
  ON v1.funcionario_id = v2.funcionario_id
  AND v1.empresa_id = v2.empresa_id
  AND v1.id < v2.id
JOIN empresas_empresa e ON e.id = v1.empresa_id
JOIN funcionarios_funcionario f ON f.id = v1.funcionario_id
WHERE v1.data_admissao <= COALESCE(v2.data_demissao, 'infinity'::date)
  AND v2.data_admissao <= COALESCE(v1.data_demissao, 'infinity'::date)
ORDER BY e.nome, f.nome;

-- 4c) Duplicidade de lançamento por vínculo + competência + parcela_13
-- (a regra de unicidade normalmente é garantida pelo Django `clean()`, mas
-- registros inseridos via import em massa podem ter contornado essa checagem)
SELECT
  e.nome AS empresa,
  l.vinculo_id,
  l.competencia,
  l.parcela_13,
  COUNT(*) AS qtd_duplicados,
  array_agg(l.id ORDER BY l.id) AS lancamento_ids
FROM lancamentos_lancamento l
JOIN empresas_empresa e ON e.id = l.empresa_id
WHERE l.vinculo_id IS NOT NULL
GROUP BY e.nome, l.vinculo_id, l.competencia, l.parcela_13
HAVING COUNT(*) > 1
ORDER BY e.nome;

-- ========================================================
-- SEÇÃO 5: LANÇAMENTOS SEM VÍNCULO (legado, fora do cálculo esperado x realizado)
-- ========================================================
SELECT
  e.nome AS empresa,
  l.id AS lancamento_id,
  f.nome AS funcionario,
  l.competencia,
  l.parcela_13,
  l.base_fgts,
  l.valor_fgts,
  l.pago
FROM lancamentos_lancamento l
JOIN empresas_empresa e ON e.id = l.empresa_id
JOIN funcionarios_funcionario f ON f.id = l.funcionario_id
WHERE l.vinculo_id IS NULL
ORDER BY e.nome, f.nome, l.competencia;

-- ========================================================
-- LIMPEZA (rode por último, só depois de conferir todas as seções acima)
-- ========================================================
-- DROP TABLE IF EXISTS _auditoria_vinculo;
