@echo off
REM Usage: push_kernel.cmd smoke   (50-step sanity run)   or   push_kernel.cmd full
REM Copies train.ipynb into kaggle_kernel\, sets SMOKE_TEST, and pushes the kernel to Kaggle (GPU + internet + dataset attached via kernel-metadata.json).
setlocal
cd /d "%~dp0"
if "%1"=="" ( echo usage: push_kernel.cmd smoke^|full & exit /b 1 )
if /i "%1"=="smoke" ( set FLAG=True ) else ( set FLAG=False )
.venv\Scripts\python -c "import json,sys; p='kaggle_kernel/train.ipynb'; nb=json.load(open('train.ipynb',encoding='utf-8')); c=nb['cells'][1]; s=''.join(c['source']); assert s.startswith('SMOKE_TEST = '); c['source']=s.replace('SMOKE_TEST = True','SMOKE_TEST = %FLAG%',1).replace('SMOKE_TEST = False','SMOKE_TEST = %FLAG%',1); json.dump(nb,open(p,'w',encoding='utf-8'),indent=1); print('SMOKE_TEST set to %FLAG%')" || exit /b 1
.venv\Scripts\kaggle.exe kernels push -p kaggle_kernel
echo.
.venv\Scripts\kaggle.exe kernels status cartertierney/guardrails-train
