import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

print("Testando criação de tabela no Supabase...")
print("="*70)

try:
    # Conectar ao PostgreSQL COM SSL DESABILIDADO
    conn = psycopg2.connect(
        host=os.getenv('SUPABASE_HOST'),
        database=os.getenv('SUPABASE_DB'),
        user=os.getenv('SUPABASE_USER'),
        password=os.getenv('SUPABASE_PASSWORD'),
        port=int(os.getenv('SUPABASE_PORT', 5432)),
        sslmode='disable'  # Tentar sem SSL primeiro
    )
    
    cursor = conn.cursor()
    
    # Criar tabela de teste simples
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS teste_tabela (
        id SERIAL PRIMARY KEY,
        nome VARCHAR(255) NOT NULL,
        criada_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
    
    print("✅ Conexão estabelecida!")
    print("="*70)
    print("\nCriando tabela de teste...")
    
    cursor.execute(create_table_sql)
    conn.commit()
    
    print("✅ Tabela 'teste_tabela' criada com sucesso!")
    
    # Listar tabelas
    cursor.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public'
        ORDER BY table_name;
    """)
    
    tables = cursor.fetchall()
    print(f"\n📊 Total de tabelas: {len(tables)}")
    print("\nTabelas no banco:")
    for table in tables:
        print(f"  - {table[0]}")
    
    cursor.close()
    conn.close()
    
    print("\n" + "="*70)
    print("✅ SUCESSO! PostgreSQL está funcionando!")
    
except Exception as e:
    print(f"❌ ERRO: {e}")
    print("\nCredenciais configuradas:")
    print(f"  Host: {os.getenv('SUPABASE_HOST')}")
    print(f"  Database: {os.getenv('SUPABASE_DB')}")
    print(f"  User: {os.getenv('SUPABASE_USER')}")
    print(f"  Port: {os.getenv('SUPABASE_PORT')}")
