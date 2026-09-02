"""
Script para ajustar o código inicial das empresas para começar em 1000
Execute este script uma única vez após a implantação
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fgtsweb.settings')
django.setup()

from django.db import connection
from empresas.models import Empresa

def set_empresa_codigo_start():
    """Define o próximo código de empresa para começar em 1000"""
    
    # Verificar se já existem empresas
    max_codigo = Empresa.objects.all().aggregate(max_codigo=models.Max('codigo'))['max_codigo']
    
    if max_codigo is None:
        # Nenhuma empresa cadastrada, setar para 1000
        next_value = 1000
    elif max_codigo < 1000:
        # Existem empresas mas com código menor que 1000
        next_value = 1000
    else:
        # Já existem empresas com código >= 1000
        next_value = max_codigo + 1
    
    # Ajustar a sequência do PostgreSQL ou SQLite
    with connection.cursor() as cursor:
        # Para SQLite
        if connection.vendor == 'sqlite':
            cursor.execute(
                f"UPDATE sqlite_sequence SET seq = {next_value - 1} WHERE name = 'empresas_empresa'"
            )
            print(f"✓ Sequência SQLite ajustada. Próximo código de empresa será: {next_value}")
        
        # Para PostgreSQL
        elif connection.vendor == 'postgresql':
            cursor.execute(
                f"SELECT setval('empresas_empresa_codigo_seq', {next_value - 1})"
            )
            print(f"✓ Sequência PostgreSQL ajustada. Próximo código de empresa será: {next_value}")
        
        else:
            print(f"⚠ Banco de dados {connection.vendor} não suportado neste script")
            return False
    
    print(f"\n✅ Configuração concluída!")
    print(f"   - Códigos de empresa começarão a partir de: {next_value}")
    print(f"   - Empresas existentes: {Empresa.objects.count()}")
    
    return True

if __name__ == '__main__':
    from django.db import models
    set_empresa_codigo_start()
