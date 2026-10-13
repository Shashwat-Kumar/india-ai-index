from __future__ import annotations
import json, datetime as dt
from pathlib import Path
from typing import Dict, List

from .scoring import SCORERS

SCHEMA_VERSION = "1.0"


def load_tasks(task_dir: str = "tasks") -> List[Dict]:
    items = []
    for f in sorted(Path(task_dir).glob("*.jsonl")):
        for line in f.read_text(encoding="utf-8").splitlines():
            if line.strip(): items.append(json.loads(line))
    return items


def run(provider, items: List[Dict], usd_inr: float) -> Dict:
    rows = []
    for it in items:
        c = provider.complete(it["prompt"])
        score = SCORERS[it["scorer"]](c.text, it["reference"])
        usd = (c.input_tokens * provider.pin + c.output_tokens * provider.pout) / 1e6
        rows.append({"id": it["id"], "suite": it["suite"], "lang": it.get("lang", "en"), "score": round(score, 4),
                     "input_tokens": c.input_tokens, "output_tokens": c.output_tokens,
                     "latency_s": round(c.latency_s, 3), "cost_inr": round(usd * usd_inr, 6)})
    suites: Dict[str, Dict] = {}
    for r in rows:
        s = suites.setdefault(r["suite"], {"n": 0, "score": 0.0, "cost_inr": 0.0})
        s["n"] += 1; s["score"] += r["score"]; s["cost_inr"] += r["cost_inr"]
    for s in suites.values():
        s["score"] = round(s["score"] / s["n"], 4); s["cost_inr_per_task"] = round(s["cost_inr"] / s["n"], 6)
    overall = round(sum(r["score"] for r in rows) / max(len(rows), 1), 4)
    return {"schema_version": SCHEMA_VERSION, "provider": provider.name, "model": provider.model,
            "run_at": dt.datetime.now(dt.timezone.utc).isoformat(), "usd_inr": usd_inr,
            "price_usd_per_m": {"input": provider.pin, "output": provider.pout},
            "n_items": len(rows), "overall_score": overall,
            "cost_inr_total": round(sum(r["cost_inr"] for r in rows), 4),
            "suites": suites, "items": rows}


def validate(result: Dict) -> List[str]:
    errs = []
    for k in ("schema_version", "provider", "model", "run_at", "overall_score", "suites", "items", "usd_inr"):
        if k not in result: errs.append(f"missing {k}")
    if not 0 <= result.get("overall_score", -1) <= 1: errs.append("overall_score out of range")
    return errs
