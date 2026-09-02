#!/bin/bash
# ============================================
# Script de inicialização automática - Coolify
# ============================================
# Executa automaticamente no deploy:
# - Verifica conexão com banco
# - Aplica migrações
# - Coleta arquivos estáticos
# - Cria superuser (se necessário)
# - Inicia servidor
# ============================================

set -e  # Parar em caso de erro

echo "🚀 Iniciando aplicação FGTS Web..."
echo "=========================================="

# ============================================
# 1. Verificar conexão com banco de dados
# ============================================
echo ""
echo "📋 1. Verificando conexão com banco de dados..."

MAX_RETRIES=30
RETRY_COUNT=0

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if python manage.py check --database default > /dev/null 2>&1; then
        echo "✅ Banco de dados: Conectado"
        break
    else
        RETRY_COUNT=$((RETRY_COUNT + 1))
        echo "⏳ Aguardando banco... ($RETRY_COUNT/$MAX_RETRIES)"
        sleep 2
    fi
done

if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
    echo "❌ Não foi possível conectar ao banco de dados após $MAX_RETRIES tentativas"
    echo "Verifique as variáveis de ambiente SUPABASE_*"
    exit 1
fi

# ============================================
# 2. Aplicar migrações
# ============================================
echo ""
echo "📋 2. Aplicando migrações..."

python manage.py migrate --noinput

if [ $? -eq 0 ]; then
    echo "✅ Migrações: Aplicadas com sucesso"
else
    echo "❌ Erro ao aplicar migrações"
    exit 1
fi

# ============================================
# 3. Coletar arquivos estáticos
# ============================================
echo ""
echo "📋 3. Coletando arquivos estáticos..."

python manage.py collectstatic --noinput

if [ $? -eq 0 ]; then
    echo "✅ Arquivos estáticos: Coletados"
else
    echo "⚠️  Aviso: Erro ao coletar arquivos estáticos (não crítico)"
fi

# ============================================
# 4. Criar superuser padrão (se não existir)
# ============================================
echo ""
echo "📋 4. Verificando superuser..."

python manage.py shell << EOF
from usuarios.models import Usuario
if not Usuario.objects.filter(username='admin').exists():
    Usuario.objects.create_superuser('admin', 'admin@example.com', 'senha123')
    print('✅ Superuser criado: admin/senha123')
else:
    print('ℹ️  Superuser já existe')
EOF

# ============================================
# 5. Informações do sistema
# ============================================
echo ""
echo "📊 Informações do sistema:"
echo "  → Python: $(python --version)"
echo "  → Django: $(DJANGO_SETTINGS_MODULE=fgtsweb.settings python -c 'import django; print(django.get_version())')"

# Verificar qual banco está sendo usado (usar POSIX sh)
DB_ENGINE=$(DJANGO_SETTINGS_MODULE=fgtsweb.settings python -c "from django.conf import settings; print(settings.DATABASES['default']['ENGINE'])")
case "$DB_ENGINE" in
    *postgresql*)
        echo "  → Banco: PostgreSQL/Supabase ✅"
        ;;
    *sqlite*)
        echo "  → Banco: SQLite ⚠️  (deveria ser PostgreSQL em produção)"
        ;;
    *)
        echo "  → Banco: $DB_ENGINE"
        ;;
esac

# ============================================
# 6. Iniciar servidor
# ============================================
echo ""
echo "=========================================="
echo "✅ Iniciando servidor Gunicorn..."
echo "=========================================="
echo ""

# Inicia Gunicorn
# - bind 0.0.0.0:8000 = Escuta em todas as interfaces
# - workers 2 = 2 processos worker (otimizado para VPS)
# - timeout 120 = Timeout de 120 segundos para requests longos
# - access-logfile - = Log de acesso no stdout
# - error-logfile - = Log de erro no stdout
# - log-level info = Nível de log informativo

exec gunicorn \
    --bind 0.0.0.0:8000 \
    --workers 2 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile - \
    --log-level info \
    fgtsweb.wsgi:application
