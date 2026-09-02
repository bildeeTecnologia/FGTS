"""
Script completo de diagnóstico Supabase
Testa: REST API, RPC, e conexão Postgres
"""
import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')

print("=" * 80)
print("DIAGNÓSTICO COMPLETO SUPABASE")
print("=" * 80)

print(f"\nSUPABASE_URL: {SUPABASE_URL}")
print(f"SUPABASE_KEY (primeiros 20 chars): {SUPABASE_KEY[:20] if SUPABASE_KEY else 'NÃO DEFINIDA'}...")

# =============================================================================
# TESTE 1: REST API - Health Check
# =============================================================================
print("\n" + "=" * 80)
print("TESTE 1: REST API - Health Check")
print("=" * 80)

try:
    response = requests.get(
        f"{SUPABASE_URL}/rest/v1/",
        headers={
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}"
        },
        timeout=10
    )
    print(f"Status: {response.status_code}")
    print(f"Headers: {dict(response.headers)}")
    print(f"Body: {response.text[:500]}")
except Exception as e:
    print(f"ERRO: {e}")

# =============================================================================
# TESTE 2: Listar tabelas via REST
# =============================================================================
print("\n" + "=" * 80)
print("TESTE 2: Tentar listar tabelas existentes")
print("=" * 80)

tabelas_teste = [
    'usuarios_usuario',
    'empresas_empresa',
    'funcionarios_funcionario',
    'lancamentos_lancamento',
    'indices_indice',
    'billing_subscription',
    'audit_logs_auditlog'
]

for tabela in tabelas_teste:
    try:
        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/{tabela}?select=count",
            headers={
                "apikey": SUPABASE_KEY,
                "Authorization": f"Bearer {SUPABASE_KEY}",
                "Prefer": "count=exact"
            },
            timeout=5
        )
        print(f"\n{tabela}: {response.status_code}")
        if response.status_code == 200:
            print(f"  ✓ Tabela existe")
        elif response.status_code == 404:
            print(f"  ✗ Tabela NÃO existe")
        else:
            print(f"  ? Status inesperado: {response.text[:200]}")
    except Exception as e:
        print(f"\n{tabela}: ERRO - {e}")

# =============================================================================
# TESTE 3: RPC - Criar tabela simples via SQL
# =============================================================================
print("\n" + "=" * 80)
print("TESTE 3: RPC - Executar SQL simples")
print("=" * 80)

sql_teste = """
CREATE TABLE IF NOT EXISTS teste_diagnostico (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(100),
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

try:
    response = requests.post(
        f"{SUPABASE_URL}/rest/v1/rpc/exec",
        headers={
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}",
            "Content-Type": "application/json"
        },
        json={"query": sql_teste},
        timeout=10
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"ERRO: {e}")

# =============================================================================
# TESTE 4: Verificar schema público
# =============================================================================
print("\n" + "=" * 80)
print("TESTE 4: Verificar information_schema via RPC")
print("=" * 80)

try:
    response = requests.post(
        f"{SUPABASE_URL}/rest/v1/rpc/exec",
        headers={
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "query": "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' ORDER BY table_name"
        },
        timeout=10
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"ERRO: {e}")

# =============================================================================
# TESTE 5: Testar conexão Postgres direta
# =============================================================================
print("\n" + "=" * 80)
print("TESTE 5: Conexão Postgres Direta")
print("=" * 80)

try:
    import psycopg2
    
    SUPABASE_HOST = os.getenv('SUPABASE_HOST')
    SUPABASE_DB = os.getenv('SUPABASE_DB')
    SUPABASE_USER = os.getenv('SUPABASE_USER')
    SUPABASE_PASSWORD = os.getenv('SUPABASE_PASSWORD')
    
    print(f"Host: {SUPABASE_HOST}")
    print(f"Database: {SUPABASE_DB}")
    print(f"User: {SUPABASE_USER}")
    print(f"Password: {'***' if SUPABASE_PASSWORD else 'NÃO DEFINIDA'}")
    
    if SUPABASE_HOST and SUPABASE_DB and SUPABASE_USER and SUPABASE_PASSWORD:
        conn = psycopg2.connect(
            host=SUPABASE_HOST,
            database=SUPABASE_DB,
            user=SUPABASE_USER,
            password=SUPABASE_PASSWORD,
            port=5432,
            connect_timeout=10
        )
        print("✓ Conexão Postgres estabelecida!")
        
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        print(f"PostgreSQL Version: {version[0]}")
        
        cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' ORDER BY table_name;")
        tabelas = cursor.fetchall()
        print(f"\nTabelas existentes ({len(tabelas)}):")
        for tabela in tabelas:
            print(f"  - {tabela[0]}")
        
        cursor.close()
        conn.close()
    else:
        print("✗ Credenciais Postgres incompletas no .env")
        
except ImportError:
    print("psycopg2 não instalado")
except Exception as e:
    print(f"ERRO Postgres: {type(e).__name__}: {e}")

# =============================================================================
# RESUMO
# =============================================================================
print("\n" + "=" * 80)
print("RESUMO DO DIAGNÓSTICO")
print("=" * 80)
print("\nPróximos passos:")
print("1. Se REST API funciona (200) mas RPC falha (404) → use SQL Editor manual")
print("2. Se Postgres direto funciona → use migrate com psycopg2")
print("3. Se tudo falha → verifique credenciais e status do projeto Supabase")
