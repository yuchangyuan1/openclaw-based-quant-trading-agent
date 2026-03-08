import json
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATE_PATH = ROOT / "state" / "push_job_state.json"
OUT = ROOT / "outputs"


def load_state():
    if not STATE_PATH.exists():
        return {
            "daily_last_success": None,
            "weekly_last_success": None,
            "last_error": None,
            "retry_queue": []
        }
    return json.loads(STATE_PATH.read_text(encoding="utf-8"))


def main():
    state = load_state()
    report_path = OUT / "daily_report.generated.md"
    now = datetime.now().astimezone().isoformat(timespec="seconds")

    if report_path.exists():
        state["daily_last_success"] = now
        state["last_error"] = None
    else:
        state["last_error"] = f"{now} daily_report.generated.md missing"
        state.setdefault("retry_queue", []).append({
            "ts": now,
            "job": "daily_report_push",
            "reason": "daily_report_missing"
        })

    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"updated: {STATE_PATH}")


if __name__ == "__main__":
    main()
