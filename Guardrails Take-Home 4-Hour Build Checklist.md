# Guardrails Take-Home: 4-Hour Build Checklist

Nov 8, 2026 · @Carter

## What you are building

A local guardrail service: a fine-tuned Qwen3.5-2B that labels text as safe or one of 6 AWS categories, plus regex PII masking, behind an AWS-shaped API.

- **Model:** fine-tune Qwen3.5-2B with LoRA on a free Kaggle T4. It is one of the models openjev.com (SemIf) runs, and 2B trains in about 15 to 30 min.
- **Format:** the openjev.com trick. Ask a multiple-choice question (A = safe, B = hate, C = insults, D = sexual, E = violence, F = misconduct/illegal, G = prompt attack) and read the probability of each letter. No text generation.
- **PII:** regex for email, phone, SSN, credit card. Runs first, so raw PII never reaches the model.
- **API:** FastAPI `POST /guardrail/apply` that returns the same JSON shape as AWS ApplyGuardrail (`action`, `assessments`, masked `outputs`).
- **Proof:** base model vs your fine-tuned model on held-out test data, plus false positive rate on harmless prompts (XSTest). That table is the whole pitch.

Scope cut on purpose (say this out loud): denied topics, grounding checks, Automated Reasoning, images, multilingual. They go on the limitations slide.

## Manual vs AI: who does what

"AI" = Claude Code (or Devin) running in your `local-guardrails` folder on your PC, with permission to run commands. It writes every file, installs everything, runs the Kaggle training remotely through the Kaggle command-line tool, and runs the eval and the servers. You only do what needs your logins, your face, or your judgment.

**Only you can do these (about 25 minutes total):**

1. Create the Kaggle account, verify your phone, and download the Kaggle API token
2. Create the Hugging Face account and read token, and accept the Aegis dataset terms
3. Paste both tokens where AI tells you (AI should never ask you to paste a token into chat)
4. Spot-check 20 dataset rows and 5 live demo results (2 minutes each)
5. Record the backup demo video
6. Edit the slides and rehearse out loud

**AI does everything else:** installs Python packages and llama.cpp, builds the dataset, uploads it to Kaggle, writes and launches the training notebook, waits for it, downloads the model, runs the eval, writes and starts the guardrail API and demo UI, measures latency and VRAM, writes the README and slide draft.

One rule: when AI finishes a file, ask it "explain this file in 2 sentences". If you cannot repeat that back, you are not ready to present it.

## The checklist (about 4 hours)

Do Phase 0 yourself first, then hand AI this doc and say "do Phases 1 to 5, stop at every \[YOU\] step". Your hands-on time after Phase 0 is about 40 minutes.

**Phase 0: Accounts and tokens, all manual (0:00 to 0:25)**

- [x] &#91;YOU\] Kaggle account and phone verification
  - Go to kaggle.com, click Register, sign up with Google (fastest)
  - Click your profile picture (top right), then Settings
  - Scroll to Phone Verification, enter your number, type in the SMS code. Without this, Kaggle will not give you a GPU or internet in notebooks
