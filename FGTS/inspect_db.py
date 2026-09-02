import os
import psycopg2
from dotenv import load_dotenv
import sys

# Load environment variables
load_dotenv()

def get_db_connection():
    try:
        conn = psycopg2.connect(
            host=os.getenv('SUPABASE_HOST'),
            database=os.getenv('SUPABASE_DB'),
            user=os.getenv('SUPABASE_USER'),
            password=os.getenv('SUPABASE_PASSWORD'),
            port=os.getenv('SUPABASE_PORT', 5432)
        )
        return conn
    except Exception as e:
        print(f"Erro ao conectar: {e}")
        return None

def inspect_schema():
    conn = get_db_connection()
    if not conn:
        return

    cursor = conn.cursor()
    
    query = """
    SELECT 
        table_name, 
        column_name, 
        data_type, 
        is_nullable 
    FROM 
        information_schema.columns 
    WHERE 
        table_schema = 'public' 
    ORDER BY 
        table_name, ordinal_position;
    """
    
    try:
        cursor.execute(query)
        rows = cursor.fetchall()
        
        output_file = "db_schema_report.txt"
        with open(output_file, "w", encoding="utf-8") as f:
            f.write("=== RELATÓRIO DE ESTRUTURA DO BANCO DE DADOS (SUPABASE) ===\n\n")
            
            if not rows:
                f.write("Nenhuma tabela encontrada no schema 'public'. O banco parece vazio.\n")
            else:
                current_table = ""
                for row in rows:
                    table, col, dtype, nullable = row
                    if table != current_table:
                        f.write(f"\n--- Tabela: {table} ---\n")
                        current_table = table
                    
                    null_str = "NULL" if nullable == 'YES' else "NOT NULL"
                    f.write(f"  - {col:<30} {dtype:<20} {null_str}\n")
        
        print(f"Relatório gerado com sucesso: {output_file}")
        
    except Exception as e:
        print(f"Erro ao executar query: {e}")
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    inspect_schema()
