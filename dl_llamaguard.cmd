@echo off
cd /d "%~dp0"
curl -L -sS -o models\llama-guard-3-1b-q8_0.gguf.part https://huggingface.co/QuantFactory/Llama-Guard-3-1B-GGUF/resolve/main/Llama-Guard-3-1B.Q8_0.gguf > logs\lg_download.log 2>&1 && move /y models\llama-guard-3-1b-q8_0.gguf.part models\llama-guard-3-1b-q8_0.gguf >> logs\lg_download.log
echo DONE %errorlevel% >> logs\lg_download.log
