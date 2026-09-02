import sqlite3

conn = sqlite3.connect('db.sqlite3')
cursor = conn.cursor()

# Tabelas relevantes
tables = [
    'usuarios_usuario',
    'empresas_empresa', 
    'funcionarios_funcionario',
    'lancamentos_lancamento',
    'indices_indice',
    'billing_subscription',
    'audit_logs_auditlog'
]

for table in tables:
    cursor.execute(f'PRAGMA table_info({table})')
    cols = cursor.fetchall()
    print(f'\n{table}:')
    for col in cols:
        print(f'  {col[1]:30s} {col[2]:20s}')

conn.close()
