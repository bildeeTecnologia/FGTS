# 🔑 GUIA: Como Obter Credenciais PostgreSQL do Supabase

**Data:** 02 de Janeiro de 2026

---

## ⚠️ IMPORTANTE: Diferença entre APIs

Você compartilhou as credenciais da **API REST**, mas o Django precisa das credenciais do **PostgreSQL direto**.

### O que você tem (API REST):
```bash
URL: https://supabase.bildee.com.br/rest/v1/
API Key: eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```
✅ **Uso:** Consultas HTTP via API REST (útil para frontend, mobile)

### O que você precisa (PostgreSQL):
```env
SUPABASE_HOST=db.xxxxxxxxx.supabase.co
SUPABASE_DB=postgres
SUPABASE_USER=postgres
SUPABASE_PASSWORD=sua-senha-postgresql
SUPABASE_PORT=5432
```
✅ **Uso:** Conexão direta do Django ao banco PostgreSQL (muito mais rápido!)

---

## 🚀 PASSO A PASSO: Obtendo Credenciais PostgreSQL

### Opção 1: Via Dashboard Supabase (Recomendado)

#### 1. Acessar o Projeto
```
1. Abrir: https://supabase.com/dashboard
2. Fazer login (se necessário)
3. Selecionar seu projeto: "fgts-bildee" ou similar
```

#### 2. Navegar para Database Settings
```
1. No menu lateral esquerdo, clicar em: ⚙️ Settings (engrenagem)
2. Clicar em: Database
```

#### 3. Copiar Credenciais

Você verá uma seção chamada **"Connection string"** ou **"Connection info"**:

```plaintext
Host: db.xxxxxxxxxxxxxxxxx.supabase.co
Database name: postgres
Port: 5432
User: postgres
Password: [Click to reveal] ← CLICAR AQUI!
```

**Screenshot esperado:**
```
┌─────────────────────────────────────────────────┐
│ Database                                        │
├─────────────────────────────────────────────────┤
│ Connection string                               │
│                                                 │
│ postgres://postgres:[PASSWORD]@db.xxx.supabase.co:5432/postgres
│                                                 │
│ Connection parameters                           │
│ Host: db.xxxxxxxxxxxxxxxxx.supabase.co        │
│ Database name: postgres                         │
│ Port: 5432                                      │
│ User: postgres                                  │
│ Password: ●●●●●●●●●●●● [Show]                  │
└─────────────────────────────────────────────────┘
```

---

### Opção 2: Via Connection String

Se você tiver uma **Connection String** como esta:

```
postgres://postgres:SUA_SENHA_AQUI@db.xxxxxxx.supabase.co:5432/postgres
```

**Decodificar:**
```
postgres://     [protocolo]
postgres:       [usuário]
SUA_SENHA_AQUI  [senha]
@db.xxxxxxx.supabase.co  [host]
:5432           [porta]
/postgres       [database]
```

---

### Opção 3: Usar Connection Pooler (Recomendado para Produção)

Se estiver usando **Connection Pooler** (pgBouncer):

```
Host: aws-0-us-east-1.pooler.supabase.com
Port: 6543  ← DIFERENTE! (pooler usa 6543)
Database: postgres
User: postgres.xxxxxxx
Password: [sua senha]
```

**Vantagens do Pooler:**
- Suporta 1000+ conexões simultâneas
- Reduz latência
- Mais estável em produção

---

## 📝 ATUALIZAR SEU .env

### Cenário 1: Conexão Direta (Desenvolvimento)

```dotenv
# ===== DJANGO =====
DJANGO_SECRET_KEY=your-secret-key-here
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=127.0.0.1,localhost

# ===== SUPABASE POSTGRESQL (Conexão Direta) =====
SUPABASE_HOST=db.xxxxxxxxxxxxxxxxx.supabase.co
SUPABASE_DB=postgres
SUPABASE_USER=postgres
SUPABASE_PASSWORD=sua-senha-postgresql-aqui
SUPABASE_PORT=5432

# ===== SUPABASE REST API (Para leitura direta - opcional) =====
SUPABASE_URL=https://supabase.bildee.com.br
SUPABASE_KEY=eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJzdXBhYmFzZSIsImlhdCI6MTc2NjA2MjMyMCwiZXhwIjo0OTIxNzM1OTIwLCJyb2xlIjoiYW5vbiJ9.0kKgj8siWkfT18wWZHzSGVIJpr7grXnVcDBXnilV12s

# ===== ASAAS (Pagamentos) =====
ASAAS_API_KEY=your-asaas-key
ASAAS_SANDBOX=True
```

### Cenário 2: Connection Pooler (Produção)

```dotenv
# ===== SUPABASE POSTGRESQL (Connection Pooler - Produção) =====
SUPABASE_HOST=aws-0-us-east-1.pooler.supabase.com
SUPABASE_DB=postgres
SUPABASE_USER=postgres.xxxxxxxxxxxxxxxxx
SUPABASE_PASSWORD=sua-senha-postgresql-aqui
SUPABASE_PORT=6543  # ← DIFERENTE!
```

---

## ✅ VERIFICAR CONEXÃO

### Teste 1: Testar Connection String

```bash
# Windows PowerShell
cd "c:\Users\Gt_Soluções\OneDrive\Desktop\Projetos\PJT-FGTS PYTHON\FGTS-PYTHON"
.\.venv\Scripts\activate

# Testar conexão
python -c "import psycopg2; conn = psycopg2.connect('postgresql://postgres:SENHA@db.xxx.supabase.co:5432/postgres'); print('Conexão OK!'); conn.close()"
```

