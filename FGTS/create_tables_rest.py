"""
Cria tabelas diretamente no Supabase via REST API usando SQL
"""
import os
import requests
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')

# SQL das tabelas (ordem respeitando FKs)
TABLES_SQL = [
    # 1. Empresas (sem FK)
    """
    CREATE TABLE IF NOT EXISTS empresas_empresa (
        id SERIAL PRIMARY KEY,
        razao_social VARCHAR(255) NOT NULL,
        nome_fantasia VARCHAR(255),
        cnpj VARCHAR(20) UNIQUE,
        ie VARCHAR(30),
        endereco VARCHAR(255),
        numero VARCHAR(10),
        complemento VARCHAR(255),
        bairro VARCHAR(100),
        cidade VARCHAR(100),
        estado VARCHAR(2),
        cep VARCHAR(9),
        telefone VARCHAR(20),
        email VARCHAR(254),
        responsavel VARCHAR(150),
        ativa BOOLEAN NOT NULL DEFAULT TRUE,
        criada_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        atualizada_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
    );
    """,
    
    # 2. Usuarios (FK empresa_id mas sem constraint)
    """
    CREATE TABLE IF NOT EXISTS usuarios_usuario (
        id SERIAL PRIMARY KEY,
        password VARCHAR(128) NOT NULL,
        last_login TIMESTAMP,
        is_superuser BOOLEAN NOT NULL DEFAULT FALSE,
        username VARCHAR(150) NOT NULL UNIQUE,
        first_name VARCHAR(150),
        last_name VARCHAR(150),
        email VARCHAR(254),
        is_staff BOOLEAN NOT NULL DEFAULT FALSE,
        is_active BOOLEAN NOT NULL DEFAULT TRUE,
        date_joined TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        empresa_id INTEGER
    );
    """,
    
    # 3. Funcionarios (FK empresa_id)
    """
    CREATE TABLE IF NOT EXISTS funcionarios_funcionario (
        id SERIAL PRIMARY KEY,
        empresa_id INTEGER NOT NULL,
        nome VARCHAR(255) NOT NULL,
        cpf VARCHAR(14) UNIQUE,
        data_nascimento DATE,
        genero VARCHAR(1),
        email VARCHAR(254),
        telefone VARCHAR(20),
        endereco VARCHAR(255),
        numero VARCHAR(10),
        complemento VARCHAR(255),
        bairro VARCHAR(100),
        cidade VARCHAR(100),
        estado VARCHAR(2),
        cep VARCHAR(9),
        data_admissao DATE,
        cargo VARCHAR(100),
        salario DECIMAL(15,2),
        ativo BOOLEAN NOT NULL DEFAULT TRUE,
        criado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        atualizado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        CONSTRAINT fk_funcionario_empresa FOREIGN KEY (empresa_id) REFERENCES empresas_empresa(id) ON DELETE CASCADE
    );
    """,
    
    # 4. Lancamentos (FKs empresa_id e funcionario_id)
    """
    CREATE TABLE IF NOT EXISTS lancamentos_lancamento (
        id SERIAL PRIMARY KEY,
        empresa_id INTEGER NOT NULL,
        funcionario_id INTEGER NOT NULL,
        competencia VARCHAR(7),
        mes_referencia INTEGER,
        ano_referencia INTEGER,
        valor_fgts DECIMAL(15,2),
        valor_multa DECIMAL(15,2),
        pago BOOLEAN NOT NULL DEFAULT FALSE,
        data_pagamento DATE,
        criado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        atualizado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        CONSTRAINT fk_lancamento_empresa FOREIGN KEY (empresa_id) REFERENCES empresas_empresa(id) ON DELETE CASCADE,
        CONSTRAINT fk_lancamento_funcionario FOREIGN KEY (funcionario_id) REFERENCES funcionarios_funcionario(id) ON DELETE CASCADE
    );
    """,
    
    # 5. Indices (sem FK)
    """
    CREATE TABLE IF NOT EXISTS indices_indice (
        id SERIAL PRIMARY KEY,
        competencia VARCHAR(7),
        mes INTEGER,
        ano INTEGER,
        valor DECIMAL(15,6),
        criado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        atualizado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
    );
    """,
    
    # 6. Billing (FK empresa_id)
    """
    CREATE TABLE IF NOT EXISTS billing_subscription (
        id SERIAL PRIMARY KEY,
        empresa_id INTEGER NOT NULL,
        plano VARCHAR(50),
        status VARCHAR(20),
        data_inicio DATE,
        data_fim DATE,
        valor_mensal DECIMAL(15,2),
        criada_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        atualizada_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        CONSTRAINT fk_subscription_empresa FOREIGN KEY (empresa_id) REFERENCES empresas_empresa(id) ON DELETE CASCADE
    );
    """,
    
    # 7. Audit Logs (FK usuario_id)
    """
    CREATE TABLE IF NOT EXISTS audit_logs_auditlog (
        id SERIAL PRIMARY KEY,
        usuario_id INTEGER,
        acao VARCHAR(50),
        tabela VARCHAR(100),
        registro_id INTEGER,
        dados_antigos TEXT,
        dados_novos TEXT,
        endereco_ip VARCHAR(45),
        user_agent TEXT,
        criado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        CONSTRAINT fk_auditlog_usuario FOREIGN KEY (usuario_id) REFERENCES usuarios_usuario(id) ON DELETE SET NULL
    );
    """
]

