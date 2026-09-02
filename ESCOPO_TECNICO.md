# Documento de Escopo Técnico — FGTS Web
> Gerado em: Março/2026
> Finalidade: Levantamento técnico para fins de cotação de desenvolvimento
> Este documento descreve o sistema existente em sua totalidade, servindo como base para que desenvolvedores, agências ou profissionais freelancers possam estimar esforço e custo de reconstrução.

---

## 1. Visão Geral do Sistema

Sistema SaaS (Software as a Service) web voltado para gestão de FGTS empresarial. Permite que empresas e escritórios contábeis (BPOs) calculem, registrem, importem e exportem lançamentos de FGTS de seus funcionários, com correção monetária, geração de SEFIP, relatórios e faturamento recorrente integrado.

### Público-alvo
- Empresas com funcionários registrados (CLT) que precisam controlar o FGTS
- Escritórios de contabilidade e BPOs que gerenciam múltiplos CNPJs

### Domínio de produção
- `https://fgts.bildee.com.br`

---

## 2. Stack Tecnológica

| Camada | Tecnologia |
|---|---|
| Linguagem | Python |
| Framework backend | Django 6.0 |
| Banco de dados (produção) | PostgreSQL via Supabase |
| Banco de dados (desenvolvimento) | SQLite |
| ORM | Django ORM (padrão) |
| Frontend | Bootstrap 5.3 + Django Templates |
| Ícones | Bootstrap Icons 1.10 |
| Arquivos estáticos | WhiteNoise (CompressedManifestStaticFilesStorage) |
| E-mail (SMTP) | Brevo / Sendinblue (smtp-relay.brevo.com:587 TLS) |
| Gateway de pagamento | Asaas (API REST v3) |
| Background jobs | APScheduler (django-apscheduler) |
| Geração de PDF | ReportLab |
| Manipulação de XLSX | openpyxl |
| Deploy | Coolify + Dockerfile |
| SEO | robots.txt, sitemap.xml, JSON-LD, Open Graph |

---

## 3. Infraestrutura e Deploy

- Containerizado via **Docker** com `Dockerfile` próprio
- Orquestrado por **Coolify** (self-hosted PaaS)
- Banco de dados: **PostgreSQL via Supabase** com SSL obrigatório (porta 6543, pooler)
- Variáveis de ambiente para todas as credenciais (nunca hard-coded)
- Logging em arquivo (`logs/django.log`) com nível configurável por env var
- Sessão expira em 15 minutos (`SESSION_COOKIE_AGE = 900`)
- Segurança de produção: HSTS (1 ano + preload), SSL redirect, secure cookies, `X-Content-Type-Options`

---

## 4. Arquitetura Geral

```
fgtsweb/          ← configurações principais (settings, urls, views globais, mixins)
empresas/         ← empresas, grupos econômicos, vínculos, calculadora pública, leads
funcionarios/     ← cadastro de funcionários
lancamentos/      ← lançamentos FGTS, importação, relatórios, SEFIP, conferência
indices/          ← índices de correção FGTS mensais
coefjam/          ← coeficientes JAM (juros de atualização monetária)
billing/          ← planos, assinatura, gateway Asaas, módulo BPO
usuarios/         ← usuário customizado, autenticação, controle de acesso
audit_logs/       ← auditoria completa de ações
monitoring/       ← rastreamento de performance
emails/           ← serviço centralizado de e-mail
configuracoes/    ← chave-valor de configurações do sistema
```

---

## 5. Módulos e Funcionalidades

### 5.1 Autenticação e Usuários

- Modelo de usuário customizado (extende `AbstractUser` do Django)
- Registro com confirmação por e-mail (link tokenizado)
- Login/logout com sessão de 15 minutos
- Controle de acesso multi-empresa por usuário:
  - Empresa principal (FK)
  - Empresas adicionais (ManyToMany, modo multi-empresa)
  - Roles por empresa: `admin`, `gestor`, `operador`
- Expansão automática de acesso para todo o grupo econômico quando usuário é admin
- Usuário demo para onboarding (criado por management command, com empresa e dados fictícios pré-carregados)

**Complexidade:** Média-alta. O sistema de permissões é multi-camada (empresa principal → grupo econômico → empresas permitidas → role por empresa).

