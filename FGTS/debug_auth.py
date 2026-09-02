import psycopg2
import sys

HOST = "supabase.bildee.com.br"
PORT = 5432
DB = "postgres"

CREDENTIALS = [
    ("postgres", "DMGlkHeR95JFmA189ctaTlnbL6ASTJ3t", "Senha do PostgreSQL (Screenshot)"),
    ("postgres", "6zhaeVvg8P7o1E7e5CZw55OVdniyolVu", "Senha do Dashboard (Tentativa)"),
    ("kSa7YwiEGdbKGLL0", "6zhaeVvg8P7o1E7e5CZw55OVdniyolVu", "Usuário do Dashboard (Tentativa)"),
]

print(f"Testando conexão com {HOST}:{PORT}...")
print("-" * 60)

success = False

for user, password, desc in CREDENTIALS:
    print(f"Tentando: {desc}")
    print(f"User: {user}")
    # print(f"Pass: {password}") 
    
    try:
        conn = psycopg2.connect(
            host=HOST,
            database=DB,
            user=user,
            password=password,
            port=PORT,
            sslmode='prefer'
        )
        print(f"[OK] SUCESSO! Conectado com: {desc}")
        conn.close()
        success = True
        break
    except psycopg2.OperationalError as e:
        print(f"[X] Falha: {e}")
        print("-" * 60)

if not success:
    print("\nTodas as tentativas falharam.")
    print("Sugestão: Verifique se a senha foi realmente aplicada no Coolify/Supabase (Redeploy pode ser necessário).")
