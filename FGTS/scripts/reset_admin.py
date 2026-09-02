"""
Script para resetar senha do admin
"""
import os
import sys
import django

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fgtsweb.settings')
django.setup()

from usuarios.models import Usuario

try:
    usuario = Usuario.objects.get(username='admin')
    usuario.set_password('admin123')
    usuario.save()
    print(f"✓ Senha resetada para: admin / admin123")
    print(f"✓ Usuário ativo: {usuario.is_active}")
    print(f"✓ Staff: {usuario.is_staff}")
    print(f"✓ Superuser: {usuario.is_superuser}")
except Usuario.DoesNotExist:
    print("✗ Usuário admin não encontrado!")
    print("Criando usuário admin...")
    usuario = Usuario.objects.create_superuser(
        username='admin',
        email='admin@fgts.com',
        password='admin123'
    )
    print(f"✓ Usuário criado: admin / admin123")