---

### 5.2 Empresas (CNPJs)

- Cadastro e edição de empresas com todos os dados fiscais (CNPJ, CNAE, FPAS, Outras Entidades, Simples Nacional, RAT)
- Auto-geração de código de folha único (`CF` + 8 hex chars)
- Preenchimento automático de endereço via API de CEP (na submissão do formulário)
- Grupos econômicos: agrupa múltiplas empresas sob uma empresa-mãe
- Feature flags por empresa (matriz de recursos habilitados: exportar, importar, criar, editar, excluir funcionários; gerar relatório; criar, editar, excluir lançamentos; exportar; gerar SEFIP)
- Painel de administração por empresa: gerenciamento de usuários e roles, toggle de colunas do relatório (Índice, Correção, JAM)
- Transferência de funcionários entre empresas do mesmo grupo

---

### 5.3 Funcionários

- Cadastro individual com: nome, CPF, PIS, CBO, carteira profissional, data de nascimento
- Modelo de vínculo (`FuncionarioVinculo`): um funcionário pode ter múltiplos vínculos (histórico por empresa)
  - Campos de vínculo: matrícula, cargo, salário, admissão, demissão, motivo de saída
  - Status automático (ativo / transferido / demitido) derivado dos campos
- Importação em lote via XLSX
- Download de template XLSX para importação
- Validação de limite de funcionários por plano (com mensagem de erro específica ao atingir o teto)
- Histórico de transferências entre empresas
- Listagem filtrada por nome, CPF, PIS, matrícula, empresa, status
- Paginação
- Exportação de IDs via API JSON (para cascata em outros formulários)

---

### 5.4 Lançamentos FGTS

Este é o módulo central do sistema.

**Criação e edição:**
- Registro de lançamento por competência (`MM/AAAA`) e funcionário/vínculo
- Suporte a 13º salário (1ª e 2ª parcela) com validação de mês correto
- Cálculo automático do valor FGTS (8% da base)
- Propagação automática de salário: ao alterar a base FGTS, todos os lançamentos posteriores do mesmo vínculo são atualizados em cascata via `bulk_update`
- Controle de pagamento: pago/não pago, data de pagamento, valor pago
- Validação do período histórico permitido pelo plano

**Importação em lote (XLSX):**
- Upload de planilha XLSX
- Tela de preview com amostra dos dados (OK vs erros)
- Opções de processamento: recalcular FGTS (forçar 8%) ou manter valor do arquivo; aplicar JAM com data de referência configurável
- Aceite de responsabilidade com registro imutável (texto dos termos, IP, user-agent, timestamp)
- Processamento assíncrono com acompanhamento em tempo real (polling AJAX com barra de progresso e timer)
- Resultado detalhado: criados, atualizados, erros

**Importação legada (CSV do VB6):**
- Importa empresas, funcionários ou lançamentos de CSV gerado por sistema legado em VB6
- Opção de pular duplicados

**Exclusão em massa:**
- Seleção múltipla com persistência entre páginas (sessionStorage)
- Seleção total via AJAX (busca todos os IDs que atendem ao filtro atual)
- Confirmação via modal antes da exclusão

**Filtros e listagem:**
- Filtros por competência, funcionário, matrícula, empresa, ano, status de pagamento, ordenação
- Persistência dos filtros na sessão

**Complexidade:** Alta. O módulo de lançamentos tem lógica de negócio sofisticada (cascata de salários, importação assíncrona, validação fiscal de 13º salário, JAM).

---

### 5.5 Relatórios

**Relatório por Competência:**
- Filtros: empresa, funcionário, matrícula, competência simples ou múltipla (textarea), agrupamento (competência / ano / funcionário / vínculo), data de pagamento
- Colunas condicionais controladas por empresa: Índice CEF, Correção Monetária, JAM
- Totais consolidados
- Exportação CSV (ponto-e-vírgula)
- Exportação PDF (ReportLab, multi-coluna)
- Memória de cálculo por lançamento (PDF individual)
- Overlay de loading durante geração

**Relatório de Recolhimento por Funcionário:**
- Filtros: empresa, funcionário, período (competência início/fim)
- Exportação PDF (ReportLab)
- Exportação XLSX (openpyxl com cabeçalho estilizado, bordas, cores)

