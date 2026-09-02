# 💳 ESTRUTURA DO BANCO DE DADOS - BILLING & ASSINATURAS

## 📊 Diagrama de Relacionamentos

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         ESTRUTURA COMPLETA                              │
└─────────────────────────────────────────────────────────────────────────┘

         ┌──────────────┐
         │   EMPRESA    │ ← Modelo base (empresas.models.Empresa)
         └──────┬───────┘
                │
                │ OneToOne
                ↓
      ┌─────────────────────┐
      │  BILLING_CUSTOMER   │ ← Cliente de faturamento
      │  ─────────────────  │
      │  • empresa (FK)     │
      │  • plan (FK)        │ ←──────┐
      │  • active_employees │        │
      │  • email_cobranca   │        │ FK
      │  • asaas_customer_id│        │
      │  • status           │        │
      └─────────┬───────────┘        │
                │                    │
                │ FK (1:N)           │
                ↓                    │
      ┌─────────────────────┐        │      ┌─────────────────────┐
      │   SUBSCRIPTION      │        └──────│       PLAN          │
      │  ─────────────────  │               │  ─────────────────  │
      │  • customer (FK)    │               │  • plan_type        │
      │  • asaas_sub_id     │               │  • max_employees    │
      │  • plan_name        │               │  • has_*_features   │
      │  • amount           │               │  • support_level    │
      │  • periodicity      │               │  • price_monthly    │
      │  • status           │               │  • price_yearly     │
      │  • next_due_date    │               └─────────────────────┘
      └─────────┬───────────┘
                │
                │ FK (1:N)
                ↓
      ┌─────────────────────┐
      │     PAYMENT         │ ← Pagamentos individuais
      │  ─────────────────  │
      │  • subscription(FK) │
      │  • asaas_payment_id │
      │  • amount           │
      │  • due_date         │
      │  • pay_date         │
      │  • status           │
      │  • invoice_url      │
      └─────────────────────┘


      ┌─────────────────────┐
      │   PRICING_PLAN      │ ← Modelo legado (compatibilidade)
      │  ─────────────────  │
      │  • name             │
      │  • description      │
      │  • amount           │
      │  • periodicity      │
      │  • active           │
      │  • sort_order       │
      └─────────────────────┘
```

---

## 📋 TABELA 1: `billing_plan`

**Função:** Define os 3 tipos de planos disponíveis (BASIC, PROFESSIONAL, ENTERPRISE)

| Campo | Tipo | Descrição | Valores |
|-------|------|-----------|---------|
| `id` | INTEGER | Primary Key | Auto increment |
| `plan_type` | VARCHAR(20) | Tipo do plano | 'BASIC', 'PROFESSIONAL', 'ENTERPRISE' |
| `max_employees` | INTEGER | Limite de colaboradores | 50, 200, NULL (ilimitado) |
| `has_advanced_dashboard` | BOOLEAN | Dashboard avançado | True/False |
| `has_custom_reports` | BOOLEAN | Relatórios personalizados | True/False |
| `has_pdf_export` | BOOLEAN | Exportar PDF/Excel | True/False |
| `has_api` | BOOLEAN | Acesso API | True/False |
| `support_level` | VARCHAR(20) | Nível de suporte | 'EMAIL', 'PRIORITY', '24_7' |
| `price_monthly` | DECIMAL(10,2) | Preço mensal | 99.00, 199.00, 399.00 |
| `price_yearly` | DECIMAL(10,2) | Preço anual | 990.00, 1990.00, 3990.00 |
| `active` | BOOLEAN | Plano ativo? | True/False |
| `created_at` | DATETIME | Data de criação | Auto |
| `updated_at` | DATETIME | Última atualização | Auto |

**Registros Atuais:**
```sql
SELECT * FROM billing_plan;

