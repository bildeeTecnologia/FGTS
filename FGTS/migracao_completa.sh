#!/bin/bash
# ============================================
# SCRIPT DE MIGRAÇÃO - SQLite → Supabase
# ============================================
# Execute no terminal do Coolify APÓS:
# - Ter feito backup (backup_producao.sh)
# - Ter configurado variáveis de ambiente
# - Ter reiniciado o container
#
# Como usar:
# 1. Copie e cole este script no terminal do Coolify
# 2. Pressione Enter
# 3. Acompanhe o processo
# ============================================

set -e  # Parar em caso de erro

echo "🚀 Iniciando migração para Supabase..."
echo "=========================================="
echo ""

# ============================================
# ETAPA 1: Verificar Variáveis de Ambiente
# ============================================
echo "📋 ETAPA 1: Verificando variáveis de ambiente..."
echo ""

VARS_OK=true

if [ -z "$SUPABASE_HOST" ]; then
    echo "❌ SUPABASE_HOST não configurada!"
    VARS_OK=false
else
    echo "✅ SUPABASE_HOST: $SUPABASE_HOST"
fi

if [ -z "$SUPABASE_DB" ]; then
    echo "❌ SUPABASE_DB não configurada!"
    VARS_OK=false
else
    echo "✅ SUPABASE_DB: $SUPABASE_DB"
fi

if [ -z "$SUPABASE_USER" ]; then
    echo "❌ SUPABASE_USER não configurada!"
    VARS_OK=false
else
    echo "✅ SUPABASE_USER: $SUPABASE_USER"
fi

if [ -z "$SUPABASE_PASSWORD" ]; then
    echo "❌ SUPABASE_PASSWORD não configurada!"
    VARS_OK=false
else
    echo "✅ SUPABASE_PASSWORD: *** (ocultada)"
fi

if [ "$VARS_OK" = false ]; then
    echo ""
    echo "❌ Variáveis faltando! Configure no Coolify e reinicie o container."
    exit 1
fi

echo ""
echo "✅ Todas as variáveis configuradas!"
echo ""

# ============================================
# ETAPA 2: Testar Conexão com Supabase
# ============================================
echo "📋 ETAPA 2: Testando conexão com Supabase..."
echo ""

python -c "
import os
import psycopg2

try:
    conn = psycopg2.connect(
        host=os.getenv('SUPABASE_HOST'),
        database=os.getenv('SUPABASE_DB'),
        user=os.getenv('SUPABASE_USER'),
        password=os.getenv('SUPABASE_PASSWORD'),
        port=os.getenv('SUPABASE_PORT', '6543'),
        sslmode='require'
    )
    print('✅ Conexão com Supabase estabelecida com sucesso!')
    conn.close()
except Exception as e:
    print(f'❌ Erro ao conectar: {e}')
    exit(1)
"

if [ $? -ne 0 ]; then
    echo ""
    echo "❌ Não foi possível conectar ao Supabase!"
    echo "Verifique:"
    echo "  - Credenciais corretas"
    echo "  - Porta 6543 acessível"
    echo "  - Firewall liberado"
    exit 1
fi

echo ""

# ============================================
# ETAPA 3: Verificar Banco Atual
# ============================================
echo "📋 ETAPA 3: Verificando banco de dados atual..."
echo ""

DB_ENGINE=$(python -c "
from django.conf import settings
print(settings.DATABASES['default']['ENGINE'])
")

echo "🔍 Engine atual: $DB_ENGINE"

if [[ "$DB_ENGINE" == *"sqlite"* ]]; then
    echo "⚠️  Ainda usando SQLite - algo está errado!"
    echo "Verifique se as variáveis foram salvas e o container foi reiniciado."
    exit 1
elif [[ "$DB_ENGINE" == *"postgresql"* ]]; then
    echo "✅ Usando PostgreSQL (Supabase)!"
else
    echo "⚠️  Engine desconhecida: $DB_ENGINE"
fi

echo ""

# ============================================
# ETAPA 4: Aplicar Migrações
# ============================================
echo "📋 ETAPA 4: Aplicando migrações no Supabase..."
echo ""

python manage.py migrate --noinput

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Migrações aplicadas com sucesso!"
else
    echo ""
    echo "❌ Erro ao aplicar migrações!"
    exit 1
fi

echo ""

# ============================================
# ETAPA 5: Verificar Estrutura das Tabelas
# ============================================
echo "📋 ETAPA 5: Verificando estrutura da tabela usuarios_usuario..."
echo ""

python manage.py dbshell << EOF
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'usuarios_usuario' 
ORDER BY ordinal_position;
EOF

echo ""

# ============================================
# ETAPA 6: Importar Dados (se houver backup)
# ============================================
echo "📋 ETAPA 6: Importação de dados..."
echo ""

BACKUP_FILE=$(ls -t backup_producao_*.json 2>/dev/null | head -1)

if [ -n "$BACKUP_FILE" ]; then
    echo "📦 Backup encontrado: $BACKUP_FILE"
    echo "🔄 Importando dados..."
    
    python manage.py loaddata "$BACKUP_FILE"
    
    if [ $? -eq 0 ]; then
        echo "✅ Dados importados com sucesso!"
    else
        echo "⚠️  Erro ao importar dados - mas tabelas estão criadas"
        echo "Você pode importar manualmente depois"
    fi
else
    echo "ℹ️  Nenhum backup encontrado - pulando importação"
    echo "Se você tem um backup, execute:"
    echo "  python manage.py loaddata backup_producao_TIMESTAMP.json"
fi

echo ""

# ============================================
# ETAPA 7: Verificação Final
# ============================================
echo "📋 ETAPA 7: Verificação final..."
echo ""

echo "📊 Contagem de registros:"
echo ""

EMPRESAS=$(python manage.py shell -c "from empresas.models import Empresa; print(Empresa.objects.count())" 2>/dev/null)
echo "  → Empresas: $EMPRESAS"

USUARIOS=$(python manage.py shell -c "from usuarios.models import Usuario; print(Usuario.objects.count())" 2>/dev/null)
echo "  → Usuários: $USUARIOS"

FUNCIONARIOS=$(python manage.py shell -c "from funcionarios.models import Funcionario; print(Funcionario.objects.count())" 2>/dev/null)
echo "  → Funcionários: $FUNCIONARIOS"

LANCAMENTOS=$(python manage.py shell -c "from lancamentos.models import Lancamento; print(Lancamento.objects.count())" 2>/dev/null)
echo "  → Lançamentos: $LANCAMENTOS"

echo ""
echo "=========================================="
echo "✅ MIGRAÇÃO CONCLUÍDA COM SUCESSO!"
echo "=========================================="
echo ""
echo "📋 Próximos passos:"
echo "  1. Teste o registro de novo usuário"
echo "  2. Verifique o login"
echo "  3. Navegue pelo sistema"
echo "  4. Execute o script de verificação (verificacao_pos_deploy.sh)"
echo ""
echo "🌐 Acesse: http://fgts.bildee.com.br"
echo ""
