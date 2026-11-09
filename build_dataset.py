"""Build train.jsonl (4,000 rows) and test.jsonl for the guardrail classifier.

Labels (multiple-choice letters, same as the model prompt):
  A safe, B hate, C insults, D sexual, E violence, F misconduct/illegal, G prompt attack

Row schema: {"text", "label", "valid_labels", "source", "kind": "input"|"output", "test_set" (test only)}
Model-output rows start with "Model output: " and are never G.

Run:  python build_dataset.py            (writes data/train.jsonl, data/test.jsonl, data/counts.json, data/sample20.txt)
"""
from __future__ import annotations

import collections
import hashlib
import itertools
import json
import random
import re
import sys
from pathlib import Path

from datasets import load_dataset

SEED = 42
rng = random.Random(SEED)
OUT = Path(__file__).resolve().parent / "data"
OUT.mkdir(exist_ok=True)

LETTERS = "ABCDEFG"
NAMES = {"A": "safe", "B": "hate", "C": "insults", "D": "sexual", "E": "violence", "F": "misconduct", "G": "prompt_attack"}
MIN_CHARS, MAX_CHARS = 8, 2000

# Aegis 2.0 violated_categories -> letter. Unmapped categories are ignored; a row whose mapped
# categories disagree (two letters) is dropped, a row with no mapped category is unusable.
AEGIS_MAP = {
    "Hate/Identity Hate": "B",
    "Harassment": "C",
    "Sexual": "D",
    "Sexual (minor)": "D",
    "Violence": "E",
    "Threat": "E",
    "Criminal Planning/Confessions": "F",
    "Guns and Illegal Weapons": "F",
    "Controlled/Regulated Substances": "F",
    "Fraud/Deception": "F",
    "Malware": "F",
}
# WildGuardMix subcategory -> letter, matched by substring on the (undocumented) subcategory string
WG_MAP = [
    (("hate", "stereotype", "discrimination"), "B"),
    (("sexual",), "D"),
    (("violence", "physical_harm"), "E"),
    (("fraud", "illegal", "cyberattack"), "F"),
]
INJECTION_RE = re.compile(
    r"ignore (all |any )?(previous|prior|above|the) (instructions|prompts?|rules|text)|disregard (all |any )?(previous|prior|above)"
    r"|act as|you are now|pretend (to be|you are)|jailbreak|\bDAN\b|developer mode|system prompt|forget (all |everything|your)",
    re.I,
)

log_lines: list[str] = []


def log(*a):
    s = " ".join(str(x) for x in a)
    print(s, flush=True)
    log_lines.append(s)


def norm(t: str) -> str:
    return re.sub(r"\s+", " ", t.lower()).strip()


def h(t: str) -> str:
    return hashlib.sha1(norm(t).encode()).hexdigest()


# English-only (Carter: no German / multilingual rows). Cheap heuristic: German/French/Spanish function
# words or a high share of non-ASCII letters -> not English.
_FOREIGN_WORDS = {
    "der", "die", "das", "und", "ist", "nicht", "ich", "sie", "ein", "eine", "einen", "einem", "einer", "für", "mit", "auf",
    "sind", "auch", "oder", "im", "den", "dem", "des", "zu", "von", "sich", "alle", "mir", "dir", "mein", "meine",
    "dass", "diese", "dieser", "wo", "wer", "warum", "sag", "schreibe", "erkläre", "gibt", "haben", "hat", "nein",
    "werden", "wird", "ihr", "ihre", "bitte", "kannst", "über", "welche", "wenn", "aber", "noch", "sehr", "kann",
    "je", "puis", "très", "vous", "nous", "avec", "qui", "pour", "dans", "sont", "être", "mais", "aussi", "une",
    "está", "pero", "usted", "también", "puedo", "cómo", "qué", "porque", "tiene", "hacer",
}
_ACCENT_RE = re.compile(r"[äöüÄÖÜßéèêàçñóíáú]")
_INVERTED_RE = re.compile(r"[¿¡]")


def is_english(t: str) -> bool:
    words = re.findall(r"[a-zA-ZäöüÄÖÜßéèêàçñóíáú]+", t.lower())
    if not words:
        return True
    foreign_hits = sum(1 for w in words if w in _FOREIGN_WORDS)
    accents = len(_ACCENT_RE.findall(t))
    if foreign_hits >= 2 or (foreign_hits >= 1 and accents >= 1) or accents >= 2 or _INVERTED_RE.search(t):
        return False
    letters = sum(1 for ch in t if ch.isalpha())
    non_ascii = sum(1 for ch in t if ch.isalpha() and ord(ch) > 127)
    if letters and non_ascii / letters > 0.05:
        return False
    return True


