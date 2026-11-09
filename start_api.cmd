@echo off
cd /d "%~dp0"
.venv\Scripts\uvicorn api:app --port 8000
