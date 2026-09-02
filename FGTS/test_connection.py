import os
from dotenv import load_dotenv
import psycopg2

load_dotenv()

print("Testando conexão com PostgreSQL Supabase...")
print("="*70)

try:
    conn = psycopg2.connect(
        host=os.getenv('SUPABASE_HOST'),
        database=os.getenv('SUPABASE_DB'),
        user=os.getenv('SUPABASE_USER'),
        password=os.getenv('SUPABASE_PASSWORD'),
        port=int(os.getenv('SUPABASE_PORT', 5432))
    )
    
    print("✅ Conexão PostgreSQL OK!")
    print("="*70)
    
    cursor = conn.cursor()
    cursor.execute('SELECT version();')
    version = cursor.fetchone()[0]
    print(f"Versão PostgreSQL: {version}")
    
    cursor.execute('SELECT current_database();')
    database = cursor.fetchone()[0]
    print(f"Database conectado: {database}")
    
    cursor.close()
    conn.close()
    
    print("="*70)
    print("✅ SUCESSO! PostgreSQL está pronto para uso!")
    
except Exception as e:
    print(f"❌ ERRO ao conectar: {e}")
    print("\nCredenciais configuradas:")
    print(f"  Host: {os.getenv('SUPABASE_HOST')}")
    print(f"  Database: {os.getenv('SUPABASE_DB')}")
    print(f"  User: {os.getenv('SUPABASE_USER')}")
    print(f"  Port: {os.getenv('SUPABASE_PORT')}")
    print(f"  Password: {'*' * len(os.getenv('SUPABASE_PASSWORD', ''))}")