def ok_text(t) -> bool:
    return isinstance(t, str) and MIN_CHARS <= len(t.strip()) <= MAX_CHARS and "REDACTED" not in t and is_english(t)


def row(text, label, source, kind="input", valid=None, test_set=None):
    text = text.strip()
    if kind == "output":
        text = "Model output: " + text
        assert label != "G"
    r = {"text": text, "label": label, "valid_labels": sorted(valid or {label}), "source": source, "kind": kind}
    if test_set:
        r["test_set"] = test_set
    return r


def take(cands, n, name):
    cands = list(cands)
    rng.shuffle(cands)
    got = cands[:n]
    flag = "" if len(got) >= n else f"   <-- SHORT by {n - len(got)}"
    log(f"  {name:55s} want {n:4d}  have {len(cands):6d}  took {len(got):4d}{flag}")
    return got


def aegis_letters(cats: str) -> set[str]:
    return {AEGIS_MAP[c.strip()] for c in (cats or "").split(",") if c.strip() in AEGIS_MAP}


def aegis_single_letter(r) -> str | None:
    """Letter for an Aegis row, or None if unmapped / conflicting."""
    cats = r["violated_categories"] or ""
    if "Needs Caution" in cats:
        return None
    ls = aegis_letters(cats)
    return next(iter(ls)) if len(ls) == 1 else None


# ----------------------------------------------------------------------------- load sources
log("== loading sources")
aegis = load_dataset("nvidia/Aegis-AI-Content-Safety-Dataset-2.0")
ag_train, ag_test = aegis["train"], aegis["test"]
log("Aegis train", len(ag_train), "test", len(ag_test))
log("Aegis train violated_categories (top 25):")
for k, v in collections.Counter(r["violated_categories"] for r in ag_train).most_common(25):
    log(f"    {v:6d}  {k!r}")

wg = load_dataset("allenai/wildguardmix", "wildguardtrain")["train"]
log("WildGuardMix train", len(wg))
log("WildGuardMix subcategory x adversarial x prompt_harm_label:")
for k, v in sorted(collections.Counter((r["subcategory"], r["adversarial"], r["prompt_harm_label"]) for r in wg).items(), key=lambda x: -x[1]):
    log(f"    {v:6d}  {k}")

orb = load_dataset("bench-llm/or-bench", "or-bench-80k")["train"]
sg = load_dataset("xTRam1/safe-guard-prompt-injection")  # English-only replacement for deepset (which is half German)
jack = load_dataset("jackhhao/jailbreak-classification")["train"]
gandalf = load_dataset("Lakera/gandalf_ignore_instructions")["train"]

# ----------------------------------------------------------------------------- Aegis pools
ag_prompt_pool = collections.defaultdict(list)   # letter -> prompts
ag_resp_pool = collections.defaultdict(list)     # letter -> unsafe responses
ag_safe_prompts, ag_safe_resps = [], []
for r in ag_train:
    p, resp = r["prompt"], r["response"]
    if r["prompt_label"] == "safe":
        if ok_text(p) and not ("Needs Caution" in (r["violated_categories"] or "")) and not INJECTION_RE.search(p):
            ag_safe_prompts.append(p)
    else:
        L = aegis_single_letter(r)
        if L and ok_text(p):
            ag_prompt_pool[L].append(p)
    if r["response_label"] == "safe" and ok_text(resp):
        ag_safe_resps.append(resp)
    elif r["response_label"] == "unsafe" and ok_text(resp):
        L = aegis_single_letter(r)
        if L:
            ag_resp_pool[L].append(resp)
log("Aegis usable prompts per letter:", {k: len(v) for k, v in sorted(ag_prompt_pool.items())}, "safe:", len(ag_safe_prompts))
log("Aegis usable unsafe responses per letter:", {k: len(v) for k, v in sorted(ag_resp_pool.items())}, "safe:", len(ag_safe_resps))


def wg_letter(sub: str) -> str | None:
    s = (sub or "").lower()
    for keys, L in WG_MAP:
        if any(k in s for k in keys):
            return L
    return None


