import json
import os
from datetime import datetime
from pathlib import Path
from urllib import request, error

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs"
STATE_PATH = ROOT / "state" / "push_job_state.json"


def load_state():
    if not STATE_PATH.exists():
        return {
            "daily_last_success": None,
            "weekly_last_success": None,
            "last_error": None,
            "retry_queue": []
        }
    return json.loads(STATE_PATH.read_text(encoding="utf-8"))


def save_state(state):
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def enqueue_retry(state, reason, payload):
    queue = state.setdefault("retry_queue", [])
    queue.append({
        "ts": datetime.now().astimezone().isoformat(timespec="seconds"),
        "job": "daily_report_push",
        "reason": reason,
        "attempt": 1,
        "payload": payload,
    })


def send_to_feishu(webhook_url: str, text: str):
    body = {
        "msg_type": "text",
        "content": {"text": text}
    }
    data = json.dumps(body, ensure_ascii=False).encode("utf-8")
    req = request.Request(webhook_url, data=data, headers={"Content-Type": "application/json"}, method="POST")
    with request.urlopen(req, timeout=15) as resp:
        raw = resp.read().decode("utf-8", errors="ignore")
        if resp.status < 200 or resp.status >= 300:
            raise RuntimeError(f"HTTP {resp.status}: {raw}")
        return raw


def main():
    state = load_state()
    report_path = OUT / "daily_report.generated.md"
    now = datetime.now().astimezone().isoformat(timespec="seconds")

    if not report_path.exists():
        err = "daily_report.generated.md missing"
        state["last_error"] = f"{now} {err}"
        enqueue_retry(state, err, {"report_path": str(report_path)})
        save_state(state)
        print("queued: report missing")
        return

    webhook_url = os.getenv("FEISHU_WEBHOOK_URL") or os.getenv("FEISHU_BOT_WEBHOOK")
    if not webhook_url:
        err = "FEISHU_WEBHOOK_URL missing"
        state["last_error"] = f"{now} {err}"
        enqueue_retry(state, err, {"report_path": str(report_path)})
        save_state(state)
        print("queued: webhook missing")
        return

    text = report_path.read_text(encoding="utf-8")
    if len(text) > 3800:
        text = text[:3800] + "\n\n[报告过长，已截断。完整版本请查看文件 outputs/daily_report.generated.md]"

    try:
        resp = send_to_feishu(webhook_url, text)
        state["daily_last_success"] = now
        state["last_error"] = None
        save_state(state)
        print(f"pushed: success {resp}")
    except (error.URLError, error.HTTPError, TimeoutError, RuntimeError) as e:
        err = str(e)
        state["last_error"] = f"{now} push failed: {err}"
        enqueue_retry(state, err, {"report_path": str(report_path)})
        save_state(state)
        print("queued: push failed")


if __name__ == "__main__":
    main()
