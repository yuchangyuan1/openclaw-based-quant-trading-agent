import json
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / "state" / "push_job_state.json"
OUT = ROOT / "outputs"


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    now = datetime.now().astimezone()
    if not STATE.exists():
        STATE.parent.mkdir(parents=True, exist_ok=True)
        STATE.write_text(json.dumps({"daily_last_success": None, "weekly_last_success": None, "last_error": None, "retry_queue": []}, ensure_ascii=False, indent=2), encoding="utf-8")

    state = json.loads(STATE.read_text(encoding="utf-8"))
    msgs = []

    daily_ts = state.get("daily_last_success")
    if daily_ts:
        try:
            last = datetime.fromisoformat(daily_ts)
            if now - last > timedelta(hours=30):
                msgs.append("检测到日报任务可能漏跑，建议补发摘要（系统状态+风险提示）。")
        except Exception:
            msgs.append("日报状态时间格式异常，建议人工检查。")
    else:
        msgs.append("首次运行：尚无日报成功记录。")

    recovery = {
        "timestamp": now.isoformat(timespec="seconds"),
        "alerts": msgs,
        "action": "no_op" if not msgs else "review_and_backfill"
    }

    out_path = OUT / "missed_run_recovery.json"
    out_path.write_text(json.dumps(recovery, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"generated: {out_path}")


if __name__ == "__main__":
    main()
