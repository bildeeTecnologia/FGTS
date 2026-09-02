# 🚨 CORREÇÃO URGENTE - PRODUÇÃO (fgts.bildee.com.br)

**Erro:** `table usuarios_usuario has no column named empresa_id`

**Causa:** Migrações não aplicadas + SQLite sendo usado ao invés do Supabase

---

## ✅ CHECKLIST DE CORREÇÃO

### 🔴 ETAPA 1: Aplicar Migrações (URGENTE)

**Via Terminal Coolify:**

1. Acesse o painel do Coolify
2. Vá até a aplicação FGTS Web
3. Clique em **"Terminal"** ou **"Execute Command"**
4. Execute:

```bash
python manage.py migrate
```

5. Verifique se aplicou:

```bash
python manage.py showmigrations usuarios
```

**Resultado esperado:**
```
usuarios
 [X] 0001_initial
 [X] 0002_usuario_empresa_usuario_empresas_permitidas_and_more
```

---

### 🔴 ETAPA 2: Configurar Supabase em Produção

**Problema atual:** O Django está usando SQLite porque as variáveis do Supabase não estão configuradas.

#### 2.1 Adicionar Variáveis de Ambiente no Coolify

Acesse: **Coolify → Projeto FGTS Web → Environment Variables**

Adicione/Verifique estas variáveis:

```env
# Django
DJANGO_SECRET_KEY=your-secret-key-change-in-production
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=fgts.bildee.com.br,127.0.0.1,localhost

# Supabase PostgreSQL
SUPABASE_HOST=db.qbyipfcyqnaptstidphj.supabase.co
SUPABASE_DB=postgres
SUPABASE_USER=postgres
SUPABASE_PASSWORD=your-supabase-password
SUPABASE_PORT=6543

# Supabase REST API
SUPABASE_URL=https://qbyipfcyqnaptstidphj.supabase.co
SUPABASE_KEY=your-supabase-service-role-key

# Asaas (Pagamentos)
ASAAS_API_KEY=your-asaas-key-here
ASAAS_SANDBOX=True
```

#### 2.2 Reiniciar Container

Após adicionar as variáveis:

1. Clique em **"Restart"** no Coolify
2. Aguarde 1-2 minutos
3. Verifique os logs para confirmar que conectou no Postgres

---

### 🔴 ETAPA 3: Migrar Dados do SQLite para Supabase (Se necessário)

**⚠️ Se já existem usuários/empresas/dados no SQLite de produção:**

#### 3.1 Backup do SQLite atual

```bash
# No terminal do Coolify
python manage.py dumpdata --natural-foreign --natural-primary \
  -e contenttypes -e auth.Permission \
  --indent 2 > backup_producao.json
```

#### 3.2 Aplicar migrations no Supabase

```bash
# Já com as variáveis configuradas
python manage.py migrate
```

#### 3.3 Importar dados para Supabase

```bash
python manage.py loaddata backup_producao.json
```

---

### ✅ ETAPA 4: Verificação Final

Execute no terminal do Coolify:

```bash
# 1. Verificar conexão com Supabase
python manage.py dbshell
# Deve abrir console do PostgreSQL
# Digite \dt para listar tabelas
# Digite \q para sair

# 2. Verificar usuários
python manage.py shell
>>> from usuarios.models import Usuario
>>> Usuario.objects.count()
>>> exit()

# 3. Verificar estrutura da tabela usuarios_usuario
python manage.py dbshell
SELECT column_name, data_type FROM information_schema.columns 
WHERE table_name = 'usuarios_usuario';
\q
```

**Colunas esperadas na tabela usuarios_usuario:**
- `id`
- `password`
- `last_login`
- `is_superuser`
- `username`
- `first_name`
- `last_name`
- `email`
- `is_staff`
- `is_active`
- `date_joined`
- `manutencao`
- **`empresa_id`** ← deve existir após migração
- `is_multi_empresa`

---

## 🔍 VERIFICAÇÃO DE PRODUÇÃO

### Teste 1: Criar Usuário
1. Acesse: http://fgts.bildee.com.br/usuario/registrar/
2. Preencha o formulário
3. **Resultado esperado:** Usuário criado com sucesso

### Teste 2: Login
1. Acesse: http://fgts.bildee.com.br/usuario/login/
2. Faça login
3. **Resultado esperado:** Redirecionamento para dashboard

### Teste 3: Verificar banco
```bash
python manage.py dbshell
SELECT id, username, empresa_id FROM usuarios_usuario LIMIT 5;
\q
```

---

## 📊 STATUS ATUAL vs ESPERADO

### ❌ STATUS ATUAL (PROBLEMA)
```
✗ Django usando SQLite em produção
✗ Tabela usuarios_usuario sem coluna empresa_id
✗ Variáveis Supabase não configuradas no Coolify
✗ Erro ao criar usuários
```

### ✅ STATUS ESPERADO (APÓS CORREÇÃO)
```
✓ Django usando PostgreSQL/Supabase em produção
✓ Todas as migrações aplicadas
✓ Tabela usuarios_usuario com todas as colunas
✓ Registro de usuários funcionando
✓ Dados persistidos no Supabase
```

---

## 🆘 TROUBLESHOOTING

### Erro: "FATAL: no such user"
**Solução:** Usar porta 6543 ao invés de 5432 e verificar credenciais

### Erro: "Connection timed out"
**Solução:** 
1. Verificar firewall do servidor
2. Testar conexão: `nc -zv db.qbyipfcyqnaptstidphj.supabase.co 6543`
3. Usar sslmode=require no settings.py

### Erro: "relation usuarios_usuario does not exist"
**Solução:** Executar `python manage.py migrate` novamente

### SQLite ainda sendo usado após adicionar variáveis
**Solução:**
1. Verificar se as variáveis foram salvas (sem espaços extras)
2. Reiniciar o container no Coolify
3. Verificar logs: deve aparecer "PostgreSQL" e não "SQLite"

---

## 📝 ORDEM DE EXECUÇÃO RECOMENDADA

```
1. ✅ ETAPA 1: Aplicar migrações no banco atual (SQLite)
   └─→ Resolve erro imediato, permite criar usuários

2. ✅ ETAPA 2: Configurar variáveis Supabase no Coolify
   └─→ Próximo restart usará PostgreSQL

3. ✅ ETAPA 3: Backup e migração de dados (se houver)
   └─→ Preserva dados existentes

4. ✅ ETAPA 4: Verificação e testes
   └─→ Confirma que tudo está funcionando
```

---

## ⏱️ TEMPO ESTIMADO

- Etapa 1 (Migrate): **2-3 minutos**
- Etapa 2 (Config Supabase): **5-10 minutos**
- Etapa 3 (Migração dados): **5-15 minutos** (depende do volume)
- Etapa 4 (Verificação): **3-5 minutos**

**Total: 15-30 minutos**

---

## 🎯 AÇÃO IMEDIATA (1 comando)

Se quiser resolver o erro AGORA sem mudar para Supabase ainda:

```bash
python manage.py migrate
```

Isso permite criar usuários. Depois você configura o Supabase com calma.

---

## 📞 CONTATO/SUPORTE

Se encontrar problemas:
1. Verifique os logs no Coolify
2. Teste a conexão com Supabase localmente primeiro
3. Compare settings.py local (funcionando) vs produção

**Arquivos de referência:**
- [.env](file://.env) ← credenciais corretas
- [settings.py](file://fgtsweb/settings.py) ← lógica de conexão
- [GUIA_DEPLOY_SUPABASE.md](file://GUIA_DEPLOY_SUPABASE.md) ← deploy completo
