@echo off
REM Runs llama-server detached (used by the GuardrailsServer scheduled task). Pass "q4" for the Q4_K_M model.
cd /d "%~dp0"
if not exist logs mkdir logs
set MODEL=models\guardrail-2b-q8_0.gguf
if /i "%1"=="q4" set MODEL=models\guardrail-2b-q4_k_m.gguf
(
echo === %date% %time% starting %MODEL%
echo === port 8080 before start
netstat -ano | findstr :8080
nvidia-smi --query-gpu=name,memory.used,memory.total --format=csv,noheader
) > logs\llama_server.log 2>&1
C:\llama.cpp\llama-server.exe -m %MODEL% -ngl 99 -c 2048 --port 8080 >> logs\llama_server.log 2>&1
echo === %date% %time% llama-server exited with %errorlevel% >> logs\llama_server.log
