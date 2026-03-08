import hashlib
import json
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
STATE = ROOT / "state"
STATE.mkdir(parents=True, exist_ok=True)
HISTORY = STATE / "advice_history.jsonl"
OUT = ROOT / "outputs"


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def parse_history(path: Path):
    if not path.exists():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return rows


def main():
    signal_path = DATA / "signal_report.generated.json"
    if not signal_path.exists():
        raise SystemExit("signal_report.generated.json missing")

    report = load_json(signal_path)
    rows = parse_history(HISTORY)
    now = datetime.now().astimezone()
    dedup_cutoff = now - timedelta(hours=24)

    latest_by_symbol = {}
    for r in rows:
        sym = r.get("symbol")
        ts = r.get("ts")
        if sym and ts:
            latest_by_symbol[sym] = r

    advisory = []
    appended = []

    for s in report.get("signals", []):
        symbol = s["symbol"]
        action = s["signal"]
        reason_text = "|".join(s.get("reasons", []))
        reason_hash = hashlib.md5(reason_text.encode("utf-8")).hexdigest()[:12]
        prev = latest_by_symbol.get(symbol)

        change = "首次建议"
        if prev:
            if prev.get("action") == action:
                change = "与上次一致"
            else:
                change = f"由{prev.get('action')}调整为{action}"

        allow_send = True
        if prev:
            try:
                prev_ts = datetime.fromisoformat(prev["ts"])
                if prev_ts.tzinfo is None:
                    prev_ts = prev_ts.replace(tzinfo=now.tzinfo)
            except Exception:
                prev_ts = now - timedelta(days=999)
            if prev_ts >= dedup_cutoff and prev.get("action") == action and prev.get("reason_hash") == reason_hash:
                allow_send = False

        record = {
            "ts": now.isoformat(timespec="seconds"),
            "symbol": symbol,
            "action": action,
            "reason_hash": reason_hash,
            "confidence": s.get("confidence", 0.62),
            "change_vs_last": change,
        }

        if allow_send:
            appended.append(record)
            advisory.append({**s, "change_vs_last": change, "suppressed": False})
        else:
            advisory.append({**s, "change_vs_last": "24小时去重抑制", "suppressed": True})

    if appended:
        with HISTORY.open("a", encoding="utf-8") as f:
            for r in appended:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")

    OUT.mkdir(parents=True, exist_ok=True)
    out_path = OUT / "advice_actions.json"
    out_path.write_text(json.dumps({"timestamp": now.isoformat(timespec="seconds"), "items": advisory}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"generated: {out_path}")


if __name__ == "__main__":
    main()