---

### 5.6 SEFIP

- **Exportação SEFIP.RE:** gera o arquivo `.RE` no formato fixo de 360 caracteres/linha, codificação ISO-8859-1, seguindo as regras do SEFIP do FGTS. Filtros por empresa, competência e range de funcionários (de/até).
- **Importação SEFIP.RE:** lê arquivo `.RE`/`.TXT` (até 50 MB), analisa registros tipo 00/10/30, cria ou atualiza `Lancamento` no banco.

**Complexidade:** Alta. O formato SEFIP é um protocolo legado complexo de largura fixa com regras específicas do governo.

---

### 5.7 Conferência de Lançamentos

- Gate de pré-pagamento: cada lançamento pode ser marcado como conferido, com problema ou rejeitado
- Validações automáticas na conferência:
  - FGTS > 0
  - Base × 8% bate com valor declarado (margem R$1)
  - Competência válida
  - Data de pagamento após competência
  - Valor conferido difere do calculado em menos de 5%
- Registro de quem conferiu, quando e observações
- Relatório de conferência por empresa e competência (totais por status)
- Verificação se a competência pode ser consolidada (bloqueia se há rejeitados ou pendentes)

---

### 5.8 Índices e CoefJAM

**Índices FGTS:**
- Tabela de índices mensais de correção (TR)
- Importação por arquivo de texto (`import_indices`)
- Leitura da tabela gerenciada pelo Supabase (`indices_fgts`, modelo unmanaged)

**CoefJAM:**
- Tabela de coeficientes de Juros de Atualização Monetária
- Upload do arquivo `COEFJAM.TXT` (pipe-delimited ou ponto-e-vírgula)
- Dois management commands de importação (formatos distintos)

---

### 5.9 Calculadora FGTS Pública

- Página pública (sem login) para calcular FGTS com correção
- Inputs: base FGTS, competência, data de pagamento
- Retorna: valor FGTS + correção monetária
- Captura de lead: formulário de e-mail para receber "relatório premium"
- Armazena resultado completo em JSON no banco
- Dispara fluxo de e-mail de nutrição ao lead (4 etapas automáticas)
- SEO completo: meta tags, Open Graph, JSON-LD (WebApplication schema)

---

### 5.10 Billing e Planos

**Planos SaaS (3 tiers):**
- **Essencial**: limite de funcionários, meses de histórico, funcionalidades básicas
- **Profissional**: limites maiores, relatórios customizados, PDF, dashboard avançado
- **Enterprise**: sem limites, suporte 24/7, preço negociado por override
- Overrides individuais por empresa (preço, limite de funcionários, empresas, histórico)

**Trial:**
- Todo novo cadastro recebe trial de N dias (configurável por plano)
- Middleware bloqueia acesso e redireciona ao checkout quando trial expira
- Envio automático de e-mails de lifecycle: 3 dias antes, 1 dia antes, logo após expiração, aviso final

**Faturamento:**
- Integração com gateway Asaas (criação de customer, subscription, payment)
- Webhook Asaas recebido e processado (`/billing/webhook/`): atualiza status de pagamento
- Suporte a BOLETO, PIX, CARTÃO DE CRÉDITO
- Checkout com seleção de plano e forma de pagamento

**LGPD:**
- Management command `cleanup_expired_trials`: exclui todos os dados (funcionários, lançamentos, empresa, billing) de trials expirados há mais de N dias

---

### 5.11 Módulo BPO (Bureau de Processamento de Folha)

Modelo de negócio adicional para escritórios contábeis que gerenciam múltiplos CNPJs de clientes.

**Conceito:** O escritório paga por CNPJ ativo/mês. Ao adicionar um novo CNPJ no meio do ciclo, é cobrado um rateio proporcional (dias restantes ÷ dias do mês × preço).

