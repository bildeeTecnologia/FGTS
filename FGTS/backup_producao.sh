#!/bin/bash
# ============================================
# SCRIPT DE BACKUP - SQLITE PRODUÇÃO
# ============================================
# Execute ANTES de migrar para Supabase
#
# Como usar no Coolify:
# 1. Vá no Terminal do container
# 2. Copie e cole este script completo
# 3. Salve o arquivo backup_producao.json gerado

echo "🔄 Iniciando backup do banco SQLite de produção..."
echo "=================================================="
echo ""

# Criar backup com timestamp
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="backup_producao_${TIMESTAMP}.json"

echo "📦 Fazendo dump de todos os dados..."
python manage.py dumpdata \
  --natural-foreign \
  --natural-primary \
  -e contenttypes \
  -e auth.Permission \
  --indent 2 \
  > "$BACKUP_FILE"

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Backup criado com sucesso!"
    echo "📄 Arquivo: $BACKUP_FILE"
    echo ""
    
    # Verificar tamanho do arquivo
    SIZE=$(ls -lh "$BACKUP_FILE" | awk '{print $5}')
    echo "📊 Tamanho do backup: $SIZE"
    
    # Contar registros por app
    echo ""
    echo "📈 Resumo dos dados exportados:"
    echo "================================"
    
    # Empresas
    EMPRESAS=$(python manage.py shell -c "from empresas.models import Empresa; print(Empresa.objects.count())" 2>/dev/null || echo "0")
    echo "  → Empresas: $EMPRESAS"
    
    # Usuários
    USUARIOS=$(python manage.py shell -c "from usuarios.models import Usuario; print(Usuario.objects.count())" 2>/dev/null || echo "0")
    echo "  → Usuários: $USUARIOS"
    
    # Funcionários
    FUNCIONARIOS=$(python manage.py shell -c "from funcionarios.models import Funcionario; print(Funcionario.objects.count())" 2>/dev/null || echo "0")
    echo "  → Funcionários: $FUNCIONARIOS"
    
    # Lançamentos
    LANCAMENTOS=$(python manage.py shell -c "from lancamentos.models import Lancamento; print(Lancamento.objects.count())" 2>/dev/null || echo "0")
    echo "  → Lançamentos: $LANCAMENTOS"
    
    echo ""
    echo "⚠️  IMPORTANTE: Guarde este arquivo em local seguro!"
    echo "💾 Download o arquivo $BACKUP_FILE antes de continuar"
    echo ""
    
else
    echo ""
    echo "❌ Erro ao criar backup!"
    echo "Verifique se o banco de dados está acessível"
    exit 1
fi

echo "=================================================="
echo "✅ Backup concluído!"
echo ""
echo "📋 Próximos passos:"
echo "  1. Download o arquivo $BACKUP_FILE"
echo "  2. Configure as variáveis do Supabase no Coolify"
echo "  3. Reinicie o container"
echo "  4. Execute o script de migração"
echo ""
