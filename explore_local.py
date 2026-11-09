"""Print schema + label counts for the gated / streamed datasets (needs HF login). Output -> data/explore_local.txt"""
import collections, json, itertools
from datasets import load_dataset, get_dataset_config_names

def head(ds, n=1):
    for i, r in enumerate(ds):
        print("   ", json.dumps(r, default=str)[:400])
        if i + 1 >= n: break

def counts(ds, col, k=40):
    c = collections.Counter(str(r[col]) for r in ds)
    print(f"   {col}: {len(c)} values ->", c.most_common(k))

print("=" * 70, "WildGuardMix")
print("configs:", get_dataset_config_names("allenai/wildguardmix"))
wg = load_dataset("allenai/wildguardmix", "wildguardtrain")
for s in wg:
    d = wg[s]; print("--", s, len(d), d.column_names); head(d)
    for col in ("adversarial", "prompt_harm_label", "response_harm_label", "response_refusal_label", "subcategory"):
        if col in d.column_names: counts(d, col)
    ct = collections.Counter((r["subcategory"], r["adversarial"], r["prompt_harm_label"]) for r in d)
    for k, v in sorted(ct.items(), key=lambda x: -x[1]): print("   XT", k, v)

print("=" * 70, "XSTest")
print("configs:", get_dataset_config_names("walledai/XSTest"))
xs = load_dataset("walledai/XSTest")
for s in xs:
    d = xs[s]; print("--", s, len(d), d.column_names); head(d)
    for col in ("label", "type", "focus"):
        if col in d.column_names: counts(d, col)

print("=" * 70, "rogue-security/prompt-injections-benchmark")
print("configs:", get_dataset_config_names("rogue-security/prompt-injections-benchmark"))
pib = load_dataset("rogue-security/prompt-injections-benchmark")
for s in pib:
    d = pib[s]; print("--", s, len(d), d.column_names); head(d, 2)
    for col in d.column_names:
        if col.lower() in ("label", "type", "category", "source"): counts(d, col)

print("=" * 70, "civil_comments (streamed, first 20k)")
cc = load_dataset("google/civil_comments", split="train", streaming=True)
n = hit = 0
for r in itertools.islice(cc, 20000):
    n += 1
    if r["insult"] >= 0.7 and r["identity_attack"] < 0.2 and r["threat"] < 0.2 and r["sexual_explicit"] < 0.2:
        hit += 1
        if hit <= 3: print("   HIT", json.dumps(r, default=str)[:300])
print(f"   scanned {n}, matched {hit} -> est. need ~{int(300 * n / max(hit,1))} rows streamed for 300")
