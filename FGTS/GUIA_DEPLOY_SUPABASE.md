# 🚀 Guia de Deploy - Supabase + Coolify

**Data:** 31/12/2025  
**Objetivo:** Migrar banco de dados completo para Supabase PostgreSQL

---

## 📋 Pré-requisitos

- ✅ Acesso ao painel do Supabase
- ✅ Acesso ao painel do Coolify
- ✅ Código atualizado no GitHub (último commit)
- ✅ Scripts SQL prontos:
  - `scripts/setup_rls_supabase.sql` (RLS)
  - `scripts/insert_demo_data.sql` (dados demo)

---

## 🔑 PASSO 1: Obter Credenciais do Supabase

### 1.1 Acessar Supabase Dashboard
1. Acesse https://supabase.com/dashboard
2. Selecione seu projeto FGTS
3. Vá em **Settings** → **Database**

### 1.2 Copiar Informações de Conexão
Na seção **Connection String**, você verá:

```
Host: db.XXXXXXXXXXXXX.supabase.co
Database name: postgres
Port: 5432
User: postgres
Password: [sua senha configurada]
```

### 1.3 Obter SERVICE ROLE KEY
1. Vá em **Settings** → **API**
2. Na seção **Project API keys**
3. Copie a chave **service_role** (não a anon key!)
   - ⚠️ **NUNCA exponha esta chave no frontend!**

---

## ⚙️ PASSO 2: Configurar Variáveis de Ambiente no Coolify

### 2.1 Acessar Coolify
1. Acesse seu painel do Coolify
2. Selecione o projeto FGTS-PYTHON
3. Vá em **Environment Variables**

### 2.2 Adicionar/Atualizar Variáveis

Configure as seguintes variáveis (clique em **+ Add** para cada):

```bash
# ========================================
# DATABASE - SUPABASE POSTGRESQL
# ========================================

SUPABASE_HOST=db.XXXXXXXXXXXXX.supabase.co
SUPABASE_DB=postgres
SUPABASE_USER=postgres.XXXXXXXXXXXXX
SUPABASE_PASSWORD=SUA_SENHA_AQUI
SUPABASE_PORT=5432

# ========================================
# DJANGO SETTINGS
# ========================================

DEBUG=False
SECRET_KEY=seu-secret-key-super-seguro-aqui-min-50-chars
DJANGO_ALLOWED_HOSTS=fgts.bildee.com.br,*.bildee.com.br

# ========================================
# ASAAS PAYMENT GATEWAY
# ========================================

ASAAS_API_KEY=sua-chave-asaas-aqui
ASAAS_WALLET_ID=seu-wallet-id-aqui

# ========================================
# SUPABASE API (para REST)
# ========================================

SUPABASE_URL=https://XXXXXXXXXXXXX.supabase.co
SUPABASE_KEY=sua-service-role-key-aqui
```

### 2.3 Salvar e Redeploy
1. Clique em **Save**
2. Coolify irá reiniciar o container automaticamente

---

## 🗄️ PASSO 3: Executar Migrações no Banco

### 3.1 Acessar Terminal do Coolify
1. No painel do Coolify, vá em **Terminal** ou **Execute Command**
2. Execute os comandos abaixo:

```bash
# Verificar conexão com banco
python manage.py dbshell

# Se conectou, saia (Ctrl+D) e continue

# Aplicar todas as migrações
python manage.py migrate

# Criar superusuário (opcional, para admin)
python manage.py createsuperuser
```

### 3.2 Verificar Tabelas Criadas
As tabelas devem ser criadas automaticamente:
- `usuarios_usuario`
- `empresas_empresa`
- `empresas_empresa_usuarios`
- `funcionarios_funcionario`
- `lancamentos_lancamento`
- `billing_plan`
- `billing_billingcustomer`
- `billing_subscription`
- `billing_payment`
- `indices_fgts`
- `coefjam_coefjam`
- `configuracoes_configuracao`
- `audit_logs_auditlog`

---

## 🔒 PASSO 4: Configurar RLS (Row Level Security)

### 4.1 Acessar Supabase SQL Editor
1. No Supabase Dashboard, vá em **SQL Editor**
2. Clique em **+ New Query**

### 4.2 Executar Script RLS
1. Abra o arquivo `scripts/setup_rls_supabase.sql`
2. Copie TODO o conteúdo
3. Cole no SQL Editor do Supabase
4. Clique em **Run** ou `Ctrl+Enter`

### 4.3 Verificar RLS Ativo
Execute esta query para confirmar:

```sql
SELECT schemaname, tablename, rowsecurity 
FROM pg_tables 
WHERE schemaname = 'public' 
AND rowsecurity = true;
```

Deve retornar todas as 13 tabelas com `rowsecurity = true`.

---

## 📦 PASSO 5: Criar Planos Padrão

### 5.1 Via Terminal Coolify
```bash
python manage.py shell < scripts/create_default_plans.py
```

### 5.2 Verificar Planos Criados
```bash
python manage.py shell -c "from billing.models import Plan; print(list(Plan.objects.values('plan_type', 'price')))"
```

Deve retornar:
```python
[
  {'plan_type': 'STARTER', 'price': Decimal('49.90')},
  {'plan_type': 'PROFESSIONAL', 'price': Decimal('99.90')},
  {'plan_type': 'ENTERPRISE', 'price': Decimal('199.90')}
]
```

---

