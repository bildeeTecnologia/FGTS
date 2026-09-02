# Configuração de Ambiente - FGTS System

## Variáveis de Ambiente Obrigatórias

O sistema utiliza as seguintes variáveis de ambiente para conectar ao Supabase (fonte da verdade para índices FGTS):

### Configuração Automática (.env)

As credenciais estão configuradas no arquivo `.env` na raiz do projeto e são carregadas automaticamente pelo Django via `python-dotenv`.

**Arquivo: `.env`**
```
SUPABASE_URL=https://supabase.bildee.com.br
SUPABASE_KEY=eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

### Configuração Manual (PowerShell)

Se preferir configurar manualmente, execute:

```powershell
. .\scripts\set_env.ps1
```

Ou diretamente no terminal:

```powershell
$env:SUPABASE_URL = "https://supabase.bildee.com.br"
$env:SUPABASE_KEY = "sua-chave-aqui"
```

## Iniciando o Servidor

Com o `.env` configurado, basta executar:

```bash
python manage.py runserver
```

As variáveis serão carregadas automaticamente!

## Importante

⚠️ **NUNCA commite o arquivo `.env` com credenciais reais!**
- O arquivo `.env` já está no `.gitignore`
- Use `.env.example` para documentar variáveis necessárias sem expor valores reais

## Verificação

Para verificar se as credenciais estão configuradas corretamente:

```python
from django.conf import settings
print(f"SUPABASE_URL: {settings.SUPABASE_API_URL}")
print(f"SUPABASE_KEY: {'Configurado' if settings.SUPABASE_API_KEY else 'Não configurado'}")
```

## Índices FGTS

O sistema busca índices **EXCLUSIVAMENTE** da tabela `indices_fgts` no Supabase via:
1. ORM Django (SupabaseIndice model) - se conexão Postgres estiver configurada
2. REST API Supabase - fallback automático
3. **Não há mais fallback para tabela local!**