**Resposta esperada:**
```
Conexão OK!
```

### Teste 2: Testar via Django Shell

```python
# Abrir shell Django
python manage.py shell

# No shell:
from django.db import connection

# Testar conexão
with connection.cursor() as cursor:
    cursor.execute("SELECT version();")
    print(cursor.fetchone())
    # Deve retornar: ('PostgreSQL 15.x on x86_64-pc-linux-gnu...',)

# Testar database name
with connection.cursor() as cursor:
    cursor.execute("SELECT current_database();")
    print(cursor.fetchone())
    # Deve retornar: ('postgres',)
```

**Resposta esperada:**
```python
('PostgreSQL 15.6 on x86_64-pc-linux-gnu, compiled by gcc...',)
('postgres',)
```

---

## 🔒 SEGURANÇA

### ⚠️ NUNCA COMMITAR CREDENCIAIS

```bash
# Verificar se .env está no .gitignore
cat .gitignore | Select-String ".env"

# Se não estiver, adicionar:
echo ".env" >> .gitignore
echo ".env.local" >> .gitignore
echo ".env.production" >> .gitignore
```

### 🔑 Usar Variáveis de Ambiente em Produção

**Para deploy (Coolify, Docker, etc):**

```bash
# Não usar arquivo .env
# Definir variáveis direto no sistema

# Linux/Docker:
export SUPABASE_HOST=db.xxx.supabase.co
export SUPABASE_PASSWORD=senha-segura-aqui

# Windows (PowerShell):
$env:SUPABASE_HOST = "db.xxx.supabase.co"
$env:SUPABASE_PASSWORD = "senha-segura-aqui"
```

---

## 🐛 TROUBLESHOOTING

### Erro: "could not connect to server"

```python
psycopg2.OperationalError: could not connect to server: 
    Connection timed out
```

**Soluções:**
1. Verificar firewall (porta 5432 ou 6543)
2. Verificar se o IP está na whitelist do Supabase
3. Tentar connection pooler (porta 6543)

**Fix Supabase Dashboard:**
```
1. Ir em: Settings → Database
2. Rolar até: "Connection pooling"
3. Habilitar: "Enable connection pooling"
4. Usar porta 6543 ao invés de 5432
```

### Erro: "password authentication failed"

```python
psycopg2.OperationalError: 
    password authentication failed for user "postgres"
```

**Soluções:**
1. Resetar senha no Dashboard:
   - Settings → Database → Database password → Reset
2. Copiar nova senha
3. Atualizar .env

### Erro: "SSL connection required"

```python
psycopg2.OperationalError: 
    SSL connection (protocol: TLSv1.3) required
```

**Fix em settings.py:**
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'HOST': SUPABASE_HOST,
        'PORT': int(SUPABASE_PORT),
        'NAME': SUPABASE_DB,
        'USER': SUPABASE_USER,
        'PASSWORD': SUPABASE_PASSWORD,
        'OPTIONS': {
            'sslmode': 'require',  # ← ADICIONAR ESTA LINHA!
        },
    }
}
```

---

## 📊 COMPARAÇÃO DE PERFORMANCE

### API REST vs PostgreSQL Direto

| Operação | REST API | PostgreSQL | Ganho |
|----------|----------|------------|-------|
| **Query simples** | 150-300ms | 5-15ms | 20x ⚡ |
| **Query com joins** | 500-1200ms | 20-80ms | 15x ⚡ |
| **Insert batch (100)** | 2000-5000ms | 100-300ms | 20x ⚡ |
| **Transações** | ❌ Complexo | ✅ Nativo | ∞x ⚡ |

**Conclusão:** PostgreSQL direto é 15-20x mais rápido! 🚀

---

## ✅ CHECKLIST FINAL

Antes de migrar, confirme que tem:

- [ ] SUPABASE_HOST (db.xxx.supabase.co)
- [ ] SUPABASE_DB (postgres)
- [ ] SUPABASE_USER (postgres)
- [ ] SUPABASE_PASSWORD (revelada no dashboard)
- [ ] SUPABASE_PORT (5432 ou 6543 se pooler)
- [ ] psycopg2-binary instalado (✅ você já tem!)
- [ ] .env atualizado com credenciais
- [ ] Testou conexão via Python
- [ ] Backup do SQLite feito

---

## 🚀 PRÓXIMO PASSO

Depois de obter as credenciais e atualizar o `.env`:

```bash
# 1. Testar conexão
python -c "from django.db import connection; connection.ensure_connection(); print('PostgreSQL conectado!')"

# 2. Rodar migrations
python manage.py migrate

# 3. Criar superuser (se não tiver)
python manage.py createsuperuser

# 4. Testar servidor
python manage.py runserver

# 5. Acessar admin
# http://127.0.0.1:8000/admin
```

---

## 📞 SUPORTE

Se não conseguir encontrar as credenciais:

1. **Verificar email** - Supabase envia email com credenciais ao criar projeto
2. **Resetar senha** - Settings → Database → Reset password
3. **Contato Supabase** - support@supabase.io (se for cliente pago)

---

**Última atualização:** 02/01/2026  
**Status:** Aguardando credenciais PostgreSQL para migração completa
