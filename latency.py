"""Average and p95 latency of POST /guardrail/apply, plus nvidia-smi VRAM. Writes results/latency.json."""
import json, statistics, subprocess, sys, time, requests

API = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8000"
N = int(sys.argv[2]) if len(sys.argv) > 2 else 50
texts = [l.split("\t", 1)[1].strip() for l in open("demo_prompts.txt", encoding="utf-8") if "\t" in l]
lat = []
for i in range(N):
    t = texts[i % len(texts)] + f" (run {i})"   # defeat the prompt cache
    t0 = time.perf_counter()
    requests.post(f"{API}/guardrail/apply", json={"source": "INPUT", "content": [{"text": {"text": t}}]}, timeout=60).raise_for_status()
    lat.append((time.perf_counter() - t0) * 1000)
lat.sort()
res = {"n": N, "mean_ms": round(statistics.mean(lat), 1), "p50_ms": round(lat[len(lat) // 2], 1), "p95_ms": round(lat[int(len(lat) * 0.95) - 1], 1), "max_ms": round(lat[-1], 1)}
try:
    smi = subprocess.run(["nvidia-smi", "--query-gpu=memory.used,memory.total", "--format=csv,noheader"], capture_output=True, text=True, timeout=10).stdout.strip()
    res["gpu_memory"] = smi
    res["processes"] = subprocess.run(["nvidia-smi", "--query-compute-apps=process_name,used_memory", "--format=csv,noheader"], capture_output=True, text=True, timeout=10).stdout.strip()
except Exception as e:
    res["gpu_memory"] = f"nvidia-smi failed: {e}"
print(json.dumps(res, indent=1))
json.dump(res, open("results/latency.json", "w"), indent=1)