- [x] &#91;YOU\] Kaggle API token (lets AI launch training from your PC)
  - Same Settings page, scroll to the API section, click Create New Token
  - If it downloads `kaggle.json`: make the folder `C:\Users\<your name>\.kaggle\` and move the file into it
  - If it instead shows a token string: copy it, and when AI asks, paste it into the terminal (not into chat)
- [x] &#91;YOU\] Hugging Face account and read token
  - Go to huggingface.co, click Sign Up, confirm your email
  - Click your profile picture (top right), then Settings, then Access Tokens in the left menu (direct link: huggingface.co/settings/tokens)
  - Click Create new token, pick token type Read, name it `guardrails`, click Create token
  - Copy it right away, it is only shown once. Save it in your password manager or a note
- [x] &#91;YOU\] Unlock the 3 gated datasets (same logged-in browser, about 3 min). Open each page and fill in and accept the access form at the top:
  - huggingface.co/datasets/allenai/wildguardmix (AI2 form, approved automatically)
  - huggingface.co/datasets/walledai/XSTest
  - huggingface.co/datasets/rogue-security/prompt-injections-benchmark (if it shows a form)
  - Aegis 2.0, OR-Bench, civil\_comments, jackhhao, Gandalf, deepset, JailbreakBench and the OpenAI moderation set are not gated, nothing to do
- [x] &#91;YOU\] GPU check done: RTX 3050, 6,144 MB, driver 595.95, CUDA 13.2. Fine for everything in this plan
  - Note: about 1,400 MB of that is already used by open apps (Chrome, Discord, Overwolf, Steam, Epic, Teams, Riot Vanguard, ChatGPT, Claude, CurseForge). That leaves about 4,700 MB for the model. Phase 3 has you close these first
- [x] &#91;YOU\] Run `python --version` done: you have 3.14 (default), 3.13, 3.12 and 3.11. Use 3.12 for this project: AI runs py -3.12 -m venv .venv in the project folder, then activates it with .venv\\Scripts\\activate before any pip install. Leave your 3.14 default alone
- [x] &#91;YOU\] Make the folder `C:\Users\<your name>\local-guardrails`, open Claude Code (or Devin) in it, paste this doc in, and say "do Phases 1 to 5"

**Phase 1: Install and dataset (0:25 to 1:00)**

- [ ] &#91;AI\] `pip install fastapi uvicorn requests pyyaml gradio datasets huggingface_hub kaggle`
- [ ] &#91;AI\] Run `hf auth login`, then \[YOU\] paste the HF token into the terminal prompt when it asks
- [ ] &#91;AI\] Download llama.cpp: from github.com/ggml-org/llama.cpp/releases, latest release, grab the Windows CUDA 13 zips if listed (`llama-<build>-bin-win-cuda-13.x-x64.zip` plus the matching `cudart-...` zip), otherwise the CUDA 12.4 pair. Your driver supports both. Unzip both into `C:\llama.cpp`
  - If AI cannot download it: \[YOU\] open that releases page, expand Assets under the newest release, download those two zips, unzip both into `C:\llama.cpp`
- [ ] &#91;AI\] Before sampling, print Aegis 2.0 category counts and WildGuardMix `subcategory` names (exact spellings are not documented). If any category has under 250 clean rows, top it up from WildGuardMix
- [ ] &#91;AI\] Write and run `build_dataset.py` on your PC: 4,000 training rows, seed 42, logged counts per source
  - A safe (1,600): Aegis safe prompts 600 (drop "Needs Caution", "REDACTED" rows, and any safe row matching an injection pattern like "ignore previous" or "act as", because Aegis mislabels some injections as safe), OR-Bench-80k 400 (benign prompts that look scary), WildGuardMix adversarial benign 300, deepset label 0 150, Aegis safe model responses 150
  - B hate (400): Aegis Hate/Identity Hate 250 prompts + 50 responses, WildGuardMix hate/stereotype rows 100
  - C insults (400): `google/civil_comments` streamed, `insult` 0.7 or higher with `identity_attack`, `threat` and `sexual_explicit` under 0.2, 300 rows; Aegis Harassment 100. Aegis has no insults category, which is why this source is added
  - D sexual, E violence, F misconduct (400 each): Aegis prompts 250 + Aegis unsafe responses 50 + matching WildGuardMix rows 100
  - G prompt attack (400): WildGuardMix adversarial harmful 150 (modern jailbreaks), jackhhao jailbreaks 100, deepset label 1 100, Gandalf train 50
  - Rules: a jailbreak or injection is always G even if it is also hateful; model response rows start with "Model output:" and are never labeled G; drop rows that map to two different letters
- [ ] &#91;AI\] Build the test set from sources never trained on:
  - G: `rogue-security/prompt-injections-benchmark`, 500 rows (200 jailbreak, 300 benign). Main prompt-attack number
  - B to E: `mmathys/openai-moderation-api-evaluation`, all 1,680 (H to B, HR to C, S to D, V and SH to E, none to A)
  - All classes: Aegis 2.0 test, 400 stratified
  - Over-blocking: XSTest safe 250 + JailbreakBench benign 100
  - deepset test 116, reported as secondary only (small, most baselines trained on it)
- [ ] &#91;AI\] Dedup: hash lowercased text, drop any training row that matches a test row
- [ ] &#91;AI\] Print 20 random rows with labels. \[YOU\] Read them, 2 minutes. If labels look wrong, tell AI which ones
- [ ] &#91;AI\] Upload `train.jsonl` and `test.jsonl` as a private Kaggle dataset with `kaggle datasets create` (so the notebook needs no HF token)
- [ ] &#91;AI\] Fallback if a gate blocks you: replace WildGuardMix rows with more Aegis rows, plus 150 G rows from `xTRam1/safe-guard-prompt-injection` (label 1)

**Phase 2: Fine-tune on Kaggle (1:00 to 2:00)**

- [ ] &#91;AI\] Write `train.ipynb` from Unsloth's Qwen3.5-2B notebook: 16-bit LoRA (not 4-bit QLoRA, Unsloth says it hurts Qwen3.5), r=16, alpha=16, lr 2e-4, 1 epoch, max length 512, loss on the answer letter only, thinking off
- [ ] &#91;AI\] Write `kernel-metadata.json` with GPU and internet on and the dataset attached, then launch with `kaggle kernels push`
- [ ] &#91;AI\] Run a 50-step smoke test first and confirm the loss is a real number that goes down, then launch the full run
- [ ] &#91;AI\] Poll `kaggle kernels status` every few minutes (about 20 to 40 min for 4,000 rows; first run is slower because Unsloth compiles kernels)
- [ ] &#91;AI\] Notebook also runs the eval, base model vs fine-tuned, on every test set from Phase 1
  - Per test set: precision, recall and F1 per class, macro-F1, a confusion matrix
  - Over-blocking: false positive rate on XSTest safe + JailbreakBench benign
  - 95% Wilson intervals on every number (at about 100 rows they are roughly plus or minus 10 points, say so)
  - Score model-output rows separately from user-input rows
- [ ] &#91;AI\] Export GGUF Q8\_0 (about 2.5 GB) and also Q4\_K\_M (about 1.5 GB) as a backup for low VRAM
- [ ] &#91;AI\] Download everything with `kaggle kernels output` into `models/` and `results/`
- [ ] &#91;AI\] While training runs: write `pii.py` (regex), `scorer.py` (calls llama-server, reads letter probabilities), `api.py` (`/guardrail/apply` + `/chat`), `guardrail.yaml` (LOW/MEDIUM/HIGH thresholds), `tests/`, `demo_prompts.txt`

**Phase 3: Run it locally (2:00 to 2:35)**

- [ ] &#91;YOU\] Free GPU memory: quit Discord, Overwolf, Steam, Epic, CurseForge, Teams and the ChatGPT app (right-click their tray icons, Quit). Leave Claude/Devin and one Chrome window open
- [ ] &#91;AI\] Run `nvidia-smi` and confirm at least 3,500 MB is free
- [ ] &#91;AI\] Start the model on your 3050: `C:\llama.cpp\llama-server.exe -m models\guardrail-2b-q8_0.gguf -ngl 99 -c 2048 --port 8080`
  - If it fails with out of memory: switch to the Q4\_K\_M file, same command
- [ ] &#91;AI\] Start the API (`uvicorn api:app --port 8000`) and run `pytest`
- [ ] &#91;AI\] Send the 5 demo prompts (safe, hate, email address, injection, base64-encoded injection) and print a right/wrong table
- [ ] &#91;YOU\] Read the table, 2 minutes. Pick which miss you will show on purpose in the demo
- [ ] &#91;AI\] Run `latency.py` (average and p95 ms per check) and `nvidia-smi` for VRAM, save to `results/`

**Phase 4: Demo and docs (2:30 to 3:15)**

- [ ] &#91;AI\] Write and launch `ui.py`: Gradio with Guardrails OFF vs ON side by side, JSON response shown
- [ ] &#91;YOU\] Record a 2-minute backup video: press Win + G (Xbox Game Bar), click Record, walk through the 5 demo prompts
- [ ] &#91;AI\] Write the README: what it is, architecture diagram, AWS coverage table, results table, how to run in 3 commands, limitations, dataset licenses

**Phase 5: Slides and rehearse (3:15 to 4:00)**

- [ ] &#91;AI\] Draft 8 slides with your real numbers filled in: problem, AWS coverage vs what you built, what Open Jev is, architecture, data and training, results, demo, limitations and next steps
- [ ] &#91;YOU\] Cut anything you cannot explain, then rehearse once out loud, timing yourself

## If something breaks

| Problem | Do this |
| --- | --- |
| Kaggle gives no GPU or quota runs out | Use Google Colab free T4, same notebook |
| Unsloth errors on Qwen3.5 (it is a vision model, the notebook may need `FastModel` instead of `FastLanguageModel`) | Paste the error to AI; fallback model is Qwen3-1.7B, which trains with no surprises |
| Loss shows NaN on T4 | Lower lr to 1e-4; if still NaN, switch to Qwen3-1.7B |
| GGUF export fails | Skip llama.cpp; run the model with transformers in Python on the 3050 for the demo (slower, still works) |
| Fine-tuned model does not beat the base | Present it anyway with a reason (too little data, label noise). An honest measured result beats an unmeasured one |
| Running out of time | Cut in this order: Gradio UI, latency script, README polish. Never cut: base vs fine-tuned table, XSTest false positive number, limitations slide |

## What to say in the interview

- **Opening line:** "I had a few hours, so I built a small, correct, measured core that matches the AWS API shape, and listed every gap with how I'd close it."
- **What Open Jev is:** openjev.com is SemIf, a method that reads answer-letter probabilities from small frozen models. It has no weights of its own, so I fine-tuned the model it runs on in its exact format. (The Hugging Face "OpenJev-Flash-9B" needs about 22 GB to fine-tune and is non-commercial, so it was out.)
- **AWS coverage:** AWS already filters hate, insults, sexual, violence, misconduct (crime/illegal) and prompt attacks. I matched those 6, plus PII masking.
- **Why hybrid:** regex for PII because it is exact and auditable, and a missed SSN digit is a privacy failure. The model only handles what needs understanding.
- **Why letter probabilities, not JSON:** one forward pass, no parsing errors, and a probability per category I can threshold into LOW/MEDIUM/HIGH like AWS. AWS's own 2026 InvokeGuardrailChecks API also returns numeric scores.
- **Privacy angle (your concentration):** PII is masked before the model sees it, nothing leaves the machine, and logs store categories and hashes, not raw text. AWS logs blocked content in plain text if invocation logging is on.
- **Cost:** AWS charges $0.15 per 1,000 text units per content policy. Local has no per-call cost, but you pay for the GPU even when idle. Self-hosting wins at high steady volume.
- **Limits, say them yourself:** guard classifiers can be bypassed (a 2025 Lancaster/Mindgard paper hit up to 100% evasion on Meta Prompt Guard and Azure Prompt Shield). Show the base64 prompt your model misses on purpose. Next steps: more data, adversarial training, multilingual, denied topics.

**Why these datasets (say this when asked):**

- Aegis 2.0 (NVIDIA) is the backbone because it is human-labeled, CC-BY licensed, and covers hate, sexual, violence and crime in both prompts and model responses.
- Aegis has no insults category, so I added civil\_comments rows with a high insult score and a low identity-attack score. That is exactly how AWS separates Insults from Hate.
- WildGuardMix gives modern adversarial jailbreaks, not just 2023 DAN prompts, plus harmless prompts written to look adversarial.
- I trained on hard negatives (OR-Bench, "how do I kill a Python process") because over-blocking is how guardrails fail in production.
- I fixed label conflicts first: Aegis marks some "ignore previous instructions" prompts as safe, which would teach the opposite of my prompt-attack class.
- Every test set is a source the model never saw (Qualifire, OpenAI moderation eval, XSTest, JailbreakBench), deduplicated against training, with confidence intervals.

**Likely questions:** Why fine-tune instead of prompting? (show your base vs fine-tuned numbers) · What does a false positive cost? (blocked real users; show XSTest rate) · How would you scale it? (batching, a tiny fast pre-filter in front, more GPUs behind the API) · How do you handle new attacks? (log scores, label borderline cases, retrain the LoRA adapter)