-- Resultado:
id | plan_type     | max_employees | price_monthly | support_level
1  | BASIC         | 50            | 99.00         | EMAIL
2  | PROFESSIONAL  | 200           | 199.00        | PRIORITY
3  | ENTERPRISE    | NULL          | 399.00        | 24_7
```

---

## 📋 TABELA 2: `billing_billingcustomer`

**Função:** Cliente de faturamento - relaciona Empresa com Plano escolhido

| Campo | Tipo | Descrição | Valores |
|-------|------|-----------|---------|
| `id` | INTEGER | Primary Key | Auto increment |
| `empresa_id` | INTEGER | FK → Empresa (OneToOne) | UNIQUE |
| `plan_id` | INTEGER | FK → Plan | NULL permitido |
| `active_employees` | INTEGER | Contador de colaboradores ativos | Default: 0 |
| `email_cobranca` | VARCHAR(254) | E-mail para cobrança | NULL permitido |
| `asaas_customer_id` | VARCHAR(100) | ID no sistema Asaas | NULL até criação |
| `status` | VARCHAR(20) | Status da conta | 'active', 'inactive', 'pending', 'canceled' |
| `created_at` | DATETIME | Data de criação | Auto |
| `updated_at` | DATETIME | Última atualização | Auto |

**Relacionamento:**
- `empresa_id` → `empresas.Empresa` (OneToOne)
- `plan_id` → `billing_plan.id` (ForeignKey)

**Métodos úteis:**
- `can_add_employee()` - Verifica se pode adicionar mais um colaborador
- `get_usage_percentage()` - Retorna % de uso do plano
- `get_employees_remaining()` - Quantos colaboradores restam

---

## 📋 TABELA 3: `billing_subscription`

**Função:** Assinaturas recorrentes vinculadas ao gateway de pagamento (Asaas)

| Campo | Tipo | Descrição | Valores |
|-------|------|-----------|---------|
| `id` | INTEGER | Primary Key | Auto increment |
| `customer_id` | INTEGER | FK → BillingCustomer | NOT NULL |
| `asaas_subscription_id` | VARCHAR(100) | ID da assinatura no Asaas | NULL até criação |
| `plan_name` | VARCHAR(120) | Nome do plano | 'Plano FGTS Web' |
| `amount` | DECIMAL(10,2) | Valor da assinatura | Ex: 199.00 |
| `periodicity` | VARCHAR(10) | Periodicidade | 'MONTHLY', 'YEARLY' |
| `status` | VARCHAR(20) | Status da assinatura | 'active', 'pending', 'overdue', 'canceled', 'suspended' |
| `next_due_date` | DATE | Próxima data de vencimento | NULL permitido |
| `created_at` | DATETIME | Data de criação | Auto |
| `updated_at` | DATETIME | Última atualização | Auto |

**Relacionamento:**
- `customer_id` → `billing_billingcustomer.id` (ForeignKey)

**Ciclo de Vida:**
```
pending → active → overdue → canceled
    ↓       ↓         ↓
    └───────┴─────────→ suspended
```

---

## 📋 TABELA 4: `billing_payment`

**Função:** Pagamentos individuais de cada mensalidade/anuidade

| Campo | Tipo | Descrição | Valores |
|-------|------|-----------|---------|
| `id` | INTEGER | Primary Key | Auto increment |
| `subscription_id` | INTEGER | FK → Subscription | NOT NULL |
| `asaas_payment_id` | VARCHAR(100) | ID do pagamento no Asaas | NULL até criação |
| `amount` | DECIMAL(10,2) | Valor do pagamento | Ex: 199.00 |
| `due_date` | DATE | Data de vencimento | NOT NULL |
| `pay_date` | DATE | Data do pagamento efetivo | NULL até pagar |
| `status` | VARCHAR(20) | Status do pagamento | 'pending', 'confirmed', 'overdue', 'canceled' |
| `invoice_url` | VARCHAR(200) | URL do boleto/fatura | NULL até geração |
| `created_at` | DATETIME | Data de criação | Auto |
| `updated_at` | DATETIME | Última atualização | Auto |

**Relacionamento:**
- `subscription_id` → `billing_subscription.id` (ForeignKey)

**Ciclo de Vida:**
```
pending → confirmed (pagamento recebido)
    ↓
  overdue (venceu e não foi pago)
    ↓
  canceled (cancelado manualmente)