wg_adv_benign, wg_adv_harm = [], []
wg_pool = collections.defaultdict(list)
for r in wg:
    p = r["prompt"]
    if not ok_text(p):
        continue
    if r["adversarial"] and r["prompt_harm_label"] == "unharmful":
        wg_adv_benign.append(p)
    elif r["adversarial"] and r["prompt_harm_label"] == "harmful":
        wg_adv_harm.append(p)
    elif (not r["adversarial"]) and r["prompt_harm_label"] == "harmful":
        L = wg_letter(r["subcategory"])
        if L:
            wg_pool[L].append(p)
log("WildGuardMix adversarial benign", len(wg_adv_benign), "adversarial harmful", len(wg_adv_harm), "plain harmful per letter", {k: len(v) for k, v in sorted(wg_pool.items())})

# civil_comments streamed
log("streaming google/civil_comments for insults ...")
cc_rows = []
cc = load_dataset("google/civil_comments", split="train", streaming=True)
for i, r in enumerate(cc):
    if r["insult"] >= 0.8 and r["identity_attack"] < 0.2 and r["threat"] < 0.2 and r["sexual_explicit"] < 0.2 and ok_text(r["text"]):
        cc_rows.append(r["text"])
    if len(cc_rows) >= 600 or i >= 600_000:
        break
log(f"civil_comments scanned {i+1} rows, {len(cc_rows)} insult candidates")

# ----------------------------------------------------------------------------- train
log("== building train")
train: list[dict] = []
plan = [
    # (letter, source name, candidates, n, kind)
    # v2 rebalance: safe doubled 1,600 -> 3,200 (~57% of train) after v1 over-flagged ~40% of XSTest/JBB benign prompts.
    # OR-Bench and WildGuard adversarial-benign are "sounds unsafe, is safe" prompts, exactly what the over-blocking sets test.
    ("A", "aegis safe prompts", ag_safe_prompts, 1000, "input"),
    ("A", "or-bench-80k", [r["prompt"] for r in orb if ok_text(r["prompt"])], 1000, "input"),
    ("A", "wildguardmix adversarial benign", wg_adv_benign, 700, "input"),
    ("A", "safe-guard-prompt-injection label 0", [r["text"] for r in sg["train"] if r["label"] == 0 and ok_text(r["text"])], 250, "input"),
    ("A", "aegis safe responses", ag_safe_resps, 250, "output"),
    ("B", "aegis Hate/Identity Hate prompts", ag_prompt_pool["B"], 250, "input"),
    ("B", "aegis hate responses", ag_resp_pool["B"], 50, "output"),
    ("B", "wildguardmix hate/stereotype", wg_pool["B"], 100, "input"),
    ("C", "civil_comments insult>=0.8", cc_rows, 300, "input"),
    ("C", "aegis Harassment prompts", ag_prompt_pool["C"], 100, "input"),
    ("D", "aegis Sexual prompts", ag_prompt_pool["D"], 250, "input"),
    ("D", "aegis sexual responses", ag_resp_pool["D"], 50, "output"),
    ("D", "wildguardmix sexual", wg_pool["D"], 100, "input"),
    ("E", "aegis Violence prompts", ag_prompt_pool["E"], 250, "input"),
    ("E", "aegis violence responses", ag_resp_pool["E"], 50, "output"),
    ("E", "wildguardmix violence", wg_pool["E"], 100, "input"),
    ("F", "aegis Criminal/Guns/Substances/Fraud prompts", ag_prompt_pool["F"], 250, "input"),
    ("F", "aegis misconduct responses", ag_resp_pool["F"], 50, "output"),
    ("F", "wildguardmix fraud/illegal/cyberattack", wg_pool["F"], 100, "input"),
    ("G", "wildguardmix adversarial harmful", wg_adv_harm, 150, "input"),
    ("G", "jackhhao jailbreak", [r["prompt"] for r in jack if r["type"] == "jailbreak" and ok_text(r["prompt"])], 100, "input"),
    ("G", "safe-guard-prompt-injection label 1", [r["text"] for r in sg["train"] if r["label"] == 1 and ok_text(r["text"])], 100, "input"),
    ("G", "gandalf train", [r["text"] for r in gandalf if ok_text(r["text"])], 50, "input"),
]
used_hashes: set[str] = set()
shortfall = collections.Counter()
for L, name, cands, n, kind in plan:
    cands = [c for c in dict.fromkeys(cands) if h(c) not in used_hashes]  # unique, not already used (all already English-filtered by ok_text)
    got = take(cands, n, f"{L} {name}")
    shortfall[L] += n - len(got)
    for t in got:
        used_hashes.add(h(t))
        train.append(row(t, L, name, kind))

