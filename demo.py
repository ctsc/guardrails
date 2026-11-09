"""Send the demo prompts to the running API and print a right/wrong table (Phase 3 [YOU] check)."""
import json, sys, requests

API = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8000"
rows = []
for line in open("demo_prompts.txt", encoding="utf-8"):
    if not line.strip() or line.startswith("#"):
        continue
    expected, text = line.rstrip("\n").split("\t", 1)
    r = requests.post(f"{API}/guardrail/apply", json={"source": "INPUT", "content": [{"text": {"text": text}}]}, timeout=60).json()
    filt = r["assessments"][0]["contentPolicy"]["filters"]
    ents = r["assessments"][0]["sensitiveInformationPolicy"]["piiEntities"]
    got = filt[0]["type"] if filt else ("PII" if ents else "SAFE")
    ok = got == expected or (expected == "PII" and ents)
    rows.append((expected, got, r["action"], r["assessments"][0]["invocationMetrics"]["guardrailProcessingLatency"], "RIGHT" if ok else "WRONG", text[:60]))
print(f"{'expected':14s} {'got':14s} {'action':20s} {'ms':>7s}  result  text")
for e, g, a, ms, res, t in rows:
    print(f"{e:14s} {g:14s} {a:20s} {ms:7.0f}  {res:6s} {t}")
json.dump([dict(zip(("expected", "got", "action", "ms", "result", "text"), r)) for r in rows], open("results/demo_table.json", "w"), indent=1)
