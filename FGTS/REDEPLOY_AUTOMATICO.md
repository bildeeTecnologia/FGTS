# 🚀 REDEPLOY AUTOMÁTICO - COOLIFY

## ✅ O QUE FOI CONFIGURADO

O projeto agora está **100% automatizado**. O arquivo [start.sh](start.sh) executa automaticamente no deploy:

1. ✅ Verifica conexão com banco de dados
2. ✅ Aplica todas as migrações
3. ✅ Coleta arquivos estáticos
4. ✅ Cria superuser padrão (se não existir)
5. ✅ Inicia servidor Gunicorn

**Você só precisa:**
1. Configurar variáveis no Coolify (uma vez)
2. Fazer commit + push
3. Redeploy no Coolify

---

## 📋 PASSO 1: Configurar Variáveis no Coolify (PRIMEIRA VEZ)

**Acesse:** Coolify → Projeto FGTS Web → **Environment Variables**

Adicione estas variáveis:

```env
DJANGO_SECRET_KEY=sua-chave-secreta-forte-aqui
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=fgts.bildee.com.br,127.0.0.1,localhost

SUPABASE_HOST=db.qbyipfcyqnaptstidphj.supabase.co
SUPABASE_DB=postgres
SUPABASE_USER=postgres
SUPABASE_PASSWORD=your-supabase-password
SUPABASE_PORT=6543

SUPABASE_URL=https://qbyipfcyqnaptstidphj.supabase.co
SUPABASE_KEY=your-supabase-service-role-key

ASAAS_API_KEY=your-asaas-key-here
ASAAS_SANDBOX=True
```

**⚠️ IMPORTANTE:** Gere uma SECRET_KEY forte (execute localmente):

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

---

## 🚀 PASSO 2: Fazer Commit das Mudanças

```bash
cd "C:\Users\Gt_Soluções\OneDrive\Desktop\Projetos\PJT-FGTS PYTHON\FGTS-PYTHON"

git add .
git commit -m "feat: Configurar deploy automático com migrações"
git push origin main
```

---

## 🔄 PASSO 3: Redeploy no Coolify

### Opção A: Redeploy Automático (se configurado webhook)
- O Coolify detecta o push e faz deploy automaticamente

### Opção B: Redeploy Manual
1. Acesse o painel do Coolify
2. Vá em: Projeto FGTS Web
3. Clique em **"Redeploy"** ou **"Deploy"**
4. Aguarde 2-5 minutos

---

## 📊 O QUE ACONTECE NO DEPLOY

```
🚀 Iniciando aplicação FGTS Web...
==========================================

📋 1. Verificando conexão com banco de dados...
✅ Banco de dados: Conectado

📋 2. Aplicando migrações...
✅ Migrações: Aplicadas com sucesso

📋 3. Coletando arquivos estáticos...
✅ Arquivos estáticos: Coletados

📋 4. Verificando superuser...
✅ Superuser criado: admin/senha123

📊 Informações do sistema:
  → Python: 3.11
  → Django: 5.1.4
  → Banco: PostgreSQL/Supabase ✅

==========================================
✅ Iniciando servidor Gunicorn...
==========================================
```

---

## ✅ VERIFICAR SE DEU CERTO

### 1. Verificar Logs no Coolify
- Acesse: Coolify → Projeto → **Logs**
- Procure por: `✅ Migrações: Aplicadas com sucesso`
- Procure por: `✅ Banco: PostgreSQL/Supabase`

### 2. Testar Registro de Usuário
- Acesse: http://fgts.bildee.com.br/usuario/registrar/
- Crie um novo usuário
- ✅ Deve funcionar sem erro `empresa_id`

### 3. Testar Login
- Acesse: http://fgts.bildee.com.br/usuario/login/
- Login: `admin` / Senha: `senha123`
- ✅ Deve entrar no sistema

---

## 🔄 DEPLOY DE NOVAS ATUALIZAÇÕES

**A partir de agora, para qualquer mudança:**

```bash
# 1. Fazer alterações no código
# 2. Commit e push
git add .
git commit -m "descrição da mudança"
git push origin main

# 3. Redeploy no Coolify (ou aguardar webhook)
```

**As migrações serão aplicadas automaticamente!** 🎉

---

## 🆘 TROUBLESHOOTING

### ❌ Erro: "Não foi possível conectar ao banco"

**Verifique:**
1. Variáveis `SUPABASE_*` estão corretas no Coolify
2. Porta é `6543` (não 5432)
3. Container foi reiniciado após adicionar variáveis

**Solução:**
```bash
# No terminal do Coolify:
python -c "import os; print('HOST:', os.getenv('SUPABASE_HOST'))"
python -c "import os; print('PORT:', os.getenv('SUPABASE_PORT'))"
```

### ❌ Ainda usando SQLite

**Logs mostram:** `⚠️ Banco: SQLite`

**Solução:**
1. Verifique se as variáveis foram salvas no Coolify
2. Reinicie o container
3. Verifique os logs novamente

### ❌ Erro nas migrações

**Logs mostram:** `❌ Erro ao aplicar migrações`

**Solução:**
1. Verifique os logs completos no Coolify
2. Se a tabela já existe, pode ser apenas aviso
3. Teste o sistema para confirmar se está funcionando

---

## 📁 ARQUIVOS MODIFICADOS

- ✅ [start.sh](start.sh) - Script de inicialização automática
- ✅ [fgtsweb/settings.py](fgtsweb/settings.py) - Porta 6543 como padrão
- ✅ [Dockerfile](Dockerfile) - Já configurado
- ✅ [.env](.env) - Credenciais locais (dev)
- ✅ [.env.production](.env.production) - Template para Coolify

---

## 🎯 RESUMO

### Antes (Manual):
```
1. Fazer backup manualmente
2. Configurar variáveis
3. SSH no servidor
4. Executar scripts manualmente
5. Verificar tudo manualmente
```

### Agora (Automático):
```
1. Configurar variáveis no Coolify (uma vez)
2. git push
3. Redeploy
4. ✅ Pronto!
```

---

## 📞 PRÓXIMOS DEPLOYS

**Rotina normal:**

```bash
# 1. Desenvolver localmente
# 2. Testar
python manage.py runserver

# 3. Commit
git add .
git commit -m "feat: nova funcionalidade"
git push

# 4. Redeploy no Coolify
# As migrações serão aplicadas automaticamente!
```

---

## ⏱️ TEMPO ESTIMADO

- **Primeira configuração:** 10 minutos
- **Próximos deploys:** 2-3 minutos (só git push + redeploy)

---

**Tudo automatizado! 🚀**
