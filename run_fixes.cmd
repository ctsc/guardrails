@echo off
REM One-shot: unit tests, restart API with the new code, Llama Guard 3 1B baseline, demo, throughput, fill docs, commit + push.
cd /d "%~dp0"
if not exist logs mkdir logs
if not exist models mkdir models
set LG_URL=https://huggingface.co/QuantFactory/Llama-Guard-3-1B-GGUF/resolve/main/Llama-Guard-3-1B.Q8_0.gguf

echo [1/8] unit tests
.venv\Scripts\python -m pytest -q tests -k "not live"
if errorlevel 1 echo !! unit tests failed, continuing so you still get the rest & echo.

echo [2/8] make sure llama-server (:8080) is up, restart API (:8000) with the new code
powershell -NoProfile -Command "try { Invoke-WebRequest -UseBasicParsing http://127.0.0.1:8080/health | Out-Null; exit 0 } catch { exit 1 }"
if errorlevel 1 (
  echo    llama-server not running, starting it...
  schtasks /run /tn GuardrailsServer >nul 2>&1 || start "llama-server" /min cmd /c start_server.cmd
  powershell -NoProfile -Command "for ($i=0; $i -lt 60; $i++) { Start-Sleep 2; try { Invoke-WebRequest -UseBasicParsing http://127.0.0.1:8080/health | Out-Null; break } catch {} }"
)
taskkill /f /im uvicorn.exe >nul 2>&1
powershell -NoProfile -Command "Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -like '*uvicorn*api:app*' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force }"
schtasks /run /tn GuardrailsApi >nul 2>&1
powershell -NoProfile -Command "for ($i=0; $i -lt 15; $i++) { Start-Sleep 1; try { Invoke-WebRequest -UseBasicParsing http://127.0.0.1:8000/healthz | Out-Null; exit 0 } catch {} }; exit 1"
if errorlevel 1 (
  echo    scheduled task did not bring the API up, starting uvicorn directly
  start "api" /min cmd /c ".venv\Scripts\uvicorn api:app --port 8000 > logs\api.log 2>&1"
  powershell -NoProfile -Command "for ($i=0; $i -lt 30; $i++) { Start-Sleep 1; try { Invoke-WebRequest -UseBasicParsing http://127.0.0.1:8000/healthz | Out-Null; exit 0 } catch {} }; Write-Host '!! API did not start, see logs\api.log'; Get-Content logs\api.log -Tail 20; exit 1"
)
powershell -NoProfile -Command "try { Write-Host '   ' (Invoke-WebRequest -UseBasicParsing http://127.0.0.1:8000/healthz).Content } catch { Write-Host '   API DOWN' }"
echo    warm-up request
powershell -NoProfile -Command "try { Invoke-RestMethod -Method Post http://127.0.0.1:8000/guardrail/apply -ContentType 'application/json' -Body '{\"source\":\"INPUT\",\"content\":[{\"text\":{\"text\":\"hello there\"}}]}' | Out-Null } catch { Write-Host $_ }"

echo [3/8] Llama Guard 3 1B download (1.3 GB, skipped if present)
if not exist models\llama-guard-3-1b-q8_0.gguf (
  curl -L -# -o models\llama-guard-3-1b-q8_0.gguf.part %LG_URL% && move /y models\llama-guard-3-1b-q8_0.gguf.part models\llama-guard-3-1b-q8_0.gguf >nul
)
if not exist models\llama-guard-3-1b-q8_0.gguf echo !! download failed, skipping the baseline & goto :demo

echo [4/8] Llama Guard eval on 2,960 rows (second llama-server on :8081, a few minutes)
powershell -NoProfile -ExecutionPolicy Bypass -File run_llamaguard_eval.ps1
if exist results\eval_llamaguard.md type results\eval_llamaguard.md

:demo
echo [5/8] demo table
.venv\Scripts\python demo.py
echo [6/8] throughput (4 concurrent clients)
.venv\Scripts\python throughput.py http://127.0.0.1:8000 4 40 laptop
echo [7/8] fill README / SLIDES / PROGRESS
.venv\Scripts\python fill_docs.py
if errorlevel 1 echo !! fill_docs failed; docs still have markers

echo [8/8] commit + push
git add -- api.py decode.py pii.py scorer.py guardrail.yaml demo_prompts.txt demo.py eval_llamaguard.py run_llamaguard_eval.ps1 throughput.py fill_docs.py run_fixes.cmd dl_llamaguard.cmd tests README.md SLIDES.md PROGRESS.md results/demo_table.json
if exist results\eval_llamaguard.json git add -- results/eval_llamaguard.json results/eval_llamaguard.md
if exist results\throughput_laptop.json git add -- results/throughput_laptop.json
git commit -m "Llama Guard 3 1B baseline results, post-fix demo table, laptop throughput"
git push origin main
echo.
echo ===== DONE. Tell Devin "run_fixes done" (paste the Llama Guard table above if the link is still flaky). =====
