"""AWS-shaped guardrail API.

POST /guardrail/apply  -> same JSON shape as Bedrock ApplyGuardrail: action, actionReason, outputs (masked text), assessments
POST /chat             -> runs the guardrail on the user message (and on the model reply), then calls an OpenAI-compatible upstream
GET  /healthz
Privacy: logs store category + sha256 of the text, never the raw text.
"""
from __future__ import annotations

import hashlib
import logging
import time
from typing import Literal

import requests
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

import decode
import pii
from scorer import LETTERS, Scorer, load_config

log = logging.getLogger("guardrail")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")

app = FastAPI(title="local-guardrails", version="0.1")
CFG = load_config()
_scorer: Scorer | None = None

STRENGTH_BLOCKS = {"HIGH": {"LOW", "MEDIUM", "HIGH"}, "MEDIUM": {"MEDIUM", "HIGH"}, "LOW": {"HIGH"}, "NONE": set()}


def get_scorer() -> Scorer:
    global _scorer
    if _scorer is None:
        _scorer = Scorer(CFG)
    return _scorer


class TextBlock(BaseModel):
    text: str


class ContentItem(BaseModel):
    text: TextBlock


class ApplyRequest(BaseModel):
    source: Literal["INPUT", "OUTPUT"] = "INPUT"
    content: list[ContentItem]


def confidence_for(p: float) -> str | None:
    c = CFG["confidence"]
    if p >= c["HIGH"]:
        return "HIGH"
    if p >= c["MEDIUM"]:
        return "MEDIUM"
    if p >= c["LOW"]:
        return "LOW"
    return None


def apply_guardrail(text: str, source: str = "INPUT", probs: dict[str, float] | None = None) -> dict:
    """Core logic, separated from FastAPI so tests can call it with precomputed probabilities."""
    t0 = time.perf_counter()
    reasons: list[str] = []

    # 1) PII first: the model never sees raw PII
    pii_cfg = CFG["sensitive_information_policy"]["pii_entities"]
    masked, ents = pii.mask(text, types=[k for k, v in pii_cfg.items() if v != "NONE"])
    pii_entities = []
    pii_block = False
    for e in ents:
        action = pii_cfg.get(e["type"], "NONE")
        pii_entities.append({"type": e["type"], "match": e["text"], "action": "BLOCKED" if action == "BLOCK" else "ANONYMIZED"})
        if action == "BLOCK":
            pii_block = True
            reasons.append(f"PII {e['type']} blocked")

    # 2) model: one forward pass per text variant, read letter probabilities. Variants = the text itself plus any
    #    base64 / URL-encoded payload it carries (decode-and-rescan), so an encoded injection is judged in the clear.
    decoded = decode.decoded_payloads(masked) if CFG.get("decode_and_rescan", True) else []
    if probs is None:
        prefix = "" if source == "INPUT" else "Model output: "
        scored = [get_scorer().score(prefix + v)["probs"] for v in [masked, *decoded]]
        probs = max(scored, key=lambda p: 1.0 - p["A"])
        if decoded:
            reasons_decoded = max(scored[1:], key=lambda p: 1.0 - p["A"])
            if reasons_decoded is probs and probs["A"] < 0.5:
                reasons.append("detected in decoded payload")
    filters = []
    content_block = False
    strength_key = "input_strength" if source == "INPUT" else "output_strength"
    for name, f in CFG["content_policy"]["filters"].items():
        p = probs[f["letter"]]
        conf = confidence_for(p)
        strength = f[strength_key]
        detected = conf is not None and f["letter"] == max(probs, key=probs.get)
        blocked = detected and conf in STRENGTH_BLOCKS[strength]
        if detected:
            filters.append({"type": name, "confidence": conf, "filterStrength": strength, "action": "BLOCKED" if blocked else "NONE",
                            "detected": True, "score": round(p, 4)})
        if blocked:
            content_block = True
            reasons.append(f"{name} {conf}")

    intervened = pii_block or content_block or bool(pii_entities)
    if pii_block or content_block:
        out_text = CFG["blocked_input_message"] if source == "INPUT" else CFG["blocked_output_message"]
    else:
        out_text = masked
    latency_ms = round((time.perf_counter() - t0) * 1000, 1)
    log.info("source=%s sha256=%s top=%s action=%s latency_ms=%s", source, hashlib.sha256(text.encode()).hexdigest()[:16],
             max(probs, key=probs.get), "BLOCKED" if (pii_block or content_block) else ("MASKED" if pii_entities else "NONE"), latency_ms)
    return {
        "usage": {"contentPolicyUnits": 1, "sensitiveInformationPolicyUnits": 1},
        "action": "GUARDRAIL_INTERVENED" if intervened else "NONE",
        "actionReason": "; ".join(reasons) if reasons else ("PII anonymized" if pii_entities else "No policy violation"),
        "outputs": [{"text": out_text}],
        "assessments": [{
            "contentPolicy": {"filters": filters},
            "sensitiveInformationPolicy": {"piiEntities": pii_entities},
            "invocationMetrics": {"guardrailProcessingLatency": latency_ms},
            "scores": {L: round(probs[L], 4) for L in LETTERS},
            "decodedPayloads": decoded,
        }],
        "blocked": pii_block or content_block,
    }


@app.get("/healthz")
def healthz():
    return {"api": "ok", "llama_server": get_scorer().healthy()}


@app.post("/guardrail/apply")
def guardrail_apply(req: ApplyRequest):
    text = "\n".join(c.text.text for c in req.content)
    if not text.strip():
        raise HTTPException(400, "empty content")
    try:
        return apply_guardrail(text, req.source)
    except requests.RequestException as e:
        raise HTTPException(503, f"llama-server unreachable: {e}")


class ChatRequest(BaseModel):
    message: str
    guardrails: bool = True


def call_upstream(message: str) -> str:
    c = CFG["chat"]
    r = requests.post(c["upstream_url"], json={"messages": [{"role": "user", "content": message}], "max_tokens": c.get("max_tokens", 200),
                                               "temperature": 0.7, "chat_template_kwargs": {"enable_thinking": False}}, timeout=120)
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"]


@app.post("/chat")
def chat(req: ChatRequest):
    if not req.guardrails:
        return {"reply": call_upstream(req.message), "guardrail": None}
    g_in = apply_guardrail(req.message, "INPUT")
    if g_in["blocked"]:
        return {"reply": g_in["outputs"][0]["text"], "guardrail": {"input": g_in, "output": None}}
    reply = call_upstream(g_in["outputs"][0]["text"])  # masked text goes upstream
    g_out = apply_guardrail(reply, "OUTPUT")
    return {"reply": g_out["outputs"][0]["text"], "guardrail": {"input": g_in, "output": g_out}}
