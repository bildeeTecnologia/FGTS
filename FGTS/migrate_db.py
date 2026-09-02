import subprocess
import os
import sys
from datetime import datetime

def run_command(command, env=None, shell=True):
    print(f"Running: {command}")
    # If env is provided, use it. Otherwise use os.environ
    # We need to ensure we pass the full environment if we modify it
    if env is None:
        env = os.environ.copy()
        
    result = subprocess.run(command, env=env, shell=shell, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error running command: {command}")
        print(f"Return Code: {result.returncode}")
        print(f"Stderr: {result.stderr}")
        print(f"Stdout: {result.stdout}")
        return False
    print(result.stdout)
    return True

def main():
    print("Iniciando processo de migração SQLite -> Supabase...")
    
    # Determine Python executable
    python_exe = r".\.venv\Scripts\python.exe"
    if not os.path.exists(python_exe):
        python_exe = "python"
        print(f"Usando python do sistema: {python_exe}")
    else:
        print(f"Usando venv python: {python_exe}")

    # --- Step 1: Export from SQLite ---
    print("\n--- Passo 1: Exportando dados do SQLite ---")
    
    # Prepare environment for SQLite (unset Supabase vars)
    sqlite_env = os.environ.copy()
    # Set to empty string to prevent load_dotenv from overwriting them with .env values
    # and to ensure settings.py treats them as falsy.
    sqlite_env['SUPABASE_HOST'] = ''
    sqlite_env['SUPABASE_DB'] = ''
    sqlite_env['SUPABASE_USER'] = ''
    sqlite_env['SUPABASE_PASSWORD'] = ''
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    dump_file = f"backup_sqlite_{timestamp}.json"
    
    cmd_dump = (
        f'"{python_exe}" manage.py dumpdata '
        "--exclude auth.permission "
        "--exclude contenttypes "
        "--exclude sessions.session "
        "--exclude admin.logentry "
        "--exclude indices.SupabaseIndice "
        "--natural-foreign "
        "--indent 2 "
        f"-o {dump_file}"
    )
    
    if not run_command(cmd_dump, env=sqlite_env):
        print("FALHA na exportação. Abortando.")
        return

    print(f"Dados exportados com sucesso para: {dump_file}")

    # --- Step 2: Migrate Supabase ---
    print("\n--- Passo 2: Aplicando Migrations no Supabase ---")
    # Run with normal environment (manage.py will load .env)
    
    cmd_migrate = f'"{python_exe}" manage.py migrate'
    if not run_command(cmd_migrate):
        print("FALHA na migration. Abortando.")
        return

    # --- Step 3: Import to Supabase ---
    print("\n--- Passo 3: Importando dados para o Supabase ---")
    
    # Note: Sometimes loading data can fail due to integrity errors if tables aren't empty.
    # But since we just migrated, they should be empty (except for initial data created by migrations).
    # contenttypes usually causes issues, but we excluded it from dump.
    
    cmd_load = f'"{python_exe}" manage.py loaddata {dump_file}'
    if not run_command(cmd_load):
        print("FALHA na importação dos dados.")
        print("Tentando continuar... Verifique os erros acima.")
    else:
        print("Importação concluída com sucesso!")

    print("\n--- Processo Finalizado ---")

if __name__ == "__main__":
    main()
