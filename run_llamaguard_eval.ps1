# Runs the Llama Guard 3 1B baseline: second llama-server on :8081, eval over data/test.jsonl, then stops the server.
Set-Location $PSScriptRoot
$log = "logs\llamaguard_eval.log"
"=== $(Get-Date) start" | Out-File $log
$p = Start-Process C:\llama.cpp\llama-server.exe -ArgumentList "-m models\llama-guard-3-1b-q8_0.gguf -ngl 99 -c 8192 --parallel 4 --port 8081" -PassThru -NoNewWindow -RedirectStandardOutput logs\lg_server.log -RedirectStandardError logs\lg_server.err
$ok = $false
for ($i = 0; $i -lt 90; $i++) { Start-Sleep 2; try { if ((Invoke-WebRequest -UseBasicParsing http://127.0.0.1:8081/health).StatusCode -eq 200) { $ok = $true; break } } catch {} }
"server up: $ok after $($i*2)s" | Out-File $log -Append
if ($ok) {
  # warm-up (first request compiles CUDA kernels on the 1660 Ti)
  try { Invoke-RestMethod -Method Post http://127.0.0.1:8081/completion -ContentType 'application/json' -Body '{"prompt":"hi","n_predict":1}' | Out-Null } catch {}
  & .venv\Scripts\python eval_llamaguard.py http://127.0.0.1:8081 2>&1 | Out-File $log -Append
}
Stop-Process -Id $p.Id -Force
"=== $(Get-Date) done" | Out-File $log -Append
