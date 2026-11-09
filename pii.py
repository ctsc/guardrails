"""Regex PII masking. Runs before the model sees the text, so the model never gets raw emails, phones, cards, SSNs, IPs, street addresses, birth dates, cloud keys.

mask(text) -> (masked_text, [(entity_type, original_span), ...])
"""
from __future__ import annotations

import re

# Order matters: longer / more specific patterns first so e.g. a card number is not eaten by the phone pattern.
PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("EMAIL", re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")),
    ("CREDIT_CARD", re.compile(r"\b(?:\d[ -]?){13,15}\d\b")),
    ("SSN", re.compile(r"\b\d{3}-\d{2}-\d{4}\b")),
    ("PHONE", re.compile(r"(?<!\w)(?:\+?1[ .-]?)?(?:\(\d{3}\)|\d{3})[ .-]?\d{3}[ .-]?\d{4}(?!\w)")),
    ("IP_ADDRESS", re.compile(r"\b(?:(?:25[0-5]|2[0-4]\d|1?\d?\d)\.){3}(?:25[0-5]|2[0-4]\d|1?\d?\d)\b")),
    ("URL", re.compile(r"\bhttps?://[^\s<>\"']+", re.I)),
    ("AWS_ACCESS_KEY", re.compile(r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b")),
    ("US_ADDRESS", re.compile(r"\b\d{1,6}\s+(?:[A-Z][A-Za-z]+\s){1,3}(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Lane|Ln|Drive|Dr|Court|Ct|Way|Place|Pl|Terrace|Ter|Highway|Hwy)\b\.?(?:,?\s*(?:Apt|Suite|Ste|Unit|#)\.?\s*\w+)?")),
    # only the date is masked (group 1); a bare date is not PII, a date introduced as a birth date is
    ("DATE_OF_BIRTH", re.compile(r"(?:\bDOB\b|date of birth|\bborn(?: on)?\b|\bbirthday\b)\s*(?:is|was|:)?\s*(\d{1,2}[/.-]\d{1,2}[/.-]\d{2,4}|(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)[a-z]*\.?\s+\d{1,2},?\s+\d{4}|\d{4}-\d{2}-\d{2})", re.I)),
]


def _luhn_ok(digits: str) -> bool:
    total, alt = 0, False
    for ch in reversed(digits):
        d = int(ch)
        if alt:
            d = d * 2
            if d > 9:
                d -= 9
        total += d
        alt = not alt
    return total % 10 == 0


def mask(text: str, types: list[str] | None = None) -> tuple[str, list[dict]]:
    """Replace each PII span with [TYPE]. `types` limits which entity types are masked (default: all)."""
    found: list[dict] = []
    spans: list[tuple[int, int, str]] = []
    for name, pat in PATTERNS:
        if types is not None and name not in types:
            continue
        for m in pat.finditer(text):
            s, e = m.span(1) if m.lastindex else m.span()
            if name == "CREDIT_CARD" and not _luhn_ok(re.sub(r"\D", "", m.group())):
                continue
            if any(not (e <= s0 or s >= e0) for s0, e0, _ in spans):  # overlaps an earlier, higher-priority match
                continue
            spans.append((s, e, name))
    spans.sort()
    out, last = [], 0
    for s, e, name in spans:
        out.append(text[last:s])
        out.append(f"[{name}]")
        found.append({"type": name, "start": s, "end": e, "text": text[s:e]})
        last = e
    out.append(text[last:])
    return "".join(out), found


if __name__ == "__main__":
    demo = "Email me at jane.doe@example.com or call (555) 123-4567. Card 4111 1111 1111 1111, SSN 123-45-6789, host 10.0.0.1"
    masked, ents = mask(demo)
    print(masked)
    for e in ents:
        print(" ", e["type"], "->", e["text"])
