@echo off
cd /d "%~dp0"
echo Executando migrations no PostgreSQL Supabase...
echo.
.\.venv\Scripts\python.exe manage.py migrate
echo.
echo Migrations concluidas!
pause
