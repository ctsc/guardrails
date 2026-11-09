@echo off
REM Download the finished Kaggle kernel outputs into models\ and results\
cd /d "%~dp0"
rmdir /s /q kaggle_kernel\output 2>nul
.venv\Scripts\kaggle.exe kernels output cartertierney/guardrails-train -p kaggle_kernel\output || exit /b 1
if not exist models mkdir models
if not exist results mkdir results
xcopy /y /e kaggle_kernel\output\results\* results\ >nul
xcopy /y /e kaggle_kernel\output\models\* models\ >nul
for %%f in (kaggle_kernel\output\*.log) do copy /y "%%f" logs\kaggle_full_run.log >nul
echo.
echo === results\ && dir /b results
echo === models\ && dir /b models
