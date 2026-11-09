# Guardrails build progress

Tracks the checklist in `Guardrails Take-Home 4-Hour Build Checklist.md`.
Legend: `[x]` done · `[~]` in progress · `[ ]` not started · `[!]` blocked / needs Carter · `[-]` skipped (with reason)

Project folder: `C:\Users\carte\OneDrive\Desktop\guardrails` on the desktop (used instead of `local-guardrails`, per Carter); clone at `C:\Users\OWNER\Desktop\guardrails` on the laptop. Repo: https://github.com/ctsc/guardrails (models/data/logs gitignored).
Python: `.venv` built with `py -3.12` (3.12.9) on the desktop, 3.11 on the laptop. Activate with `.venv\Scripts\activate`.

## Phase 1: Install and dataset

- [x] venv + `pip install fastapi uvicorn requests pyyaml gradio datasets huggingface_hub kaggle` (+ pytest, httpx, pandas, pyarrow)
  - Installed: fastapi 0.162, uvicorn 0.54, gradio 6.31, datasets 5.1, huggingface_hub 2.4, kaggle 2.2.5
- [x] HF + Kaggle auth (HF user `ctierney2`; `kaggle datasets list` works)
  - Tokens were found in `kaggle.md` (Carter saved them there). `setup_auth.py` reads that file and writes them to `~/.kaggle/access_token` and the HF token cache without printing them. `kaggle.md` is in `.gitignore` and has been deleted on both machines now that auth is stored.
- [x] llama.cpp into `C:\llama.cpp` via `get_llama_cpp.cmd`: build **b12211**, `llama-server.exe --version` = 0.9.0-dev
  - Used the **CUDA 12.4** zips, not 13.5: the newest release only ships 13.5 and your driver reports CUDA 13.2, so 12.4 is the pair guaranteed to load. Log: `logs\llama_dl.log`
- [x] Aegis 2.0 category counts + WildGuardMix subcategory names printed (`explore_local.py` -> `logs\explore_local.log`; Aegis counts also in `logs\build_dataset.log`)
  - Aegis 2.0 train: 30,007 rows; top categories: Criminal Planning/Confessions 2,850 · Needs Caution 2,148 · Hate/Identity Hate 1,140 · PII/Privacy 1,107 · Harassment 835 · Sexual 624 · Violence 392 (single-category counts; many rows are multi-category)
  - WildGuardMix subcategories (exact): benign, others, social_stereotypes_and_unfair_discrimination, disseminating_false_or_misleading_information_encouraging_disinformation_campaigns, sensitive_information_organization_government, toxic_language_hate_speech, violence_and_physical_harm, private_information_individual, defamation_encouraging_unethical_or_unsafe_actions, fraud_assisting_illegal_activities, sexual_content, mental_health_over-reliance_crisis, copyright_violations, cyberattack, causing_material_harm_by_disseminating_misinformation
  - XSTest: 450 rows (250 safe / 200 unsafe). prompt-injections-benchmark: 5,000 rows (2,003 jailbreak / 2,997 benign). civil_comments: ~1.1% of rows pass the insult filter, so ~55k rows are streamed to get 600 candidates.
