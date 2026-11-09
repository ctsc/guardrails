"""Fill the result markers in README.md / SLIDES.md / PROGRESS.md from results/*.json (run by run_fixes.cmd after the evals)."""
from __future__ import annotations

import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
os.chdir(HERE)


def fill(path: str, tag: str, body: str) -> None:
    s = open(path, encoding="utf-8").read()
    pat = re.compile(rf"<!-- {tag} -->.*?<!-- /{tag} -->", re.S)
    assert pat.search(s), (path, tag)
    s = pat.sub(f"<!-- {tag} -->\n{body}\n<!-- /{tag} -->", s, count=1)
    open(path, "w", encoding="utf-8", newline="\n").write(s)


def pct(x):
    return "-" if x is None else f"{100 * x:.1f}%"


SET_NAMES = {"aegis_test": "Aegis 2.0 test", "openai_moderation": "OpenAI moderation eval", "prompt_attack_pib": "Prompt-injection benchmark",
             "safeguard_test_secondary": "safe-guard injection test", "overblock_xstest": "XSTest safe (over-blocking)", "overblock_jbb": "JailbreakBench benign (over-blocking)",
             "all_input_rows": "all user-input rows", "all_output_rows": "all model-output rows"}

# ---- demo table
demo = json.load(open("results/demo_table.json", encoding="utf-8"))
lines = ["| demo prompt | expected | got | action | result |", "|---|---|---|---|---|"]
for r in demo:
    got = f"**{r['got']}**" if r["result"] == "WRONG" else r["got"]
    lines.append(f"| \"{r['text'].strip()}...\" | {r['expected']} | {got} | {r['action']} | {r['result']} |")
n_ok = sum(r["result"] == "RIGHT" for r in demo)
lines.append("")
lines.append(f"{n_ok}/{len(demo)} right.")
fill("README.md", "DEMO_TABLE", "\n".join(lines))
row6 = demo[5] if len(demo) > 5 else None
if row6:
    fill("SLIDES.md", "DEMO_ROW6", f"{row6['got']} ({'the deliberate miss' if row6['result'] == 'WRONG' else 'caught, so pick another miss'})")

# ---- Llama Guard vs ours
summary_lines = []
if os.path.exists("results/eval_llamaguard.json"):
    lg = json.load(open("results/eval_llamaguard.json", encoding="utf-8"))["sets"]
    ours = json.load(open("results/eval_finetuned.json", encoding="utf-8"))["sets"]
    lines = ["| test set | n | ours: flag recall | Llama Guard: flag recall | ours: FPR | Llama Guard: FPR |", "|---|---|---|---|---|---|"]
    for k, name in SET_NAMES.items():
        if k in lg and k in ours:
            o, l = ours[k], lg[k]
            lines.append(f"| {name} | {o['n']} | {pct(o.get('flag_recall'))} | {pct(l.get('flag_recall'))} | {pct(o.get('false_positive_rate'))} | {pct(l.get('false_positive_rate'))} |")
    lines.append("")
    lines.append(f"Llama Guard 3 1B took {json.load(open('results/eval_llamaguard.json'))['seconds']} s for 2,960 rows on the GTX 1660 Ti (4 parallel slots). "
                 "Its 7-way accuracy is in `results/eval_llamaguard.md` but is not comparable (no insults / prompt-attack classes).")
    fill("README.md", "LG_TABLE", "\n".join(lines))
    a_o, a_l = ours["all_input_rows"], lg["all_input_rows"]
    p_o, p_l = ours.get("prompt_attack_pib", {}), lg.get("prompt_attack_pib", {})
    x_o, x_l = ours.get("overblock_xstest", {}), lg.get("overblock_xstest", {})
    slide = (f"- **Baseline, Llama Guard 3 1B (Meta), same 2,960 rows, binary flag/safe:** all input rows flag recall {pct(a_o.get('flag_recall'))} ours vs {pct(a_l.get('flag_recall'))} Llama Guard, "
             f"FPR {pct(a_o.get('false_positive_rate'))} vs {pct(a_l.get('false_positive_rate'))}; prompt-injection benchmark recall {pct(p_o.get('flag_recall'))} vs {pct(p_l.get('flag_recall'))} "
             f"(Llama Guard has no prompt-attack class); XSTest over-blocking {pct(x_o.get('false_positive_rate'))} vs {pct(x_l.get('false_positive_rate'))}.")
    fill("SLIDES.md", "LG_SLIDE", slide)
    summary_lines.append(slide.lstrip("- "))

# ---- PROGRESS summary
summary_lines.insert(0, f"- Demo after fixes: {n_ok}/{len(demo)} right; " + "; ".join(f"{r['expected']} -> {r['got']} ({r['result']})" for r in demo))
if os.path.exists("results/throughput_laptop.json"):
    t = json.load(open("results/throughput_laptop.json"))
    summary_lines.append(f"- Throughput on the laptop, {t['concurrent_clients']} concurrent clients, n={t['n']}: **{t['requests_per_s']} req/s**, mean {t['mean_ms']} ms, p95 {t['p95_ms']} ms per request")
fill("PROGRESS.md", "FIXES_PROGRESS", "\n".join(f"- {l}" if not l.startswith("- ") else l for l in summary_lines))
print("docs filled")
