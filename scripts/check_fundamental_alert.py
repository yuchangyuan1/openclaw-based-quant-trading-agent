import json
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parents[1]
HISTORY = ROOT / "state" / "fundamental_health_history.jsonl"
OUT = ROOT / "state" / "fundamental_alert_state.json"

N_DAYS = 3


def parse_jsonl(path: Path):
    rows = []
    if not path.exists():
        return rows
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except Exception:
            continue
    return rows


def main():
    rows = parse_jsonl(HISTORY)
    latest = rows[-N_DAYS:] if len(rows) >= N_DAYS else rows

    consecutive_error = len(latest) >= N_DAYS and all((x.get("health") == "error") for x in latest)

    state = {
        "timestamp": datetime.now().astimezone().isoformat(timespec="seconds"),
        "window": N_DAYS,
        "history_samples": len(rows),
        "latest": latest,
        "alert": consecutive_error,
        "message": "fundamental 数据源连续异常，请优先排查权限/网络/回退策略" if consecutive_error else "fundamental 数据源未触发连续异常告警",
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"updated: {OUT}")
    if consecutive_error:
        print("ALERT: consecutive fundamental errors detected")


if __name__ == "__main__":
    main()
