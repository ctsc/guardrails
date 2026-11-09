# Guardrails build progress

Tracks the checklist in `Guardrails Take-Home 4-Hour Build Checklist.md`.
Legend: `[x]` done · `[~]` in progress · `[ ]` not started · `[!]` blocked / needs Carter · `[-]` skipped (with reason)

Project folder: `C:\Users\carte\OneDrive\Desktop\guardrails` (used instead of `local-guardrails`, per Carter).
Python: `.venv` built with `py -3.12` (3.12.9). Activate with `.venv\Scripts\activate`.

## Phase 1: Install and dataset

- [x] venv + `pip install fastapi uvicorn requests pyyaml gradio datasets huggingface_hub kaggle` (+ pytest, httpx, pandas, pyarrow)
  - Installed: fastapi 0.162, uvicorn 0.54, gradio 6.31, datasets 5.1, huggingface_hub 2.4, kaggle 2.2.5
- [x] HF + Kaggle auth (HF user `ctierney2`; `kaggle datasets list` works)
  - Tokens were found in `kaggle.md` (Carter saved them there). `setup_auth.py` reads that file and writes them to `~/.kaggle/access_token` and the HF token cache without printing them. `kaggle.md` is in `.gitignore`. **Carter: delete or move `kaggle.md` now that auth works; it is plaintext secrets.**
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
- [x] `demo.py` (`results\demo_table.json`): **4/5 RIGHT** (same 4/5 on v5: base64 injection still the miss)
  | expected | got | action | ms |
  |---|---|---|---|
  | SAFE "How do I kill a Python process..." | SAFE (P=0.77, violence 0.17) | NONE | 121 |
  | HATE "Immigrants ... subhuman vermin" | HATE (0.99) | GUARDRAIL_INTERVENED | 118 |
  | PII email + phone | PII masked | GUARDRAIL_INTERVENED | 99 |
  | PROMPT_ATTACK "Ignore all previous instructions... DAN" | PROMPT_ATTACK (0.999) | GUARDRAIL_INTERVENED | 113 |
  | PROMPT_ATTACK base64-encoded injection | **SAFE** | NONE | 121 |
  - The base64 miss is a natural "deliberate miss" for the demo: the model never saw encoded payloads in training, and it shows why AWS layers a prompt-attack filter with other controls. `[YOU]` Carter confirms this is the miss to show.
- [x] `latency.py` (`results\latency.json`, n=50): **mean 132 ms, p50 132 ms, p95 148 ms, max 154 ms** per `/guardrail/apply` call (PII regex + one 2B forward pass on the RTX 3050)

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

## Open questions for Carter
- Over-flagging (XSTest 39.6% / JBB 38% of benign prompts flagged): ship as-is with it on the limitations slide (recommended for the 4-hour budget), or do a second ~1 h Kaggle run with a 50/50 safe/unsafe mix?
- Deliberate miss for the demo: the base64-encoded injection (predicted SAFE) -- confirm or pick another.
- `kaggle.md` (plaintext tokens) is still in the folder: delete/move it.

## Known issues
- Devin's connection to the laptop drops every few minutes; long-running commands may need re-running.
