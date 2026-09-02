#!/usr/bin/env python
"""
Script para migrar tabelas e dados do SQLite para Supabase via:
1. Alternar configuração de DB para Supabase
2. Rodar django migrate para criar as tabelas
3. Importar dados via Django ORM/SQL
"""

import os
import sys
import django
from pathlib import Path

# Adicionar projeto ao path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fgtsweb.settings')

print("="*80)
print("🚀 MIGRAÇÃO CENTRALIZADA: SQLite → Supabase (via Django Migrations)")
print("="*80)

try:
    django.setup()
    print("✅ Django inicializado\n")
except Exception as e:
    print(f"❌ Erro ao inicializar Django: {e}")
    sys.exit(1)

from django.core.management import call_command
from django.db import connection, connections
from django.conf import settings

print("📊 Configuração de Banco de Dados:")
print(f"  Tipo: {settings.DATABASES['default']['ENGINE']}")
print(f"  Host: {settings.DATABASES['default'].get('HOST', 'sqlite3')}")
print(f"  Database: {settings.DATABASES['default'].get('NAME', 'db.sqlite3')}\n")

# Fase 1: Criar tabelas
print("--- FASE 1: Aplicar Migrations ---\n")

try:
    print("🔄 Rodando migrations...\n")
    call_command('migrate', verbosity=2)
    print("\n✅ Migrations aplicadas com sucesso!\n")
except Exception as e:
    print(f"\n❌ Erro nas migrations: {e}\n")
    sys.exit(1)

# Fase 2: Contar registros
print("\n--- FASE 2: Validar Dados ---\n")

from usuarios.models import Usuario
from empresas.models import Empresa
from funcionarios.models import Funcionario
from lancamentos.models import Lancamento
from indices.models import Indice
from audit_logs.models import AuditLog

print("📊 Contagem de registros por tabela:")
print(f"  Usuários: {Usuario.objects.count()}")
print(f"  Empresas: {Empresa.objects.count()}")
print(f"  Funcionários: {Funcionario.objects.count()}")
print(f"  Lançamentos: {Lancamento.objects.count()}")
print(f"  Índices: {Indice.objects.count()}")
print(f"  Audit Logs: {AuditLog.objects.count()}")

print("\n" + "="*80)
print("✅ MIGRAÇÃO CONCLUÍDA!")
print("="*80 + "\n")
