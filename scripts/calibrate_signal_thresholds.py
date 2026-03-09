import json
import argparse
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parents[1]
CFG = ROOT / "config" / "signal_rules.yaml"
EVAL = ROOT / "outputs" / "signal_eval_report.json"
LOG = ROOT / "state" / "parameter_change_log.jsonl"


def read_lines(path: Path):
    return path.read_text(encoding="utf-8").splitlines() if path.exists() else []


def extract_threshold(lines):
    vals = {}
    in_block = False
    for line in lines:
        s = line.strip()
        if s == "thresholds:":
            in_block = True
            continue
        if in_block and s.endswith(":") and not s.startswith("buy_watch") and not s.startswith("hold") and not s.startswith("reduce"):
            break
        if in_block and ":" in s:
            k, v = [x.strip() for x in s.split(":", 1)]
            if k in ("buy_watch", "hold", "reduce"):
                try:
                    vals[k] = float(v)
                except Exception:
                    pass
    return vals


def propose(current, win_rate):
    buy = current.get("buy_watch", 0.70)
    hold = current.get("hold", 0.55)
    reduce = current.get("reduce", 0.40)

    if win_rate < 0.5:
        buy = min(0.80, buy + 0.02)
        hold = min(buy - 0.05, hold + 0.01)
    elif win_rate > 0.6:
        buy = max(0.60, buy - 0.01)

    if not (reduce < hold < buy):
        hold = min(max(hold, reduce + 0.05), buy - 0.05)

    return {
        "buy_watch": round(buy, 2),
        "hold": round(hold, 2),
        "reduce": round(reduce, 2),
    }


def apply_thresholds(lines, proposed):
    out = []
    in_block = False
    replaced = set()
    for line in lines:
        s = line.strip()
        if s == "thresholds:":
            in_block = True
            out.append(line)
            continue
        if in_block and s.endswith(":") and not any(s.startswith(x) for x in ("buy_watch", "hold", "reduce")):
            for k in ("buy_watch", "hold", "reduce"):
                if k not in replaced:
                    out.append(f"  {k}: {proposed[k]:.2f}")
                    replaced.add(k)
            in_block = False
            out.append(line)
            continue
        if in_block and ":" in s:
            k = s.split(":", 1)[0].strip()
            if k in proposed:
                out.append(f"  {k}: {proposed[k]:.2f}")
                replaced.add(k)
                continue
        out.append(line)

    if in_block:
        for k in ("buy_watch", "hold", "reduce"):
            if k not in replaced:
                out.append(f"  {k}: {proposed[k]:.2f}")

    return out


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="apply proposed thresholds to config")
    args = parser.parse_args()

    if not EVAL.exists() or not CFG.exists():
        raise SystemExit("missing signal eval or config")

    ev = json.loads(EVAL.read_text(encoding="utf-8"))
    win_rate = float((ev.get("summary") or {}).get("win_rate", 0.5))

    lines = read_lines(CFG)
    cur = extract_threshold(lines)
    prop = propose(cur, win_rate)

    record = {
        "timestamp": datetime.now().astimezone().isoformat(timespec="seconds"),
        "win_rate": win_rate,
        "current": cur,
        "proposed": prop,
        "applied": bool(args.apply),
        "reason": "weekly calibration by proxy win_rate",
    }

    if args.apply:
        new_lines = apply_thresholds(lines, prop)
        CFG.write_text("\n".join(new_lines) + "\n", encoding="utf-8")

    LOG.parent.mkdir(parents=True, exist_ok=True)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")

    print(json.dumps(record, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
