#!/bin/bash
# ============================================
# SCRIPT DE VERIFICAÇÃO PÓS-DEPLOY
# ============================================
# Execute após concluir a migração
# Valida que tudo está funcionando corretamente
# ============================================

echo "🔍 VERIFICAÇÃO PÓS-DEPLOY"
echo "=========================================="
echo ""

ALL_OK=true

# ============================================
# 1. Verificar Banco de Dados
# ============================================
echo "📋 1. Verificando conexão com banco de dados..."
echo ""

DB_CHECK=$(python manage.py dbshell <<EOF 2>&1
SELECT 'OK' as status;
\q
EOF
)

if echo "$DB_CHECK" | grep -q "OK"; then
    echo "✅ Banco de dados: PostgreSQL conectado"
else
    echo "❌ Erro na conexão com banco de dados"
    ALL_OK=false
fi

echo ""

# ============================================
# 2. Verificar Migrações
# ============================================
echo "📋 2. Verificando status das migrações..."
echo ""

PENDING=$(python manage.py showmigrations --plan | grep "\[ \]" | wc -l)

if [ "$PENDING" -eq 0 ]; then
    echo "✅ Migrações: Todas aplicadas"
else
    echo "⚠️  Migrações pendentes: $PENDING"
    echo "Execute: python manage.py migrate"
    ALL_OK=false
fi

echo ""

# ============================================
# 3. Verificar Tabela usuarios_usuario
# ============================================
echo "📋 3. Verificando estrutura da tabela usuarios_usuario..."
echo ""

HAS_EMPRESA_ID=$(python manage.py dbshell <<EOF 2>&1
SELECT COUNT(*) FROM information_schema.columns 
WHERE table_name = 'usuarios_usuario' AND column_name = 'empresa_id';
\q
EOF
)

if echo "$HAS_EMPRESA_ID" | grep -q "1"; then
    echo "✅ Coluna empresa_id: Existe"
else
    echo "❌ Coluna empresa_id: Não encontrada"
    ALL_OK=false
fi

echo ""

# ============================================
# 4. Testar Criação de Usuário (Dry Run)
# ============================================
echo "📋 4. Testando modelo de usuário..."
echo ""

TEST_USER=$(python manage.py shell <<EOF 2>&1
from usuarios.models import Usuario
from empresas.models import Empresa

# Verificar se consegue acessar o modelo
try:
    count = Usuario.objects.count()
    print(f"OK:{count}")
except Exception as e:
    print(f"ERROR:{e}")
EOF
)

if echo "$TEST_USER" | grep -q "OK:"; then
    USER_COUNT=$(echo "$TEST_USER" | grep "OK:" | cut -d: -f2)
    echo "✅ Modelo Usuario: Funcionando ($USER_COUNT usuários)"
else
    echo "❌ Modelo Usuario: Erro"
    echo "$TEST_USER"
    ALL_OK=false
fi

echo ""

# ============================================
# 5. Verificar Variáveis de Ambiente
# ============================================
echo "📋 5. Verificando variáveis de ambiente críticas..."
echo ""

# DEBUG
if [ "$DJANGO_DEBUG" = "False" ]; then
    echo "✅ DEBUG: False (produção)"
else
    echo "⚠️  DEBUG: $DJANGO_DEBUG (deveria ser False)"
fi

# SECRET_KEY
if [ -n "$DJANGO_SECRET_KEY" ] && [ "$DJANGO_SECRET_KEY" != "your-secret-key-change-in-production" ]; then
    echo "✅ SECRET_KEY: Configurada"
else
    echo "⚠️  SECRET_KEY: Usando valor padrão (inseguro!)"
    ALL_OK=false
fi

# SUPABASE
if [ -n "$SUPABASE_HOST" ]; then
    echo "✅ SUPABASE_HOST: $SUPABASE_HOST"
else
    echo "❌ SUPABASE_HOST: Não configurada"
    ALL_OK=false
fi

echo ""

# ============================================
# 6. Verificar Arquivos Estáticos
# ============================================
echo "📋 6. Verificando arquivos estáticos..."
echo ""