## 👤 PASSO 6: Inserir Dados Demo

### 6.1 Acessar Supabase SQL Editor
1. Vá em **SQL Editor** → **+ New Query**

### 6.2 Executar Script Demo
1. Abra o arquivo `scripts/insert_demo_data.sql`
2. Copie TODO o conteúdo
3. Cole no SQL Editor do Supabase
4. Clique em **Run**

### 6.3 Verificar Dados Inseridos
```sql
-- Verificar usuário demo
SELECT username, email, is_active FROM usuarios_usuario WHERE username = 'demo';

-- Verificar empresa
SELECT nome, cnpj FROM empresas_empresa WHERE cnpj = '12.345.678/0001-99';

-- Verificar funcionários
SELECT COUNT(*) as total FROM funcionarios_funcionario 
WHERE empresa_id = (SELECT id FROM empresas_empresa WHERE cnpj = '12.345.678/0001-99');

-- Verificar lançamentos
SELECT COUNT(*) as total FROM lancamentos_lancamento 
WHERE empresa_id = (SELECT id FROM empresas_empresa WHERE cnpj = '12.345.678/0001-99');
```

Deve retornar:
- 1 usuário (demo)
- 1 empresa
- 5 funcionários
- 18 lançamentos

---

## ✅ PASSO 7: Testar em Produção

### 7.1 Acessar Sistema
1. Abra https://fgts.bildee.com.br
2. Faça login com:
   - **Usuário:** demo
   - **Senha:** demo123456

### 7.2 Verificar Funcionalidades
- ✅ Dashboard carrega com 3 cards
- ✅ Lista de funcionários mostra 5 registros
- ✅ Lista de lançamentos mostra 18 registros
- ✅ Valores FGTS estão corretos (8% do salário)
- ✅ Botões de editar/excluir funcionários funcionam
- ✅ Navegação entre páginas funciona

### 7.3 Verificar Logs (Coolify)
1. No Coolify, vá em **Logs**
2. Verifique se não há erros de banco de dados
3. Deve ver logs como:
```
[INFO] Database connection: postgresql
[INFO] Connected to: db.xxxxx.supabase.co
```

---

## 🔍 TROUBLESHOOTING

### Erro: "FATAL: database does not exist"
**Solução:** Verifique que `SUPABASE_DB=postgres` (não use outro nome)

### Erro: "password authentication failed"
**Solução:** Verifique senha no Supabase Dashboard → Settings → Database

### Erro: "SSL connection required"
**Solução:** Já configurado em `settings.py` (linha 123) - verifique que está presente

### Erro: "could not connect to server"
**Solução:** 
1. Verifique se o host está correto: `db.XXXXX.supabase.co`
2. Verifique se a porta é `5432`
3. Verifique firewall do Supabase (Project Settings → Database → Connection Pooling)

### RLS bloqueando queries
**Solução:** Django usa `service_role_key` que bypassa RLS automaticamente. Se estiver bloqueado:
1. Verifique que está usando `service_role` (não `anon` key)
2. Verifique se as políticas têm `USING (true)` para service role

### Demo user não consegue fazer login
**Solução:**
1. Verifique que o hash da senha está correto no SQL
2. Teste com: `python manage.py changepassword demo`
3. Ou recrie: `python manage.py create_demo_user --reset`

---

## 📊 MONITORAMENTO

### Verificar Performance do Banco
No Supabase Dashboard:
1. **Database** → **Query Performance**
2. Monitore queries lentas
3. Crie índices se necessário

### Verificar Uso de Recursos
1. **Settings** → **Usage**
2. Monitore:
   - Database size
   - Bandwidth
   - API requests

### Limites do Free Tier
- Database: 500MB
- Bandwidth: 2GB/mês
- 500,000 reads/mês
- 50,000 writes/mês

⚠️ **Upgrade para Pro ($25/mês) quando ultrapassar**

---

## 🎯 CHECKLIST FINAL

Antes de considerar deploy completo, verifique:

- [ ] Variáveis de ambiente configuradas no Coolify
- [ ] `python manage.py migrate` executado com sucesso
- [ ] RLS ativo em todas as tabelas
- [ ] Planos padrão criados (3 planos)
- [ ] Dados demo inseridos
- [ ] Login demo funciona (demo/demo123456)
- [ ] Dashboard mostra dados corretos
- [ ] FGTS calculado corretamente (8%)
- [ ] Multi-tenant funcionando (usuários veem apenas seus dados)
- [ ] Logs do Coolify sem erros críticos

---

## 📞 SUPORTE

Se encontrar problemas:
1. Verifique logs do Coolify
2. Verifique logs do Supabase (Database → Logs)
3. Execute queries de diagnóstico no SQL Editor
4. Verifique que todas as variáveis de ambiente estão corretas

---

## 🎉 CONCLUSÃO

Após seguir todos os passos, seu sistema estará:
- ✅ Rodando em produção com PostgreSQL/Supabase
- ✅ Com RLS configurado para segurança
- ✅ Com dados demo para testes
- ✅ Multi-tenant funcional
- ✅ Pronto para receber clientes reais

**Próximos passos:**
1. Configurar domínio customizado
2. Configurar SSL/HTTPS
3. Configurar backups automáticos no Supabase
4. Monitorar performance e uso
5. Implementar estratégia de marketing para captação de clientes

---

**Última atualização:** 31/12/2025  
**Versão:** 1.0.0