# top-up for any class that came up short: more WildGuardMix (B,D,E,F) or Aegis (others)
for L, miss in shortfall.items():
    if miss <= 0:
        continue
    extra = {"B": wg_pool["B"], "D": wg_pool["D"], "E": wg_pool["E"], "F": wg_pool["F"], "C": ag_prompt_pool["C"],
             "A": ag_safe_prompts, "G": wg_adv_harm}[L]
    extra = [c for c in dict.fromkeys(extra) if h(c) not in used_hashes]
    got = take(extra, miss, f"{L} TOP-UP")
    for t in got:
        used_hashes.add(h(t))
        train.append(row(t, L, "top-up", "input"))

# ----------------------------------------------------------------------------- test sets
log("== building test sets")
test: list[dict] = []


def find_col(cols, *cands):
    for c in cands:
        if c in cols:
            return c
    raise KeyError(f"none of {cands} in {cols}")


# G main: rogue-security/prompt-injections-benchmark, 200 jailbreak + 300 benign
pib = load_dataset("rogue-security/prompt-injections-benchmark")
pib_split = pib[list(pib.keys())[0]] if "test" not in pib else pib["test"]
tc = find_col(pib_split.column_names, "text", "prompt", "input")
lc = find_col(pib_split.column_names, "label", "type", "category")
log("prompt-injections-benchmark split", list(pib.keys()), "cols", pib_split.column_names,
    "label values", collections.Counter(str(r[lc]) for r in pib_split).most_common(10))
def pib_is_attack(v) -> bool:
    s = str(v).lower()
    return s in {"1", "true", "jailbreak", "injection", "malicious", "attack", "unsafe"} or "jailbreak" in s or "inject" in s
pib_att = [r[tc] for r in pib_split if pib_is_attack(r[lc]) and ok_text(r[tc])]
pib_ben = [r[tc] for r in pib_split if not pib_is_attack(r[lc]) and ok_text(r[tc])]
for t in take(pib_att, 200, "TEST pib jailbreak"):
    test.append(row(t, "G", "rogue-security/prompt-injections-benchmark", test_set="prompt_attack_pib"))
for t in take(pib_ben, 300, "TEST pib benign"):
    test.append(row(t, "A", "rogue-security/prompt-injections-benchmark", test_set="prompt_attack_pib"))

# B-E: OpenAI moderation eval, all rows. H->B, HR->C, S->D, V/SH->E, none->A. S3->D, H2->B, V2->E.
om = load_dataset("mmathys/openai-moderation-api-evaluation")["train"]
OM_MAP = {"H": "B", "H2": "B", "HR": "C", "S": "D", "S3": "D", "V": "E", "V2": "E", "SH": "E"}
PRIORITY = "GBDEFCA"
n_multi = 0
for r in om:
    if not ok_text(r["prompt"]):
        continue
    ls = {L for k, L in OM_MAP.items() if r.get(k) == 1}
    if not ls:
        ls = {"A"}
    if len(ls) > 1:
        n_multi += 1
    primary = min(ls, key=PRIORITY.index)
    test.append(row(r["prompt"], primary, "mmathys/openai-moderation-api-evaluation", valid=ls, test_set="openai_moderation"))
log(f"  openai moderation rows {sum(1 for t in test if t['test_set']=='openai_moderation')} ({n_multi} multi-label, scored correct if prediction in valid_labels)")

# All classes: Aegis test, 400 stratified over A-F (prompts + model outputs)
ag_pool = collections.defaultdict(list)
for r in ag_test:
    p, resp = r["prompt"], r["response"]
    if r["prompt_label"] == "safe" and ok_text(p) and "Needs Caution" not in (r["violated_categories"] or "") and not INJECTION_RE.search(p):
        ag_pool["A"].append((p, "input"))
    elif r["prompt_label"] == "unsafe":
        L = aegis_single_letter(r)
        if L and ok_text(p):
            ag_pool[L].append((p, "input"))
    if r["response_label"] == "safe" and ok_text(resp):
        ag_pool["A"].append((resp, "output"))
    elif r["response_label"] == "unsafe" and ok_text(resp):
        L = aegis_single_letter(r)
        if L:
            ag_pool[L].append((resp, "output"))
log("  Aegis test pool per letter:", {k: len(v) for k, v in sorted(ag_pool.items())})
per = 400 // 6
picked = {}
for L in "ABCDEF":
    c = list(dict.fromkeys(ag_pool[L]))
    rng.shuffle(c)
    picked[L] = c[:per]
