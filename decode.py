"""Decode-and-rescan helpers: find base64 / URL-encoded payloads in a message so the classifier can also see the decoded text.

decoded_payloads(text) -> list of decoded strings (empty if nothing decodable)
"""
from __future__ import annotations

import base64
import binascii
import re
from urllib.parse import unquote

_B64 = re.compile(r"(?<![A-Za-z0-9+/])[A-Za-z0-9+/]{20,}={0,2}(?![A-Za-z0-9+/=])")
_URLENC = re.compile(r"%[0-9A-Fa-f]{2}")
MIN_PRINTABLE = 0.9


def _mostly_text(s: str) -> bool:
    if not s.strip():
        return False
    printable = sum(ch.isprintable() or ch in "\n\t" for ch in s)
    return printable / len(s) >= MIN_PRINTABLE and any(ch.isalpha() for ch in s)


def decoded_payloads(text: str, max_payloads: int = 3) -> list[str]:
    out: list[str] = []
    for m in _B64.finditer(text):
        blob = m.group()
        try:
            raw = base64.b64decode(blob + "=" * (-len(blob) % 4), validate=False)
            s = raw.decode("utf-8")
        except (binascii.Error, UnicodeDecodeError, ValueError):
            continue
        if _mostly_text(s) and s not in out:
            out.append(s)
    if len(_URLENC.findall(text)) >= 3:
        s = unquote(text)
        if s != text and _mostly_text(s) and s not in out:
            out.append(s)
    return out[:max_payloads]
