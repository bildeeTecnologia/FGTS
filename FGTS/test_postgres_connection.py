import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

try:
    conn = psycopg2.connect(
        host=os.getenv('SUPABASE_HOST'),
        database=os.getenv('SUPABASE_DB'),
        user=os.getenv('SUPABASE_USER'),
        password=os.getenv('SUPABASE_PASSWORD'),
        port=int(os.getenv('SUPABASE_PORT', 5432)),
        connect_timeout=10
    )
    
    cursor = conn.cursor()
    cursor.execute('SELECT version();')
    version = cursor.fetchone()[0]
    print('✅ CONEXÃO POSTGRESQL ESTABELECIDA!')
    print(f'PostgreSQL: {version.split(",")[0]}')
    
    cursor.execute('SELECT COUNT(*) FROM usuarios_usuario;')
    users = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM empresas_empresa;')
    empresas = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM funcionarios_funcionario;')
    funcs = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM lancamentos_lancamento;')
    lancamentos = cursor.fetchone()[0]
    
    print(f'\n✅ Dados no Supabase PostgreSQL:')
    print(f'  - Usuários: {users}')
    print(f'  - Empresas: {empresas}')
    print(f'  - Funcionários: {funcs}')
    print(f'  - Lançamentos: {lancamentos}')
    
    cursor.close()
    conn.close()
except Exception as e:
    print(f'❌ ERRO: {type(e).__name__}: {str(e)[:100]}')
