from __future__ import annotations
import json, re, unicodedata
from collections import Counter


def norm(s: str) -> str:
    s = unicodedata.normalize("NFKC", s or "").lower().strip()
    s = re.sub(r"[\s\u0964\u0965.,!?;:'\"()\-]+", " ", s)
    return s.strip()


def exact(pred: str, ref: str) -> float:
    return float(norm(pred) == norm(ref) or norm(ref) in norm(pred).split("  ") or norm(pred).startswith(norm(ref)))


def chrf(pred: str, ref: str, n: int = 6, beta: float = 2.0) -> float:
    """Character n-gram F-score (chrF), script-agnostic, suits Indic languages."""
    p, r = norm(pred).replace(" ", ""), norm(ref).replace(" ", "")
    if not p or not r:
        return 0.0
    precs, recs = [], []
    for k in range(1, n + 1):
        pc = Counter(p[i:i + k] for i in range(len(p) - k + 1))
        rc = Counter(r[i:i + k] for i in range(len(r) - k + 1))
        if not pc or not rc: continue
        m = sum((pc & rc).values())
        precs.append(m / sum(pc.values())); recs.append(m / sum(rc.values()))
    if not precs: return 0.0
    P, R = sum(precs) / len(precs), sum(recs) / len(recs)
    return 0.0 if P + R == 0 else (1 + beta**2) * P * R / (beta**2 * P + R)


def extract_json(text: str):
    m = re.search(r"\{.*\}", text or "", re.S)
    if not m: return None
    try: return json.loads(m.group(0))
    except json.JSONDecodeError: return None


def field_accuracy(pred: str, ref: dict) -> float:
    got = extract_json(pred) or {}
    if not ref: return 0.0
    ok = sum(norm(str(got.get(k, ""))) == norm(str(v)) for k, v in ref.items())
    return ok / len(ref)


SCORERS = {"exact": exact, "chrf": chrf, "fields": field_accuracy}