- [x] `build_dataset.py` written and run (v2, after Carter's review) -> `data\train.jsonl` **3,984 rows** (4,000 sampled, 16 removed by dedup vs test). Seed 42. Full per-source counts in `data\counts.json` / `logs\build_dataset.log`
  - Per label: A 1,596 · B 397 · C 399 · D 397 · E 398 · F 400 · G 397. 350 rows are "Model output:" rows.
  - Every source hit its target (no class was short, so no WildGuardMix top-up was needed)
  - **v2 changes from Carter's row review:** (1) English only: `deepset/prompt-injections` dropped entirely (half of it is German) and replaced by `xTRam1/safe-guard-prompt-injection` (150 safe A rows + 100 attack G rows), plus an `is_english()` filter on every row as a backstop. (2) civil_comments insult threshold raised 0.7 -> 0.8 for sharper insult examples.
- [x] Test sets -> `data\test.jsonl` **2,960 rows**: prompt_attack_pib 500 (200 G / 300 A) · openai_moderation 1,511 · aegis_test 399 (A 89, B 67, C 66, D 66, E 42, F 69) · overblock_xstest 250 · overblock_jbb 100 · safeguard_test_secondary 200 (100 G / 100 A)
  - openai_moderation is 1,511 not 1,680: rows over 2,000 chars, empty, non-English, or duplicated were dropped (training max length is 512 tokens). 79 rows carry 2+ labels; they keep all valid letters in `valid_labels` and count as correct if the prediction is any of them.
  - aegis_test is 399 not 400: Aegis test only has 42 usable Violence rows.
- [x] Dedup: sha1 of lowercased, whitespace-collapsed text; 16 train rows collided with test rows and were dropped, 11 duplicate test rows dropped
- [x] 20 random rows printed (`data\sample20.txt`), reviewed by Carter `[YOU]`. Outcome: German rows removed, insult threshold raised (see v2 above). Known residual: some Aegis labels are noisy (e.g. descriptive text tagged Hate) -> goes on the limitations slide.
- [x] `train.jsonl` + `test.jsonl` uploaded as private Kaggle dataset `cartertierney/guardrails-train-test` (`upload_kaggle.cmd`, log in `logs\upload_kaggle.log`)

## Phase 2: Fine-tune on Kaggle
- [x] `train.ipynb` + `kaggle_kernel\kernel-metadata.json` written (Unsloth `FastModel`, `unsloth/Qwen3.5-2B`, 16-bit LoRA r=16 alpha=16 lr 2e-4, 1 epoch, max len 512, loss on the answer-letter token only, `enable_thinking=False`, seed 42, effective batch 16 = ~250 steps)
  - Eval is built in: base model (= LoRA at init, identity) and fine-tuned, every test set, per-class P/R/F1, macro-F1, confusion matrix, Wilson 95% CIs, FPR on XSTest+JBB, input vs model-output rows. Writes `results/eval_base.*`, `results/eval_finetuned.*`, `results/comparison.md`, `results/prompt_template.txt` (exact prompt string for `scorer.py`)
  - GGUF export: Unsloth `save_pretrained_gguf` (q8_0 + q4_k_m), fallback = merge 16-bit -> llama.cpp `convert_hf_to_gguf.py` -> prebuilt `llama-quantize`
  - `push_kernel.cmd smoke|full` sets the `SMOKE_TEST` flag and runs `kaggle kernels push`
- [x] 50-step smoke test on Kaggle (kernel `cartertierney/guardrails-train`): **loss is finite and decreasing, first-third mean 1.25 -> last-third mean 0.76** (steps 5..50: 1.15, 1.63, 0.96, 0.95, 0.81, 1.11, 0.75, 0.81, 0.75, 0.72). Token lengths min/median/max 199/220/498. Took 3 pushes:
  - v1 failed: dataset mounts at `/kaggle/input/datasets/<user>/<slug>/`, not `/kaggle/input/<slug>/` -> now globbed
  - v2 failed: prompt header is ~200 tokens so 340 text tokens overflowed 512 -> per-row text budget shrinks until it fits
  - v3 failed: CUDA OOM in the post-training eval -> adapter saved right after training, trainer freed, eval batch 8 with OOM-halving fallback
- [x] full run (v4) COMPLETE in ~61 min on a T4: 249 steps, loss first-third mean 0.87 -> last-third 0.42 (decreasing), eval base 606 s / tuned 523 s, GGUF Q8_0 + Q4_K_M exported
- [x] downloaded (`fetch_outputs.cmd`): `models\guardrail-2b-q8_0.gguf` (2.08 GB), `models\guardrail-2b-q4_k_m.gguf` (1.31 GB), `models\adapter\`, `results\eval_base.*`, `results\eval_finetuned.*`, `results\comparison.md`, `results\train_log.json`, `results\prompt_template.txt`, `logs\kaggle_full_run.log`
- [x] **results (base -> tuned, argmax over 7 letters):**
  | set | n | acc | macro-F1 | FPR (safe rows flagged) |
  |---|---|---|---|---|
  | aegis_test | 399 | 60.9 -> **74.7%** | 0.618 -> **0.734** | 55.1 -> **16.9%** |
  | openai_moderation | 1511 | 51.2 -> **63.1%** | 0.494 -> **0.534** | 60.0 -> **47.0%** |
  | prompt_attack_pib | 500 | 64.6 -> **80.4%** | 0.702 -> **0.814** | 36.0 -> **10.0%** |
  | safeguard_test_secondary | 200 | 76.5 -> **94.0%** | 0.817 -> **0.959** | 26.0 -> **7.0%** |
  | overblock_xstest (all safe) | 250 | 50.8 -> **60.4%** | - | 49.2 -> **39.6%** |
  | overblock_jbb (all safe) | 100 | 34.0 -> **62.0%** | - | 66.0 -> **38.0%** |
  | all input rows | 2826 | 55.4 -> **69.3%** | 0.479 -> **0.582** | 53.2 -> **36.4%** |
  | all model-output rows | 134 | 65.7 -> **72.4%** | 0.641 -> **0.703** | 42.3 -> **15.4%** |
  - Working: fine-tune beats base on every set; prompt attacks (80% / 94%), sexual (F1 0.92), hate (0.87) are strong on Aegis.
  - Not working well: **over-flagging of benign text** (XSTest 39.6%, JBB 38%, OpenAI-moderation safe rows 47% flagged, mostly as hate/violence); insults recall on Aegis only 0.39 (confused with safe/violence). Training mix was 40% safe / 60% unsafe, which pushes the model toward flagging. Options logged under "Open questions".
- [x] while training: `pii.py` (email/phone/SSN/card+Luhn/IP/URL), `scorer.py` (llama-server `/completion`, n_probs, renormalised letter probs), `api.py` (`POST /guardrail/apply` AWS ApplyGuardrail shape, `POST /chat`, `/healthz`; logs sha256 not raw text), `guardrail.yaml` (filter strengths LOW/MEDIUM/HIGH/NONE like AWS, PII actions), `tests/` (**14 passed, 1 live test skipped** until llama-server runs), `demo_prompts.txt` (5 prompts), `demo.py` (right/wrong table), `latency.py` (mean/p95 + nvidia-smi)

### Phase 2b: rerun with rebalanced data (Carter chose "another run for better results")
- [x] `build_dataset.py` safe quotas doubled (Aegis safe 1,000, OR-Bench 1,000, WildGuard adversarial-benign 700, safe-guard benign 250, Aegis safe responses 250) -> `data\train.jsonl` **5,580 rows, A 3,196 (57%) / B 397 / C 399 / D 397 / E 398 / F 400 / G 393**; 20 train rows dropped for colliding with test. `data\test.jsonl` byte-identical to v1 (kept as `data\test_v1.jsonl`), so v1 numbers stay comparable
- [x] `train.ipynb`: `REUSE_BASE_EVAL` loads the v1 `eval_base.json` shipped in the dataset instead of re-running the 10-min base eval; 1 epoch is now ~349 steps
- [x] dataset v2 uploaded, kernel v5 full run COMPLETE: 349 steps, ~50 min training, loss **0.76 -> 0.37** (first vs last third, decreasing); base eval reused from v1 as planned
- [x] v5 outputs downloaded; v1 GGUFs/results preserved under `models\v1\` and `results\v1\`; `models\guardrail-2b-*.gguf` are now v5
- [x] v1 -> v5 on the identical test set (`results\v1\comparison.md` vs `results\comparison.md`):

  | test set | v1 acc | **v5 acc** | v1 FPR | **v5 FPR** |
  |---|---|---|---|---|
  | Aegis test | 74.7% | **70.2%** | 16.9% | 18.0% |
  | OpenAI moderation | 63.1% | **64.7%** | 47.0% | **43.2%** |
  | JBB benign | 62.0% | 62.0% | 38.0% | 38.0% |
  | XSTest safe | 60.4% | **76.4%** | 39.6% | **23.6%** |
  | Prompt-attack benchmark | 80.4% | **82.8%** | 10.0% | **6.3%** |
  | safe-guard test | 94.0% | **94.5%** | 7.0% | 7.0% |
  | all input rows | 69.3% | **71.3%** | 36.4% | **31.7%** |
  | all output rows | 72.4% | **73.1%** | 15.4% | **11.5%** |

  - Working: over-blocking on XSTest cut 40% -> 24%, injection FPR 10% -> 6%, better on every aggregate.
  - Not working: Aegis accuracy dropped 4.5 pts (safe recall up, unsafe recall down: insults recall 0.38, violence precision 0.49); JBB benign unchanged at 38% flagged.
  - Decision: **v5 ships** (serving now). README/SLIDES updated with v5 numbers and the v1 -> v5 story.

## Phase 3: Run locally
- [x] `[YOU]` VRAM check: 4,692 MB free before start (no cleanup needed)
- [x] `start_server.cmd` -> llama-server b12211, `guardrail-2b-q8_0.gguf`, all layers on GPU, ctx 2048, :8080. Model takes ~2.1 GB VRAM (3,419 MB used total with desktop apps). `start_api.cmd` -> uvicorn :8000, `/healthz` = `{"api":"ok","llama_server":true}`
- [x] `pytest`: **15 passed** (live llama-server test included); re-run on v5: 15 passed
- [x] `demo.py` (`results\demo_table.json`, v5 model, RTX 3050 desktop): **4/5 RIGHT** (v1 was also 4/5 with the same miss). Probabilities below are from the live v5 API.
  | expected | got | action | ms |
  |---|---|---|---|
  | SAFE "How do I kill a Python process..." | SAFE (P=0.997) | NONE | 98 |
  | HATE "Immigrants ... subhuman vermin" | HATE (0.94) | GUARDRAIL_INTERVENED | 104 |
  | PII email + phone | PII masked | GUARDRAIL_INTERVENED | 104 |
  | PROMPT_ATTACK "Ignore all previous instructions... DAN" | PROMPT_ATTACK (0.997) | GUARDRAIL_INTERVENED | 104 |
  | PROMPT_ATTACK base64-encoded injection | **SAFE** | NONE | 118 |
  - The base64 miss is a natural "deliberate miss" for the demo: the model never saw encoded payloads in training, and it shows why AWS layers a prompt-attack filter with other controls. `[YOU]` Carter confirms this is the miss to show.
- [x] `latency.py` (`results\latency.json`, n=50, v5 model): **mean 122 ms, p50 124 ms, p95 144 ms, max 148 ms** per `/guardrail/apply` call (PII regex + one 2B forward pass on the RTX 3050 desktop). v1 was 132 / 132 / 148 / 154 ms (`results\v1\latency.json`)

## Phase 4: Demo and docs
- [x] `ui.py` running on http://127.0.0.1:7860 (Gradio: Guardrails OFF vs ON side by side, verdict + letter-probability bars + raw ApplyGuardrail JSON; examples from `demo_prompts.txt`). `/chat` verified both ways: guardrails ON blocks the injection (`PROMPT_ATTACK HIGH`, email anonymized) with reply "Sorry, I can't help with that request."; OFF passes the text straight to the model
- [x] `README.md`: what it is, architecture diagram, AWS coverage table, **real results table**, 3-command run, demo table + latency, limitations, dataset licenses
- [ ] `[YOU]` Carter records the 2-min backup video (UI at :7860, use the 5 example buttons; the base64 one is the miss)

## Phase 5: Slides
- [x] `SLIDES.md` drafted: 8 slides with the measured numbers (problem, AWS vs implemented, Qwen3.5-2B + why, architecture, data + training, results, demo, limitations + next steps)
- [ ] `[YOU]` Carter cuts anything he can't explain, rehearses once out loud

## Decisions / deviations log
- Used the existing `guardrails` folder instead of creating `local-guardrails` (Carter's instruction).
- Added `pytest`, `httpx`, `pandas`, `pyarrow` to the pip list (needed for `tests/`, FastAPI test client, and `datasets` parquet loading).

## Laptop (interview machine)
- [x] Clone at `C:\Users\OWNER\Desktop\guardrails`; `setup_laptop.cmd` (pip, llama.cpp b12211 CUDA build, Kaggle/HF auth via `setup_auth.py`, v5 GGUFs + data from Kaggle) finished in ~3 min; `kaggle.md` deleted after auth
- [x] Hardware: GTX 1660 Ti Max-Q 6 GB (compute 7.5), i5-10300H 4c/8t, 7.8 GB RAM, Windows 11, driver 591
- [x] llama-server (Q8_0) + API up, `pytest` 15/15, demo 4/5 (same rows right/wrong as the desktop), latency n=50: **mean 394 / p50 382 / p95 462 / max 467 ms**, 2.2 GB VRAM (`results\latency_laptop_1660ti.json`, `results\demo_table_laptop.json`)
- Gotchas: the first request after server start takes ~20 s on the 1660 Ti (CUDA warm-up; the live pytest times out at 30 s if it hits that), then ~0.4 s per call. Windows scheduled tasks default to "no start on battery", so the detached server (`run_server_bg.cmd`) silently never started until the task was set to AllowStartIfOnBatteries / DontStopIfGoingOnBatteries
- Interview plan: demo live on the laptop (Q8_0, ~0.4 s/call, no Q4_K_M needed); say up front that training/eval ran on Kaggle (T4) and the slide latency figures are from the RTX 3050 desktop

## Open questions for Carter
- Deliberate miss for the demo: the base64-encoded injection (predicted SAFE) -- confirm or pick another.
- Resolved: over-flagging -> Carter chose the second run (Phase 2b, v5 ships). `kaggle.md` deleted. Repo pushed to https://github.com/ctsc/guardrails.

## Known issues
- Devin Desktop's link to the machine drops every few minutes (seconds, on campus Wi-Fi); long jobs are run as scheduled tasks (`setup_laptop.cmd`, `run_server_bg.cmd`) that log to `logs\`.

## Post-review fixes (interview day)
Carter asked which of the "an interviewer will call this out" items could be fixed without retraining. Done:
- [x] `scorer.py`: long texts (>1,500 chars) scored in overlapping windows, worst window wins (was: silently truncated, attack at the end never seen). Test added.
- [x] `decode.py` + `api.py`: decode-and-rescan for base64 / URL-encoded payloads; worst variant wins; `decodedPayloads` added to the assessment. Tests added. Turns the base64 demo miss into a hit; `demo_prompts.txt` gained a leetspeak row as the new candidate miss.
- [x] `pii.py`: + US street address, date of birth (only the date is masked, and only when introduced as a birth date), AWS access key (BLOCK). 9 types now. Tests added.
- [x] `eval_llamaguard.py` + `run_llamaguard_eval.ps1`: Llama Guard 3 1B (Q8_0 GGUF, ungated QuantFactory build) on the same 2,960 test rows via a second llama-server on :8081, 4 parallel slots. Binary flag/safe comparison in README.
- [x] `throughput.py`: 4 concurrent clients against the API (`results/throughput_laptop.json`).
- [x] README / SLIDES: limitations now also list no validation split (model selected on test), single external baseline, possible benchmark contamination, single-turn/no context, thin output-side data, uncalibrated thresholds.
- [x] `run_fixes.cmd` runs all of the above on the laptop in one go (tests, API restart, Llama Guard download + eval, demo, throughput, `fill_docs.py`, commit + push) because the Devin Desktop link to the laptop kept dropping on campus Wi-Fi.
<!-- FIXES_PROGRESS -->
- Demo after fixes: 6/6 right; SAFE -> SAFE (RIGHT); HATE -> HATE (RIGHT); PII -> PII (RIGHT); PROMPT_ATTACK -> PROMPT_ATTACK (RIGHT); PROMPT_ATTACK -> PROMPT_ATTACK (RIGHT); PROMPT_ATTACK -> PROMPT_ATTACK (RIGHT)
- **Baseline, Llama Guard 3 1B (Meta), same 2,960 rows, binary flag/safe:** all input rows flag recall 87.7% ours vs 68.8% Llama Guard, FPR 31.7% vs 18.0%; prompt-injection benchmark recall 70.5% vs 60.0% (Llama Guard has no prompt-attack class); XSTest over-blocking 23.6% vs 7.2%.
- Throughput on the laptop, 4 concurrent clients, n=40: **1.49 req/s**, mean 2623.1 ms, p95 4414.0 ms per request
<!-- /FIXES_PROGRESS -->
