@echo off
cd /d "%~dp0"
echo Inspecionando banco de dados Supabase...
.\.venv\Scripts\python.exe inspect_db.py
pause
