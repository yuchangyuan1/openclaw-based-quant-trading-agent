import json
import os
from datetime import datetime
from pathlib import Path
from urllib import request, error

ROOT = Path(__file__).resolve().parents[1]
STATE_PATH = ROOT / "state" / "push_job_state.json"
MAX_ATTEMPTS = 5


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
    queue = state.get("retry_queue", [])
    if not queue:
        print("retry queue empty")
        return

    webhook_url = os.getenv("FEISHU_WEBHOOK_URL") or os.getenv("FEISHU_BOT_WEBHOOK")
    if not webhook_url:
        print("webhook missing; skip consume")
        return

    remained = []
    now = datetime.now().astimezone().isoformat(timespec="seconds")

    for item in queue:
        attempt = int(item.get("attempt", 1))
        payload = item.get("payload", {})
        report_path = Path(payload.get("report_path", ""))

        if not report_path.exists():
            if attempt >= MAX_ATTEMPTS:
                continue
            item["attempt"] = attempt + 1
            item["reason"] = "report_missing_on_retry"
            remained.append(item)
            continue

        text = report_path.read_text(encoding="utf-8")
        if len(text) > 3800:
            text = text[:3800] + "\n\n[重试推送，内容已截断]"

        try:
            send_to_feishu(webhook_url, text)
            state["daily_last_success"] = now
            state["last_error"] = None
        except (error.URLError, error.HTTPError, TimeoutError, RuntimeError) as e:
            if attempt >= MAX_ATTEMPTS:
                state["last_error"] = f"{now} retry dropped after {attempt} attempts: {e}"
                continue
            item["attempt"] = attempt + 1
            item["reason"] = str(e)
            remained.append(item)

    state["retry_queue"] = remained
    save_state(state)
    print(f"retry queue remaining: {len(remained)}")


if __name__ == "__main__":
    main()
