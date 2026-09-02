"""
Detectar credenciais Supabase PostgreSQL do novo projeto
"""
import os
import re

# NÃO versionar tokens/chaves aqui.
# Informe via env:
# - SUPABASE_URL=https://<ref>.supabase.co
# - SUPABASE_KEY=<service_role_key>
jwt_token = os.getenv("SUPABASE_KEY", "")
api_url = os.getenv("SUPABASE_URL", "")

if not api_url:
	raise SystemExit("Defina SUPABASE_URL no ambiente (ex.: https://<ref>.supabase.co)")

# Extrair project ID do URL
project_id = re.search(r'https://(.+?)\.supabase\.co', api_url).group(1)

print("CREDENCIAIS SUPABASE DETECTADAS:")
print(f"Project ID: {project_id}")
print(f"Host: db.{project_id}.supabase.co")
print(f"Port: 5432")
print(f"Database: postgres")
print(f"User: postgres")
print(f"Password: (você precisa fornecer - gerada no painel)")
print()
print("Para encontrar a senha:")
print("1. Acesse: https://app.supabase.com/project/{}/settings/database".format(project_id))
print("2. Copie a 'Connection string' completa")
print("3. Ou use 'Reset password' para gerar uma nova")