```

---

## 📋 TABELA 5: `billing_pricingplan` (Legado)

**Função:** Modelo legado para compatibilidade com código anterior

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `id` | INTEGER | Primary Key |
| `name` | VARCHAR(120) | Nome do plano |
| `description` | VARCHAR(255) | Descrição |
| `amount` | DECIMAL(10,2) | Valor |
| `periodicity` | VARCHAR(10) | Periodicidade |
| `active` | BOOLEAN | Ativo? |
| `sort_order` | INTEGER | Ordem de exibição |
| `updated_at` | DATETIME | Última atualização |

**Status:** Mantido para retrocompatibilidade, mas **novo sistema usa `billing_plan`**

---

## 🔄 FLUXO DE DADOS (Criação de Assinatura)

### **1. Usuário Seleciona Plano na Landing**
```sql
-- Buscar plano selecionado
SELECT * FROM billing_plan WHERE plan_type = 'PROFESSIONAL';
```

### **2. Usuário Cria Conta + Empresa**
```sql
-- Sistema cria BillingCustomer vinculado
INSERT INTO billing_billingcustomer (
    empresa_id, 
    plan_id, 
    email_cobranca, 
    status
) VALUES (
    1, -- ID da empresa recém-criada
    2, -- ID do plano PROFESSIONAL
    'empresa@example.com',
    'pending'
);
```

### **3. Sistema Cria Assinatura no Asaas (via API)**
```python
# billing/views.py - checkout_empresa()
subscription_payload = {
    'customer': 'cus_123456',  # asaas_customer_id
    'value': 199.00,
    'cycle': 'MONTHLY',
    'billingType': 'BOLETO'
}
# Asaas retorna: sub_789012
```

```sql
-- Sistema registra no banco
INSERT INTO billing_subscription (
    customer_id,
    asaas_subscription_id,
    plan_name,
    amount,
    periodicity,
    status,
    next_due_date
) VALUES (
    1,
    'sub_789012',
    'Plano FGTS Web',
    199.00,
    'MONTHLY',
    'pending',
    '2026-01-03'
);
```

### **4. Sistema Cria Pagamento Inicial**
```sql
INSERT INTO billing_payment (
    subscription_id,
    asaas_payment_id,
    amount,
    due_date,
    status,
    invoice_url
) VALUES (
    1,
    'pay_345678',
    199.00,
    '2026-01-03',
    'pending',
    'https://asaas.com/boleto/pay_345678'
);
```

### **5. Webhook do Asaas Atualiza Status (quando paga)**
```python
# billing/views.py - asaas_webhook()
# Asaas envia: {"event": "PAYMENT_RECEIVED", "payment": {...}}
```

```sql
-- Sistema atualiza pagamento
UPDATE billing_payment 
SET status = 'confirmed', pay_date = '2026-01-02'
WHERE asaas_payment_id = 'pay_345678';

-- Atualiza assinatura
UPDATE billing_subscription
SET status = 'active'
WHERE id = 1;

-- Atualiza cliente
UPDATE billing_billingcustomer
SET status = 'active'
WHERE id = 1;
```

---

## 🎯 CONSULTAS ÚTEIS

### Verificar plano de uma empresa:
```sql
SELECT 
    e.nome AS empresa,
    p.plan_type AS plano,
    bc.active_employees AS colaboradores_ativos,
    p.max_employees AS limite,
    bc.status AS status_conta
FROM empresas_empresa e
INNER JOIN billing_billingcustomer bc ON e.id = bc.empresa_id
LEFT JOIN billing_plan p ON bc.plan_id = p.id;
```

### Ver assinaturas ativas:
```sql
SELECT 
    e.nome AS empresa,
    s.plan_name AS plano,
    s.amount AS valor,
    s.periodicity AS periodo,
    s.status AS status,
    s.next_due_date AS proximo_vencimento
