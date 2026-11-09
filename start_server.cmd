@echo off
REM Phase 3: start llama-server with the fine-tuned guardrail model (Q8_0; pass q4 as the first arg to use Q4_K_M)
cd /d "%~dp0"
set MODEL=models\guardrail-2b-q8_0.gguf
if /i "%1"=="q4" set MODEL=models\guardrail-2b-q4_k_m.gguf
echo Using %MODEL%
C:\llama.cpp\llama-server.exe -m %MODEL% -ngl 99 -c 2048 --port 8080
