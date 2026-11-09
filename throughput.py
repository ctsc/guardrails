"""Throughput of POST /guardrail/apply with concurrent clients (llama-server has 4 slots). Writes results/throughput_<tag>.json."""
import json, statistics, sys, time
from concurrent.futures import ThreadPoolExecutor
import requests

API = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8000"
WORKERS = int(sys.argv[2]) if len(sys.argv) > 2 else 4
N = int(sys.argv[3]) if len(sys.argv) > 3 else 40
TAG = sys.argv[4] if len(sys.argv) > 4 else "laptop"
texts = [l.split("\t", 1)[1].strip() for l in open("demo_prompts.txt", encoding="utf-8") if "\t" in l]


def one(i):
    t0 = time.perf_counter()
    requests.post(f"{API}/guardrail/apply", json={"source": "INPUT", "content": [{"text": {"text": texts[i % len(texts)] + f" (run {i})"}}]}, timeout=120).raise_for_status()
    return (time.perf_counter() - t0) * 1000


t0 = time.perf_counter()
with ThreadPoolExecutor(WORKERS) as ex:
    lat = sorted(ex.map(one, range(N)))
wall = time.perf_counter() - t0
res = {"n": N, "concurrent_clients": WORKERS, "requests_per_s": round(N / wall, 2), "wall_s": round(wall, 1),
       "mean_ms": round(statistics.mean(lat), 1), "p50_ms": round(lat[len(lat) // 2], 1), "p95_ms": round(lat[int(len(lat) * 0.95) - 1], 1)}
print(json.dumps(res, indent=1))
json.dump(res, open(f"results/throughput_{TAG}.json", "w"), indent=1)
