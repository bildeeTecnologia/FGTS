import os
import json
from dotenv import load_dotenv
import requests

load_dotenv()

SUPABASE_URL = os.getenv('SUPABASE_URL').rstrip('/')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')

HEADERS = {
    'apikey': SUPABASE_KEY,
    'Authorization': f'Bearer {SUPABASE_KEY}',
    'Content-Type': 'application/json'
}

# SQL DDL para criar as tabelas (gerado a partir dos modelos Django)
CREATE_TABLES_SQL = """
-- Criar tabelas no Supabase
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
    FOREIGN KEY (empresa_id) REFERENCES empresas_empresa(id)
);

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
    FOREIGN KEY (empresa_id) REFERENCES empresas_empresa(id),
    FOREIGN KEY (funcionario_id) REFERENCES funcionarios_funcionario(id)
);

CREATE TABLE IF NOT EXISTS indices_indice (
    id SERIAL PRIMARY KEY,
    competencia VARCHAR(7),
    mes INTEGER,
    ano INTEGER,
    valor DECIMAL(15,6),
    criado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    atualizado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

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
    FOREIGN KEY (empresa_id) REFERENCES empresas_empresa(id)
);

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
    FOREIGN KEY (usuario_id) REFERENCES usuarios_usuario(id)
);

-- Criar índices para performance
CREATE INDEX IF NOT EXISTS idx_funcionarios_empresa ON funcionarios_funcionario(empresa_id);
CREATE INDEX IF NOT EXISTS idx_lancamentos_empresa ON lancamentos_lancamento(empresa_id);
CREATE INDEX IF NOT EXISTS idx_lancamentos_funcionario ON lancamentos_lancamento(funcionario_id);
CREATE INDEX IF NOT EXISTS idx_lancamentos_competencia ON lancamentos_lancamento(competencia);
CREATE INDEX IF NOT EXISTS idx_indices_competencia ON indices_indice(competencia);
CREATE INDEX IF NOT EXISTS idx_audit_usuario ON audit_logs_auditlog(usuario_id);
"""

def create_tables_via_sql():
    """Executa SQL DDL no Supabase via RPC function"""
    print("\n" + "="*80)
    print("🔨 CRIANDO TABELAS NO SUPABASE VIA SQL DDL")
    print("="*80 + "\n")
    
    # Dividir SQL em statements individuais
    statements = [s.strip() for s in CREATE_TABLES_SQL.split(';') if s.strip()]
    
    created = 0
    errors = 0
    
    for i, statement in enumerate(statements, 1):
        print(f"[{i}/{len(statements)}] Executando: {statement[:60]}...")
        
        try:
            # Tentar via RPC (Supabase pode ter função para executar SQL)
            # Se não funcionar, usar workaround criando via inserts
            response = requests.post(
                f"{SUPABASE_URL}/rest/v1/rpc/exec_sql",
                headers=HEADERS,
                json={"sql": statement},
                timeout=10
            )
            
            if response.status_code in [200, 201]:
                print(f"  ✅ OK\n")
                created += 1
            else:
                print(f"  ⚠️  Status {response.status_code}\n")
                errors += 1
                
        except Exception as e:
            print(f"  ❌ Erro: {str(e)[:80]}\n")
            errors += 1
    
    print("="*80)
    print(f"📊 Resultado: {created} statements OK, {errors} com erro")
    print("="*80 + "\n")
    
    return created, errors

if __name__ == "__main__":
    print(f"Supabase URL: {SUPABASE_URL}")
    create_tables_via_sql()
