# 🚀 DEPLOY FGTS WEB - COOLIFY (VPS Ubuntu 24.04)

## 📋 Pré-requisitos
- ✅ VPS com Coolify instalado (72.60.58.44)
- ✅ Acesso SSH: `ssh root@72.60.58.44`
- ✅ Git instalado na VPS

## 🎯 PASSO 1: Preparar o Projeto Localmente

### 1.1 Adicionar gunicorn ao requirements.txt
```bash
echo "gunicorn==21.2.0" >> requirements.txt
```

### 1.2 Configurar settings.py para produção
Abra `fgtsweb/settings.py` e adicione no final:

```python
# Configurações de produção
if not DEBUG:
    ALLOWED_HOSTS = ['*']  # Altere para seu domínio depois
    STATIC_ROOT = BASE_DIR / 'staticfiles'
    CSRF_TRUSTED_ORIGINS = [
        'http://72.60.58.44',
        'https://72.60.58.44',
    ]
```

### 1.3 Criar repositório Git (se ainda não tem)
```bash
cd "C:\Users\Gt_Soluções\OneDrive\Desktop\Projetos\PJT-FGTS PYTHON\FGTS-PYTHON"
git init
git add .
git commit -m "Deploy inicial"
```

### 1.4 Subir para GitHub/GitLab
```bash
# Criar repositório no GitHub e depois:
git remote add origin https://github.com/SEU_USUARIO/fgts-python.git
git push -u origin main
```

## 🎯 PASSO 2: Configurar no Coolify

### 2.1 Acessar Coolify
1. Abra o navegador e acesse o painel Coolify da VPS
2. Clique em **"Gerenciar painel"** ou acesse diretamente a URL do Coolify

### 2.2 Criar Novo Projeto
1. Clique em **"+ New Project"**
2. Nome: `FGTS Web`
3. Clique em **"Create"**

### 2.3 Adicionar Aplicação
1. Dentro do projeto, clique em **"+ Add Resource"**
2. Escolha **"Application"**
3. Selecione **"Public Repository"** (ou Private se configurou)
4. Cole a URL do seu repositório Git

### 2.4 Configurar Build
1. **Build Pack**: Selecione `Dockerfile`
2. **Port**: `8000`
3. **Domain**: Deixe o IP da VPS ou configure um domínio

### 2.5 Configurar Variáveis de Ambiente
Adicione estas variáveis em **Environment Variables**:

```env
DEBUG=False
SECRET_KEY=sua-chave-secreta-super-forte-aqui-123456789
SUPABASE_URL=https://supabase.bildee.com.br
SUPABASE_KEY=eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJzdXBhYmFzZSIsImlhdCI6MTc2NjA2MjMyMCwiZXhwIjo0OTIxNzM1OTIwLCJyb2xlIjoiYW5vbiJ9.0kKgj8siWkfT18wWZHzSGVIJpr7grXnVcDBXnilV12s
DJANGO_ALLOWED_HOSTS=72.60.58.44,localhost
```

### 2.6 Deploy!
1. Clique em **"Deploy"**
2. Aguarde o build (2-5 minutos)
3. Quando finalizar, seu app estará no ar!

## 🎯 PASSO 3: Após o Deploy

### 3.1 Acessar a aplicação
```
http://72.60.58.44:8000/admin
```

**Login padrão:**
- Usuário: `admin`
- Senha: `senha123`

### 3.2 Verificar logs
No painel Coolify:
1. Vá até a aplicação
2. Clique em **"Logs"**
3. Verifique se tudo está funcionando

## 🔧 ALTERNATIVA RÁPIDA: Deploy Manual via SSH

Se preferir fazer manualmente sem Coolify:

```bash
# 1. Conectar na VPS
ssh root@72.60.58.44

# 2. Instalar dependências
apt update
apt install -y python3-pip python3-venv git nginx

# 3. Clonar projeto
cd /var/www
git clone https://github.com/SEU_USUARIO/fgts-python.git
cd fgts-python

# 4. Criar ambiente virtual e instalar dependências
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt gunicorn

# 5. Configurar variáveis de ambiente
cat > .env << 'EOF'
DEBUG=False
SECRET_KEY=sua-chave-secreta-aqui
SUPABASE_URL=https://supabase.bildee.com.br
SUPABASE_KEY=eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJzdXBhYmFzZSIsImlhdCI6MTc2NjA2MjMyMCwiZXhwIjo0OTIxNzM1OTIwLCJyb2xlIjoiYW5vbiJ9.0kKgj8siWkfT18wWZHzSGVIJpr7grXnVcDBXnilV12s
EOF

# 6. Rodar migrations
python manage.py migrate
python manage.py collectstatic --noinput

# 7. Criar superuser
python manage.py createsuperuser

# 8. Iniciar Gunicorn
gunicorn --bind 0.0.0.0:8000 --workers 4 fgtsweb.wsgi:application &
```

## 📝 Notas Importantes

1. **Banco de Dados**: Está usando SQLite. Para produção real, recomendo PostgreSQL.
2. **SECRET_KEY**: Gere uma nova chave segura em produção.
3. **Domínio**: Configure um domínio real depois (não use apenas IP).
4. **SSL/HTTPS**: Coolify pode configurar automaticamente com Let's Encrypt.
5. **Backup**: Configure backup automático do db.sqlite3.

## 🆘 Troubleshooting

### Erro: "Bad Request (400)"
- Verifique `ALLOWED_HOSTS` no settings.py
- Adicione o IP/domínio da VPS

### Erro: "Static files not found"
```bash
python manage.py collectstatic --noinput
```

### Erro: "Database locked"
- SQLite não é ideal para múltiplos workers
- Reduza workers do Gunicorn para 2
- Ou migre para PostgreSQL

## ✅ Checklist Final

- [ ] Dockerfile criado
- [ ] .dockerignore criado
- [ ] Variáveis de ambiente configuradas
- [ ] Git repository criado
- [ ] Deploy no Coolify executado
- [ ] Aplicação acessível no navegador
- [ ] Login admin funcionando
- [ ] Logs sem erros

## 🎉 Sucesso!

Sua aplicação está no ar em: **http://72.60.58.44:8000**

Para o cliente acessar, compartilhe esse link!
