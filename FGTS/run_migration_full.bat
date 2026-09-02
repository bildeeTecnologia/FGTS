@echo off
cd /d "%~dp0"
echo Iniciando Migracao Completa...
.\.venv\Scripts\python.exe migrate_db.py
pause