**Funcionalidades:**
- Planos BPO (criados pelo admin): preço/CNPJ, limites, dias de trial
- Ativação de conta BPO via trial
- Checkout pós-trial: seleção de forma de pagamento, criação do customer Asaas
- Dashboard BPO: resumo financeiro (CNPJs ativos, preço, próxima fatura, próximo vencimento), tabela de empresas gerenciadas com ações
- Adicionar empresa cliente: cria a `Empresa`, `BillingCustomer` e `EmpresaBPO`, cobra rateio proporcional no Asaas (se não estiver em trial)
- Suspender empresa: zera cobrança, bloqueia acesso
- Reativar empresa: restaura cobrança e acesso
- Toggle de acesso: controla se o cliente pode fazer login na plataforma
- Cobrança mensal automatizada: management command `cobrar_bpo_mensal` (cron diário)
- Middleware de acesso: bloqueia login de empresa cliente se `permite_acesso_cliente = False` ou se a conta BPO estiver suspensa/cancelada
- Webhook Asaas estendido: trata pagamentos de `FaturaBPO` além dos regulares
- Guia de ajuda completa do módulo BPO

**Complexidade:** Alta. O módulo BPO é um subsistema de billing independente com lógica de rateio, controle de acesso por empresa e fluxo de pagamento distinto.

---

### 5.12 Auditoria

- Registro automático de todas ações POST/PUT/DELETE/PATCH de usuários autenticados
- Captura de login e logout via signals do Django
- Registro de erros 500 com traceback completo (truncado em 12.000 chars)
- Campos: usuário, timestamp, módulo, view, URL, ação, objeto (generic FK), valores antes/depois, IP, user-agent, HTTP method, status code
- Interface de listagem com filtros (tipo de ação, usuário, período)
- Acesso restrito a staff/superusuários

---

### 5.13 Monitoramento de Performance

- Tracking automático de 5 operações críticas (tempo > 1s):
  - Relatório por competência
  - Exportação CSV
  - Exportação PDF
  - Importação de funcionários
  - Importação de lançamentos
- Dashboard exclusivo para staff: KPIs (total, taxa de sucesso, tempo médio, operações lentas/muito lentas, erros), bottlenecks com barras de progresso, tabela por tipo, top 10 mais lentas

---

### 5.14 Configurações do Sistema

- Store de chave-valor para toggles de features do sistema
- Toggle via interface web: exibir/ocultar coluna de índice CEF, correção, JAM nos relatórios

---

### 5.15 E-mail Transacional e Marketing

**Transacionais:**
- Confirmação de cadastro (link tokenizado)
- Lifecycle do trial (4 e-mails)
- Resultados da calculadora FGTS (relatório premium)

**Marketing (lead nurturing):**
- Fluxo de 4 etapas para leads da calculadora pública
- APScheduler processa fila a cada 1 hora
- Estado de máquina: active / completed / paused / error
- Controle de erros com contador e retry

---

### 5.16 Páginas Públicas e SEO

**Páginas públicas:**
- Landing page (home)
- Calculadora FGTS
- Pricing (planos)
- Termos de Uso, Política de Privacidade, Política de Cookies, DPA (Acordo de Processamento de Dados)
- Centro de ajuda (manual, primeiros passos, FAQ, glossário, guia BPO)

**SEO:**
- `robots.txt` e `sitemap.xml` servidos dinamicamente via Django
- Meta tags completas (description, keywords, robots)
- Open Graph (título, descrição, URL, imagem)
- JSON-LD estruturado: WebSite, SoftwareApplication, Organization, WebApplication

---

## 6. Integrações Externas

### 6.1 Asaas (Gateway de Pagamento)

- **Tipo:** API REST v3 (HTTPS)
- **Ambientes:** Produção e Sandbox configuráveis por env var
- **Autenticação:** `access_token` no header
- **Retry automático:** 3 tentativas com backoff exponencial (1s, 2s) para erros 5xx e falhas de rede
- **Operações implementadas:**
  - Criar/consultar customer
  - Criar/consultar/cancelar subscription
  - Criar/consultar/cancelar payment
  - Listar payments de uma subscription
- **Webhook recebido:** endpoint próprio, trata eventos de pagamento regular e de BPO separadamente

### 6.2 Supabase (Banco de Dados)

- Conexão PostgreSQL direta via SSL
- Uma tabela gerenciada externamente pelo Supabase (`indices_fgts`) lida via modelo Django unmanaged

### 6.3 Brevo / Sendinblue (E-mail)

- SMTP autenticado com TLS
- Utilizado para todos os e-mails transacionais e de marketing

