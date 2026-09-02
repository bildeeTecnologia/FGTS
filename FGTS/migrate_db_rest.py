import os
import json
import sqlite3
from datetime import datetime
from dotenv import load_dotenv
import requests

load_dotenv()

SUPABASE_URL = os.getenv('SUPABASE_URL').rstrip('/')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')
SQLITE_DB = 'db.sqlite3'

HEADERS = {
    'apikey': SUPABASE_KEY,
    'Authorization': f'Bearer {SUPABASE_KEY}',
    'Content-Type': 'application/json'
}

# Tabelas a migrar (na ordem de dependência)
TABLES_TO_MIGRATE = [
    'usuarios_usuario',
    'empresas_empresa',
    'funcionarios_funcionario',
    'coefjam_coeficientejam',
    'lancamentos_lancamento',
    'indices_indice',
    'billing_subscription',
    'audit_logs_auditlog',
]

def normalize_json(obj):
    """Converte tipos SQLite para JSON serializáveis"""
    if isinstance(obj, dict):
        return {k: normalize_json(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [normalize_json(item) for item in obj]
    elif isinstance(obj, bytes):
        return obj.decode('utf-8', errors='ignore')
    return obj

def export_table_from_sqlite(table_name):
    """Exporta uma tabela do SQLite"""
    try:
        conn = sqlite3.connect(SQLITE_DB)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute(f"SELECT * FROM {table_name}")
        rows = cursor.fetchall()
        conn.close()
        
        data = [dict(row) for row in rows]
        return data
    except Exception as e:
        print(f"  ⚠️  Erro ao exportar {table_name}: {e}")
        return []

def import_to_supabase(table_name, data):
    """Importa dados para o Supabase via REST API"""
    if not data:
        print(f"  ℹ️  Nenhum dado para {table_name}")
        return 0
    
    url = f"{SUPABASE_URL}/rest/v1/{table_name}"
    
    success_count = 0
    error_count = 0
    
    # Tentar inserir em batch (até 1000 registros por vez)
    batch_size = 100
    for i in range(0, len(data), batch_size):
        batch = data[i:i+batch_size]
        
        try:
            response = requests.post(
                url,
                headers={**HEADERS, 'Prefer': 'resolution=ignore-duplicates'},
                json=batch,
                timeout=30
            )
            
            if response.status_code in [201, 200]:
                success_count += len(batch)
                print(f"  ✅ {len(batch)} registros inseridos")
            else:
                error_count += len(batch)
                print(f"  ❌ Erro {response.status_code}: {response.text[:100]}")
        except Exception as e:
            error_count += len(batch)
            print(f"  ❌ Erro de conexão: {str(e)[:100]}")
    
    return success_count

def main():
    print("\n" + "="*80)
    print("🚀 MIGRAÇÃO SQLite → Supabase REST API")
    print("="*80)
    
    print(f"\n📊 Configuração:")
    print(f"  SQLite DB: {SQLITE_DB}")
    print(f"  Supabase URL: {SUPABASE_URL}")
    print(f"  Tabelas a migrar: {len(TABLES_TO_MIGRATE)}")
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = f"migration_backup_{timestamp}.json"
    
    total_records = 0
    migration_data = {}
    
    print(f"\n--- FASE 1: Exportar do SQLite ---\n")
    
    for table_name in TABLES_TO_MIGRATE:
        print(f"📤 Exportando {table_name}...")
        data = export_table_from_sqlite(table_name)
        migration_data[table_name] = data
        total_records += len(data)
        print(f"  ✅ {len(data)} registros exportados\n")
    
    # Salvar backup
    print(f"💾 Salvando backup em {backup_file}...")
    with open(backup_file, 'w', encoding='utf-8') as f:
        json.dump(migration_data, f, default=str, indent=2)
    print(f"  ✅ Backup salvo\n")
    
    print(f"--- FASE 2: Importar para Supabase ---\n")
    
    total_imported = 0
    
    for table_name in TABLES_TO_MIGRATE:
        data = migration_data.get(table_name, [])
        print(f"📥 Importando {table_name}...")
        
        imported = import_to_supabase(table_name, data)
        total_imported += imported
        print()
    
    print("="*80)
    print(f"✅ MIGRAÇÃO CONCLUÍDA!")
    print(f"  📊 Total de registros exportados: {total_records}")
    print(f"  ✅ Total de registros importados: {total_imported}")
    print(f"  💾 Backup: {backup_file}")
    print("="*80 + "\n")

if __name__ == "__main__":
    main()