if [ -d "staticfiles" ]; then
    STATIC_COUNT=$(find staticfiles -type f | wc -l)
    echo "✅ Arquivos estáticos: $STATIC_COUNT arquivos em staticfiles/"
else
    echo "⚠️  Pasta staticfiles não encontrada"
    echo "Execute: python manage.py collectstatic --noinput"
fi

echo ""

# ============================================
# 7. Teste de Sistema
# ============================================
echo "📋 7. Executando system check do Django..."
echo ""

CHECK_OUTPUT=$(python manage.py check 2>&1)

if echo "$CHECK_OUTPUT" | grep -q "System check identified no issues"; then
    echo "✅ System check: Sem problemas"
else
    echo "⚠️  System check encontrou problemas:"
    echo "$CHECK_OUTPUT"
    ALL_OK=false
fi

echo ""

# ============================================
# 8. Resumo de Dados
# ============================================
echo "📋 8. Resumo dos dados no sistema..."
echo ""

echo "📊 Contagem de registros:"
python manage.py shell <<EOF
from empresas.models import Empresa
from usuarios.models import Usuario
from funcionarios.models import Funcionario
from lancamentos.models import Lancamento

print(f"  → Empresas: {Empresa.objects.count()}")
print(f"  → Usuários: {Usuario.objects.count()}")
print(f"  → Funcionários: {Funcionario.objects.count()}")
print(f"  → Lançamentos: {Lancamento.objects.count()}")
EOF

echo ""

# ============================================
# 9. Teste de URL Principal
# ============================================
echo "📋 9. Testando URLs principais..."
echo ""

# Teste interno (dentro do container)
HOME_TEST=$(python -c "
import sys
sys.path.insert(0, '.')
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fgtsweb.settings')
import django
django.setup()

from django.test import Client
client = Client()
try:
    response = client.get('/')
    print(f'OK:{response.status_code}')
except Exception as e:
    print(f'ERROR:{e}')
" 2>&1)

if echo "$HOME_TEST" | grep -q "OK:"; then
    STATUS=$(echo "$HOME_TEST" | grep "OK:" | cut -d: -f2)
    if [ "$STATUS" -lt 400 ]; then
        echo "✅ URL /: Status $STATUS"
    else
        echo "⚠️  URL /: Status $STATUS (erro)"
    fi
else
    echo "❌ URL /: Erro ao testar"
fi

echo ""

# ============================================
# RESULTADO FINAL
# ============================================
echo "=========================================="
if [ "$ALL_OK" = true ]; then
    echo "✅ TODAS AS VERIFICAÇÕES PASSARAM!"
    echo "=========================================="
    echo ""
    echo "🎉 Sistema pronto para uso!"
    echo ""
    echo "📋 Próximos testes manuais:"
    echo "  1. Acesse: http://fgts.bildee.com.br"
    echo "  2. Registre um novo usuário"
    echo "  3. Faça login"
    echo "  4. Crie uma empresa"
    echo "  5. Adicione um funcionário"
    echo "  6. Registre um lançamento"
    echo ""
else
    echo "⚠️  ALGUMAS VERIFICAÇÕES FALHARAM"
    echo "=========================================="
    echo ""
    echo "Revise os itens marcados com ❌ ou ⚠️  acima"
    echo ""
fi

# ============================================
# Informações Adicionais
# ============================================
echo "📊 Informações do Sistema:"
echo ""
echo "  → Python: $(python --version)"
echo "  → Django: $(python -c 'import django; print(django.get_version())')"
echo "  → Servidor: $(hostname)"
echo "  → Data/Hora: $(date)"
echo ""

# ============================================
# Logs Recentes
# ============================================
echo "📋 Últimas 10 linhas de log (se disponível):"
echo ""
if [ -f "logs/django.log" ]; then
    tail -n 10 logs/django.log
else
    echo "  (Arquivo de log não encontrado)"
fi

echo ""
echo "=========================================="
echo "✅ Verificação concluída!"
echo ""