### 6.4 API de CEP (ViaCEP ou similar)

- Chamada no `clean()` do formulário de empresa para preencher automaticamente endereço (logradouro, bairro, cidade, UF)

---

## 7. Automação e Jobs

| Job | Gatilho | Finalidade |
|---|---|---|
| `send_lead_emails` | APScheduler — a cada 1 hora | Processa fila de e-mails de nutrição de leads |
| `cobrar_bpo_mensal` | Cron externo — diariamente | Gera cobranças Asaas para BPOs com vencimento no dia |
| `send_trial_emails` | Cron externo — 9h diariamente | E-mails lifecycle de trial (3d antes, 1d antes, expirado, aviso final) |
| `cleanup_expired_trials` | Cron externo — 2h diariamente | LGPD: purge de dados de trials expirados há > 30 dias |

---

## 8. Middleware Stack (Personalizado)

| Middleware | Função |
|---|---|
| `AuditLogsMiddleware` | Registra todas ações POST/PUT/DELETE/PATCH + erros 500 no banco |
| `TrialWarningMiddleware` | Redireciona ao checkout quando trial/BPO expira; bloqueia login de empresa suspensa |
| `PerformanceTrackingMiddleware` | Registra tempo de execução das 5 operações críticas (> 1s) |

---

## 9. Inventário de Modelos de Dados

| App | Modelo | Propósito |
|---|---|---|
| empresas | `Empresa` | Entidade central — CNPJ registrado |
| empresas | `GrupoEmpresa` | Agrupa empresas sob uma matriz |
| empresas | `FuncionarioVinculo` | Vínculo empregatício (funcionário × empresa) |
| empresas | `TransferenciaFuncionario` | Auditoria de transferências inter-empresas |
| empresas | `EmpresaFeature` | Flags de features por empresa (1:1) |
| empresas | `RelatorioPremium` | Relatórios gerados na calculadora pública |
| empresas | `EmailLog` | Log de envios de e-mail por relatório |
| empresas | `LeadEmailFlow` | Máquina de estados do fluxo de nutrição de leads |
| funcionarios | `Funcionario` | Dados pessoais do colaborador |
| lancamentos | `Lancamento` | Registro FGTS por competência/funcionário |
| lancamentos | `ImportacaoLancamento` | Job de importação em lote (XLSX) |
| lancamentos | `ImportacaoResponsabilidade` | Aceite imutável de termos para import |
| lancamentos | `ConferenciaLancamento` | Gate de conferência pré-pagamento (1:1 com Lancamento) |
| indices | `Indice` | Índices de correção FGTS |
| indices | `SupabaseIndice` | Proxy read-only para tabela gerenciada pelo Supabase |
| coefjam | `CoefJam` | Coeficientes JAM de atualização monetária |
| billing | `Plan` | Definição dos planos SaaS |
| billing | `BillingCustomer` | Perfil de billing por empresa (1:1) |
| billing | `PricingPlan` | Exibição pública de preços |
| billing | `Subscription` | Assinatura recorrente no Asaas |
| billing | `Payment` | Registro de cobrança individual |
| billing | `Feedback` | Feedbacks enviados pelos usuários |
| billing | `PlanoBPO` | Templates de planos para escritórios BPO |
| billing | `ContaBPO` | Conta do escritório BPO |
| billing | `EmpresaBPO` | Vínculo empresa cliente × conta BPO |
| billing | `FaturaBPO` | Faturas mensais geradas para BPOs |
| usuarios | `Usuario` | Usuário customizado (extende AbstractUser) |
| usuarios | `EmpresaUsuarioRole` | Role por empresa (admin/gestor/operador) |
| audit_logs | `AuditLog` | Registro completo de auditoria |
| monitoring | `PerformanceLog` | Métrica de performance por operação |
| configuracoes | `Configuracao` | Chave-valor para configurações do sistema |

**Total: 27 modelos de dados**

---

## 10. Inventário de Telas

