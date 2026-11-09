@echo off
REM One-shot setup for a fresh clone: packages, llama.cpp, Kaggle/HF auth, model + data download.
REM Needs: .venv already created, kaggle.md (tokens) in this folder. Logs go to logs\.
cd /d "%~dp0"
if not exist logs mkdir logs
if not exist models mkdir models
if not exist data mkdir data
echo [%time%] START > logs\setup_laptop.log

start "" /min cmd /c "get_llama_cpp.cmd > logs\llama_install.log 2>&1"

.venv\Scripts\pip install fastapi uvicorn requests pyyaml gradio datasets huggingface_hub kaggle pytest httpx six pandas pyarrow > logs\pip_install.log 2>&1 && echo PIP DONE >> logs\pip_install.log
echo [%time%] pip exit %errorlevel% >> logs\setup_laptop.log

.venv\Scripts\python setup_auth.py > logs\setup_auth.log 2>&1
echo [%time%] auth exit %errorlevel% >> logs\setup_laptop.log

call fetch_outputs.cmd > logs\fetch_outputs.log 2>&1
echo [%time%] fetch exit %errorlevel% >> logs\setup_laptop.log
for /r kaggle_kernel\output %%f in (*Q8_0.gguf) do move /y "%%f" models\guardrail-2b-q8_0.gguf >nul
for /r kaggle_kernel\output %%f in (*Q4_K_M.gguf) do move /y "%%f" models\guardrail-2b-q4_k_m.gguf >nul

.venv\Scripts\kaggle.exe datasets download -d cartertierney/guardrails-train-test -p data --unzip > logs\data_dl.log 2>&1
echo [%time%] data exit %errorlevel% >> logs\setup_laptop.log

dir models >> logs\setup_laptop.log
dir data >> logs\setup_laptop.log
echo [%time%] SETUP DONE >> logs\setup_laptop.log
