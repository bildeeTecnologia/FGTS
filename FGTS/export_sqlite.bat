@echo off
cd /d "%~dp0"
echo ========================================
echo  EXPORTANDO DADOS DO SQLITE
echo ========================================
echo.

set TIMESTAMP=%date:~-4%%date:~3,2%%date:~0,2%_%time:~0,2%%time:~3,2%%time:~6,2%
set TIMESTAMP=%TIMESTAMP: =0%

:: Forçar uso do SQLite limpando variáveis de ambiente do Supabase
set SUPABASE_HOST=
set SUPABASE_DB=
set SUPABASE_USER=
set SUPABASE_PASSWORD=

echo Criando backup completo dos dados...
echo Arquivo: backup_sqlite_%TIMESTAMP%.json
echo.

.\.venv\Scripts\python.exe manage.py dumpdata ^
    --exclude auth.permission ^
    --exclude contenttypes ^
    --exclude sessions.session ^
    --natural-foreign ^
    --indent 2 ^
    --output backup_sqlite_%TIMESTAMP%.json

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================
    echo  BACKUP CRIADO COM SUCESSO!
    echo ========================================
    echo Arquivo: backup_sqlite_%TIMESTAMP%.json
    
    for %%A in (backup_sqlite_%TIMESTAMP%.json) do (
        echo Tamanho: %%~zA bytes
    )
    echo.
    echo Este arquivo sera usado para importar no PostgreSQL
) else (
    echo.
    echo ========================================
    echo  ERRO AO CRIAR BACKUP!
    echo ========================================
    echo Verifique os erros acima
)

echo.
pause