| Categoria | Telas |
|---|---|
| Autenticação | Login, Registro, Confirmação de e-mail |
| Principal | Dashboard, Landing page pública |
| Empresas | Listar, Criar, Editar, Painel admin por empresa |
| Funcionários | Listar, Criar/Editar, Detalhe, Excluir, Transferir, Novo vínculo, Importar em lote |
| Lançamentos | Listar, Criar/Editar, Excluir, Importar (upload, preview, status) |
| Importação legada | Formulário, Resultado |
| Relatórios | Por competência (com export CSV/PDF), Recolhimento por funcionário (com export PDF/XLSX), Memória de cálculo |
| SEFIP | Exportar, Importar |
| Conferência | Listar, Detalhe, Conferir, Rejeitar, Relatório |
| Índices | Listar |
| CoefJAM | Listar, Importar |
| Configurações | Listar/editar toggles |
| Billing | Checkout de plano, Feedback |
| BPO | Planos, Checkout, Dashboard, Adicionar empresa |
| Auditoria | Listar logs |
| Monitoramento | Dashboard de performance |
| Calculadora | Calculadora FGTS pública |
| Ajuda | Index, Manual, Primeiros passos, FAQ, Glossário, Guia BPO |
| Legal | Termos, Privacidade, Cookies, DPA |

**Total: ~55 telas distintas**

---

## 11. Inventário de Endpoints (URLs)

| App | Endpoints |
|---|---|
| Raiz/Global | 8 (home, robots, sitemap, login, logout, dashboard, calculadora, ajuda e legais) |
| Billing | 16 (pricing, checkout, webhook, feedback, BPO: 9 rotas) |
| Empresas | 4 (listar, criar, editar, painel admin) |
| Funcionários | 11 (CRUD + detalhe + importar + template + json + vínculos + transferência) |
| Lançamentos | 24+ (CRUD + importação com 4 etapas + relatórios + exportações + SEFIP + conferência + legado) |
| Usuários | 2 (registrar, confirmar e-mail) |
| CoefJAM | 2 (listar, upload) |
| Auditoria | 1 |
| Monitoramento | 1 |

**Total: ~70 endpoints**

---

## 12. Complexidade das Funcionalidades

### Alta complexidade
- Propagação em cascata de salário entre lançamentos de competências posteriores
- Importação assíncrona de XLSX com tracking em tempo real (polling AJAX)
- Geração e parsing de SEFIP.RE (formato fixo legado do governo)
- Módulo BPO completo (rateio proporcional, controle de acesso por empresa, cobrança via Asaas)
- Cálculo de JAM e correção monetária com índices históricos
- Controle de acesso multi-camada (empresa → grupo → roles → BPO)
- Aceite de responsabilidade imutável com rastreabilidade jurídica

### Média complexidade
- Conferência de lançamentos com validações multi-critério
- Relatório financeiro com colunas condicionais e múltiplos agrupamentos
- Lifecycle de trial com envio automático de e-mails
- Fluxo de lead nurturing (máquina de estados + APScheduler)
- Exportações PDF (ReportLab) e XLSX (openpyxl) com formatação

### Baixa/Média complexidade
- CRUDs padrão (funcionários, empresas, lançamentos individuais)
- Auditoria automática via middleware
- Monitoramento de performance via middleware
- SEO e páginas públicas

---

## 13. Pontos de Atenção para Cotação

1. **Especificidade fiscal brasileira:** O sistema lida com regras específicas de FGTS, 13º salário, SEFIP, JAM e índices de correção. Requer conhecimento do domínio ou pesquisa adicional.

2. **Integração Asaas:** Requer conta e acesso à API. Há sandbox disponível para desenvolvimento/testes.

3. **Formato SEFIP.RE:** Documentação pública disponível na Caixa Econômica Federal. Implementação de encoder/decoder do formato é um subprojeto por si só.

4. **Processamento assíncrono:** A importação de lançamentos processa em background com APScheduler. Escalar isso para volumes maiores exigiria migração para Celery + Redis.

5. **Multi-tenancy:** O sistema isola dados por empresa em nível de aplicação (não por schema de banco). A função `get_allowed_empresa_ids()` é o ponto central desse controle.

6. **BPO como subsistema:** O módulo BPO tem seu próprio ciclo de billing, controle de acesso e gestão de clientes. É funcional como produto separado.

7. **LGPD:** Há implementação de purge automático de dados (management command) e registro imutável de aceite de termos.

---

*Documento gerado com base em análise estática completa do código-fonte do sistema.*