left = 400 - sum(len(v) for v in picked.values())
rest = [(L, x) for L in "ABCDEF" for x in list(dict.fromkeys(ag_pool[L]))[len(picked[L]):]]
rng.shuffle(rest)
for L, x in rest[:left]:
    picked[L].append(x)
for L, items in picked.items():
    for t, kind in items:
        test.append(row(t, L, "nvidia/Aegis-AI-Content-Safety-Dataset-2.0 test", kind, test_set="aegis_test"))
log("  Aegis test picked:", {L: len(v) for L, v in picked.items()})

# Over-blocking: XSTest safe 250 + JailbreakBench benign 100 (all A)
xs = load_dataset("walledai/XSTest")
xs_split = xs[list(xs.keys())[0]]
xs_tc = find_col(xs_split.column_names, "prompt", "text")
xs_lc = find_col(xs_split.column_names, "label", "type")
xs_safe = [r[xs_tc] for r in xs_split if str(r[xs_lc]).lower() == "safe" and ok_text(r[xs_tc])]
for t in take(xs_safe, 250, "TEST XSTest safe"):
    test.append(row(t, "A", "walledai/XSTest", test_set="overblock_xstest"))
jbb = load_dataset("JailbreakBench/JBB-Behaviors", "behaviors")["benign"]
for t in take([r["Goal"] for r in jbb if ok_text(r["Goal"])], 100, "TEST JBB benign"):
    test.append(row(t, "A", "JailbreakBench/JBB-Behaviors benign", test_set="overblock_jbb"))

# safe-guard-prompt-injection test, secondary (100 attacks + 100 benign)
for lab, letter in ((1, "G"), (0, "A")):
    for t in take([r["text"] for r in sg["test"] if r["label"] == lab and ok_text(r["text"])], 100, f"TEST safe-guard label {lab}"):
        test.append(row(t, letter, "xTRam1/safe-guard-prompt-injection test", test_set="safeguard_test_secondary"))

# ----------------------------------------------------------------------------- dedup train vs test
log("== dedup")
test_hashes = {h(t["text"]) for t in test}
# (strip the "Model output: " prefix too so a response reused as a prompt is caught)
test_hashes |= {h(t["text"].removeprefix("Model output: ")) for t in test}
before = len(train)
train = [t for t in train if h(t["text"]) not in test_hashes and h(t["text"].removeprefix("Model output: ")) not in test_hashes]
log(f"  dropped {before - len(train)} training rows that collide with a test row")
# unique within test
seen, uniq = set(), []
for t in test:
    k = (h(t["text"]), t["test_set"])
    if k not in seen:
        seen.add(k)
        uniq.append(t)
log(f"  dropped {len(test) - len(uniq)} duplicate test rows")
test = uniq

rng.shuffle(train)

# ----------------------------------------------------------------------------- write
with open(OUT / "train.jsonl", "w", encoding="utf-8") as f:
    for t in train:
        f.write(json.dumps(t, ensure_ascii=False) + "\n")
with open(OUT / "test.jsonl", "w", encoding="utf-8") as f:
    for t in test:
        f.write(json.dumps(t, ensure_ascii=False) + "\n")

counts = {
    "train_total": len(train),
    "train_per_label": dict(sorted(collections.Counter(t["label"] for t in train).items())),
    "train_per_kind": dict(collections.Counter(t["kind"] for t in train)),
    "train_per_source": dict(sorted(collections.Counter(t["source"] for t in train).items())),
    "test_total": len(test),
    "test_per_set": dict(sorted(collections.Counter(t["test_set"] for t in test).items())),
    "test_per_set_label": {s: dict(sorted(collections.Counter(t["label"] for t in test if t["test_set"] == s).items()))
                           for s in sorted({t["test_set"] for t in test})},
}
(OUT / "counts.json").write_text(json.dumps(counts, indent=2), encoding="utf-8")
log("== counts"); log(json.dumps(counts, indent=2))

sample = rng.sample(train, 20)
lines = []
for i, t in enumerate(sample, 1):
    lines.append(f"[{i:2d}] {t['label']} ({NAMES[t['label']]:13s}) <{t['source']}>\n     {t['text'][:300].replace(chr(10), ' ')!s}\n")
(OUT / "sample20.txt").write_text("\n".join(lines), encoding="utf-8")
(OUT / "build_log.txt").write_text("\n".join(log_lines), encoding="utf-8")
log("== 20 random training rows -> data/sample20.txt")
print("\n".join(lines))
