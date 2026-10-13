import argparse, json, sys
from pathlib import Path
from .providers import REGISTRY
from .runner import load_tasks, run, validate

def main(argv=None):
    ap = argparse.ArgumentParser(prog="iai", description="India AI Index harness")
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run"); r.add_argument("--provider", required=True, choices=sorted(REGISTRY))
    r.add_argument("--model", required=True); r.add_argument("--price-in", type=float, default=0.0, help="USD per 1M input tokens")
    r.add_argument("--price-out", type=float, default=0.0); r.add_argument("--usd-inr", type=float, required=True)
    r.add_argument("--tasks", default="tasks"); r.add_argument("--out", default="results")
    sub.add_parser("list-tasks").add_argument("--tasks", default="tasks")
    a = ap.parse_args(argv)
    if a.cmd == "list-tasks":
        items = load_tasks(a.tasks); print(f"{len(items)} items"); [print(i["id"], i["suite"], i.get("lang","")) for i in items]; return 0
    p = REGISTRY[a.provider](a.model, price_in_usd_per_m=a.price_in, price_out_usd_per_m=a.price_out)
    if not p.available():
        print(f"Missing API key: set {p.env_key}", file=sys.stderr); return 2
    res = run(p, load_tasks(a.tasks), a.usd_inr)
    assert not validate(res)
    Path(a.out).mkdir(exist_ok=True)
    f = Path(a.out) / f"{p.name}__{a.model.replace('/', '_')}.json"
    f.write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8"); print(f"Wrote {f}"); return 0

if __name__ == "__main__":
    sys.exit(main())
