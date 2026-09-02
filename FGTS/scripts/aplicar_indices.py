#!/usr/bin/env python
"""
Script para aplicar migração de índices e validar performance
Executar: python manage.py shell < scripts/aplicar_indices.py
"""

import os
import sys
import django
from datetime import datetime
from decimal import Decimal

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fgtsweb.settings')
django.setup()

from django.db import connection
from django.core.management import call_command
import logging

logger = logging.getLogger(__name__)

def print_header(titulo):
    print("\n" + "="*80)
    print(f"  {titulo}")
    print("="*80)

def check_database_indices():
    """Verifica quais índices existem no banco"""
    with connection.cursor() as cursor:
        # Listar índices em lancamentos_lancamento
        cursor.execute("""
            SELECT indexname, indexdef
            FROM pg_indexes
            WHERE tablename IN ('lancamentos_lancamento', 'indices_fgts', 'coefjam_coefjam')
            ORDER BY tablename, indexname;
        """)
        indices = cursor.fetchall()
        
        print_header("📊 ÍNDICES EXISTENTES NO BANCO DE DADOS")
        
        if not indices:
            print("⚠️ Nenhum índice encontrado!")
            return False
        
        current_table = None
        for indexname, indexdef in indices:
            # Extrair nome da tabela do indexdef
            if 'lancamentos_lancamento' in indexdef:
                table = 'lancamentos_lancamento'
            elif 'indices_fgts' in indexdef:
                table = 'indices_fgts'
            elif 'coefjam_coefjam' in indexdef:
                table = 'coefjam_coefjam'
            else:
                table = 'unknown'
            
            if current_table != table:
                print(f"\n📌 Tabela: {table}")
                current_table = table
            
            print(f"  ✅ {indexname}")
        
        return len(indices) > 0

def get_table_sizes():
    """Obtém o tamanho das tabelas e seus índices"""
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT
                tablename,
                pg_size_pretty(pg_total_relation_size('public.' || tablename)) as total_size,
                pg_size_pretty(pg_relation_size('public.' || tablename)) as table_size,
                pg_size_pretty(
                    pg_total_relation_size('public.' || tablename) - pg_relation_size('public.' || tablename)
                ) as indexes_size
            FROM pg_tables
            WHERE tablename IN ('lancamentos_lancamento', 'indices_fgts', 'coefjam_coefjam')
            ORDER BY tablename;
        """)
        
        print_header("💾 TAMANHO DAS TABELAS")
        for tablename, total_size, table_size, indexes_size in cursor.fetchall():
            print(f"\n📋 {tablename}")
            print(f"   Total: {total_size:>12} | Tabela: {table_size:>12} | Índices: {indexes_size:>12}")

def get_index_stats():
    """Obtém estatísticas de uso dos índices"""
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT
                schemaname,
                tablename,
                indexname,
                idx_scan,
                idx_tup_read,
                idx_tup_fetch
            FROM pg_stat_user_indexes
            WHERE tablename IN ('lancamentos_lancamento', 'indices_fgts', 'coefjam_coefjam')
            ORDER BY tablename, idx_scan DESC;
        """)
        
        print_header("📈 ESTATÍSTICAS DE USO DOS ÍNDICES")
        
        current_table = None
        for schema, table, indexname, idx_scan, idx_tup_read, idx_tup_fetch in cursor.fetchall():
            if current_table != table:
                print(f"\n📌 {table}")
                current_table = table
            
            status = "🔥" if idx_scan > 100 else "✅" if idx_scan > 0 else "❌"
            print(f"   {status} {indexname}")
            print(f"      Scans: {idx_scan} | Tuples Read: {idx_tup_read} | Tuples Fetched: {idx_tup_fetch}")

def test_query_performance():
    """Testa a performance de queries críticas"""
    print_header("⏱️ TESTE DE PERFORMANCE DE QUERIES")
    
    with connection.cursor() as cursor:
        test_queries = [
            {
                'name': 'Buscar Lançamentos (empresa + competência + status)',
                'query': """
                    EXPLAIN ANALYZE
                    SELECT id, empresa_id, funcionario_id, competencia, valor_fgts, pago
                    FROM lancamentos_lancamento
                    WHERE empresa_id = 1 AND competencia = '01/2024' AND pago = false
                    LIMIT 10;
                """
            },
            {
                'name': 'Buscar Índices FGTS (competência + data)',
                'query': """
                    EXPLAIN ANALYZE
                    SELECT id, competencia, data_base, tabela, indice
                    FROM indices_fgts
                    WHERE competencia = '2024-01-01'::date AND data_base = '2026-01-19'::date
                    LIMIT 1;
                """
            },
            {
                'name': 'Buscar CoefJam por Competência',
                'query': """
                    EXPLAIN ANALYZE
                    SELECT id, data_pagamento, competencia, valor
                    FROM coefjam_coefjam
                    WHERE competencia = '01/2024'
                    LIMIT 1;
                """
            },
        ]
        
        for test in test_queries:
            print(f"\n🔍 {test['name']}")
            try:
                cursor.execute(test['query'])
                result = cursor.fetchall()
                
                # Procurar por "Seq Scan" ou "Index" no resultado
                for row in result:
                    row_str = str(row)
                    if 'Seq Scan' in row_str:
                        print("   ⚠️ Usando Sequential Scan (LENTO!)")
                    elif 'Index' in row_str:
                        print("   ✅ Usando Index (RÁPIDO!)")
                    
                    if 'Planning Time:' in row_str or 'Execution Time:' in row_str:
                        print(f"   📊 {row_str[:100]}...")
                        
            except Exception as e:
                print(f"   ❌ Erro ao executar: {str(e)}")

def main():
    print("\n")
    print("╔" + "═"*78 + "╗")
    print("║" + " "*20 + "🔧 SCRIPT DE INDEXAÇÃO SUPABASE" + " "*25 + "║")
    print("║" + " "*16 + f"Data: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}" + " "*40 + "║")
    print("╚" + "═"*78 + "╝")
    
    # 1. Aplicar migrações
    print_header("🚀 ETAPA 1: Aplicar Migrações")
    try:
        call_command('migrate', 'lancamentos')
        print("✅ Migração de lancamentos aplicada")
        
        call_command('migrate', 'indices')
        print("✅ Migração de indices aplicada")
        
        call_command('migrate', 'coefjam')
        print("✅ Migração de coefjam aplicada")
    except Exception as e:
        print(f"❌ Erro ao aplicar migrações: {str(e)}")
        return
    
    # 2. Verificar índices
    print_header("🔍 ETAPA 2: Verificar Índices Criados")
    check_database_indices()
    
    # 3. Ver tamanhos
    get_table_sizes()
    
    # 4. Ver estatísticas
    get_index_stats()
    
    # 5. Testar performance
    test_query_performance()
    
    # Resumo final
    print_header("✅ RESUMO FINAL")
    print("""
    ✅ Índices aplicados com sucesso!
    
    Próximos passos:
    1. Testar a página de relatórios (deve ser mais rápida)
    2. Se ainda lento, revisar logs no Supabase
    3. Monitorar uso dos índices nas próximas 24h
    
    Dicas:
    - Índices compostoseconomizam mais que simples
    - Não adicionar índice para cada coluna
    - Revisar EXPLAIN ANALYZE se query estiver lenta
    
    Referências:
    - Documento: INDEXACAO_SUPABASE.md
    - SQL direto: scripts/supabase_indexacao.sql
    """)

if __name__ == '__main__':
    main()