INDEXES_SQL = """
CREATE INDEX IF NOT EXISTS idx_usuarios_empresa ON usuarios_usuario(empresa_id);
CREATE INDEX IF NOT EXISTS idx_usuarios_username ON usuarios_usuario(username);
CREATE INDEX IF NOT EXISTS idx_empresas_cnpj ON empresas_empresa(cnpj);
CREATE INDEX IF NOT EXISTS idx_empresas_ativa ON empresas_empresa(ativa);
CREATE INDEX IF NOT EXISTS idx_funcionarios_empresa ON funcionarios_funcionario(empresa_id);
CREATE INDEX IF NOT EXISTS idx_funcionarios_cpf ON funcionarios_funcionario(cpf);
CREATE INDEX IF NOT EXISTS idx_funcionarios_ativo ON funcionarios_funcionario(ativo);
CREATE INDEX IF NOT EXISTS idx_lancamentos_empresa ON lancamentos_lancamento(empresa_id);
CREATE INDEX IF NOT EXISTS idx_lancamentos_funcionario ON lancamentos_lancamento(funcionario_id);
CREATE INDEX IF NOT EXISTS idx_lancamentos_competencia ON lancamentos_lancamento(competencia);
CREATE INDEX IF NOT EXISTS idx_lancamentos_pago ON lancamentos_lancamento(pago);
CREATE INDEX IF NOT EXISTS idx_lancamentos_empresa_competencia ON lancamentos_lancamento(empresa_id, competencia);
CREATE INDEX IF NOT EXISTS idx_indices_competencia ON indices_indice(competencia);
CREATE INDEX IF NOT EXISTS idx_indices_mes_ano ON indices_indice(mes, ano);
CREATE INDEX IF NOT EXISTS idx_billing_empresa ON billing_subscription(empresa_id);
CREATE INDEX IF NOT EXISTS idx_billing_status ON billing_subscription(status);
CREATE INDEX IF NOT EXISTS idx_audit_usuario ON audit_logs_auditlog(usuario_id);
CREATE INDEX IF NOT EXISTS idx_audit_tabela ON audit_logs_auditlog(tabela);
CREATE INDEX IF NOT EXISTS idx_audit_criado_em ON audit_logs_auditlog(criado_em);
"""

print("=" * 80)
print("CRIANDO TABELAS NO SUPABASE VIA REST API")
print("=" * 80)

# Tenta via query direta (alguns Supabase suportam)
headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json"
}

# Método 1: Tentar via RPC query
print("\nMétodo 1: Tentando via RPC query...")
for i, sql in enumerate(TABLES_SQL, 1):
    table_name = sql.split("CREATE TABLE IF NOT EXISTS ")[1].split()[0]
    print(f"\n{i}. Criando {table_name}...")
    
    try:
        response = requests.post(
            f"{SUPABASE_URL}/rest/v1/rpc/query",
            headers=headers,
            json={"query": sql},
            timeout=30
        )
        
        if response.status_code == 200:
            print(f"   ✓ {table_name} criada com sucesso!")
        else:
            print(f"   ✗ Erro {response.status_code}: {response.text[:200]}")
    except Exception as e:
        print(f"   ✗ Exceção: {e}")

# Criar índices
print(f"\n8. Criando índices...")
try:
    response = requests.post(
        f"{SUPABASE_URL}/rest/v1/rpc/query",
        headers=headers,
        json={"query": INDEXES_SQL},
        timeout=30
    )
    
    if response.status_code == 200:
        print(f"   ✓ Índices criados com sucesso!")
    else:
        print(f"   ✗ Erro {response.status_code}: {response.text[:200]}")
except Exception as e:
    print(f"   ✗ Exceção: {e}")

# Verificar tabelas criadas
print("\n" + "=" * 80)
print("VERIFICANDO TABELAS CRIADAS")
print("=" * 80)

tabelas = [
    'usuarios_usuario',
    'empresas_empresa',
    'funcionarios_funcionario',
    'lancamentos_lancamento',
    'indices_indice',
    'billing_subscription',
    'audit_logs_auditlog'
]

for tabela in tabelas:
    try:
        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/{tabela}?select=count",
            headers=headers,
            timeout=5
        )
        
        if response.status_code == 200:
            print(f"✓ {tabela} - EXISTE")
        elif response.status_code == 404:
            print(f"✗ {tabela} - NÃO EXISTE")
        else:
            print(f"? {tabela} - Status {response.status_code}")
    except Exception as e:
        print(f"✗ {tabela} - Erro: {e}")

print("\n" + "=" * 80)
print("Se todas as tabelas mostrarem 'NÃO EXISTE', você precisa criá-las")
print("manualmente no SQL Editor do Supabase Dashboard.")
print("=" * 80)