FROM billing_subscription s
INNER JOIN billing_billingcustomer bc ON s.customer_id = bc.id
INNER JOIN empresas_empresa e ON bc.empresa_id = e.id
WHERE s.status = 'active';
```

### Histórico de pagamentos de uma empresa:
```sql
SELECT 
    e.nome AS empresa,
    p.amount AS valor,
    p.due_date AS vencimento,
    p.pay_date AS data_pagamento,
    p.status AS status,
    p.invoice_url AS boleto
FROM billing_payment p
INNER JOIN billing_subscription s ON p.subscription_id = s.id
INNER JOIN billing_billingcustomer bc ON s.customer_id = bc.id
INNER JOIN empresas_empresa e ON bc.empresa_id = e.id
WHERE e.id = 1
ORDER BY p.due_date DESC;
```

### Pagamentos em atraso:
```sql
SELECT 
    e.nome AS empresa,
    bc.email_cobranca AS email,
    p.amount AS valor,
    p.due_date AS vencimento,
    (CURRENT_DATE - p.due_date) AS dias_atraso
FROM billing_payment p
INNER JOIN billing_subscription s ON p.subscription_id = s.id
INNER JOIN billing_billingcustomer bc ON s.customer_id = bc.id
INNER JOIN empresas_empresa e ON bc.empresa_id = e.id
WHERE p.status = 'overdue'
ORDER BY dias_atraso DESC;
```

### Uso do plano (colaboradores):
```sql
SELECT 
    e.nome AS empresa,
    p.plan_type AS plano,
    bc.active_employees AS uso_atual,
    p.max_employees AS limite,
    CASE 
        WHEN p.max_employees IS NULL THEN 0
        ELSE ROUND((bc.active_employees::FLOAT / p.max_employees) * 100, 2)
    END AS percentual_uso
FROM billing_billingcustomer bc
INNER JOIN empresas_empresa e ON bc.empresa_id = e.id
LEFT JOIN billing_plan p ON bc.plan_id = p.id
WHERE bc.status = 'active';
```

---

## 🔐 ÍNDICES RECOMENDADOS

```sql
-- Otimizar buscas por empresa
CREATE INDEX idx_billingcustomer_empresa ON billing_billingcustomer(empresa_id);

-- Otimizar buscas por asaas_customer_id (webhooks)
CREATE INDEX idx_billingcustomer_asaas ON billing_billingcustomer(asaas_customer_id);

-- Otimizar buscas de assinaturas ativas
CREATE INDEX idx_subscription_status ON billing_subscription(status);

-- Otimizar buscas de pagamentos por status
CREATE INDEX idx_payment_status ON billing_payment(status);

-- Otimizar buscas de pagamentos por asaas_payment_id (webhooks)
CREATE INDEX idx_payment_asaas ON billing_payment(asaas_payment_id);

-- Otimizar buscas por data de vencimento
CREATE INDEX idx_payment_duedate ON billing_payment(due_date);
```

---

## 📊 RESUMO DA ESTRUTURA

| Tabela | Registros | Função |
|--------|-----------|--------|
| `billing_plan` | 3 fixos | Catálogo de planos disponíveis |
| `billing_billingcustomer` | 1 por empresa | Cliente de faturamento |
| `billing_subscription` | 1+ por cliente | Assinatura recorrente |
| `billing_payment` | N por subscription | Histórico de pagamentos |
| `billing_pricingplan` | Legado | Compatibilidade |

---

## 🎯 ESTADOS DO SISTEMA

### BillingCustomer.status:
- `pending` - Aguardando primeiro pagamento
- `active` - Cliente ativo com pagamento confirmado
- `inactive` - Cliente inativo (não renovado)
- `canceled` - Cliente cancelou serviço

### Subscription.status:
- `pending` - Aguardando ativação
- `active` - Assinatura ativa
- `overdue` - Pagamento em atraso
- `canceled` - Cancelada
- `suspended` - Suspensa temporariamente

### Payment.status:
- `pending` - Aguardando pagamento
- `confirmed` - Pago e confirmado
- `overdue` - Vencido
- `canceled` - Cancelado

---

**Estrutura completa e pronta para gerenciar assinaturas recorrentes com integração Asaas!** 🎉
