@echo off
REM Upload data\train.jsonl + data\test.jsonl as the private Kaggle dataset cartertierney/guardrails-train-test.
REM First run creates it; later runs push a new version.
setlocal
cd /d "%~dp0"
copy /y data\train.jsonl kaggle_dataset\train.jsonl >nul || exit /b 1
copy /y data\test.jsonl kaggle_dataset\test.jsonl >nul || exit /b 1
copy /y data\counts.json kaggle_dataset\counts.json >nul
REM v1 base-model eval on the (unchanged) test set, so train.ipynb can reuse it instead of re-running it
if exist results\eval_base.json copy /y results\eval_base.json kaggle_dataset\eval_base.json >nul
.venv\Scripts\kaggle.exe datasets status cartertierney/guardrails-train-test >nul 2>&1
if errorlevel 1 (
  echo creating dataset ...
  .venv\Scripts\kaggle.exe datasets create -p kaggle_dataset --dir-mode skip
) else (
  echo dataset exists, pushing new version ...
  .venv\Scripts\kaggle.exe datasets version -p kaggle_dataset -m "rebuild %date% %time%" --dir-mode skip
)
echo.
.venv\Scripts\kaggle.exe datasets status cartertierney/guardrails-train-test
