import os
import json
import time
from datetime import datetime
from pathlib import Path

import tushare as ts
import akshare as ak

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs" / "fundamental_probe_report.json"
STATE_HISTORY = ROOT / "state" / "fundamental_health_history.jsonl"

WATCHLIST = ["600519.SH", "000858.SZ", "600036.SH"]


def _now():
    return datetime.now().astimezone().isoformat(timespec="seconds")


def _safe_call(name, fn):
    t0 = time.perf_counter()
    try:
        payload = fn()
        ms = int((time.perf_counter() - t0) * 1000)
        rows = len(payload) if hasattr(payload, "__len__") else None
        return {"name": name, "ok": True, "latency_ms": ms, "rows": rows, "error": None}
    except Exception as e:
        ms = int((time.perf_counter() - t0) * 1000)
        return {"name": name, "ok": False, "latency_ms": ms, "rows": 0, "error": str(e)[:300]}


def main():
    token = os.getenv("TUSHARE_TOKEN")
    if not token:
        raise SystemExit("TUSHARE_TOKEN missing")

    pro = ts.pro_api(token)

    checks = []

    # Tushare probes
    checks.append(_safe_call(
        "tushare.daily_basic",
        lambda: pro.daily_basic(ts_code=WATCHLIST[0], start_date="20260101", end_date="20261231", fields="ts_code,trade_date,pe,pb")
    ))
    checks.append(_safe_call(
        "tushare.fina_indicator",
        lambda: pro.fina_indicator(ts_code=WATCHLIST[0], start_date="20240101", end_date="20261231", fields="ts_code,end_date,roe,grossprofit_margin,debt_to_assets")
    ))

    # Akshare probes
    checks.append(_safe_call(
        "akshare.stock_zh_valuation_comparison_em",
        lambda: ak.stock_zh_valuation_comparison_em(symbol="SH600519")
    ))
    checks.append(_safe_call(
        "akshare.stock_financial_analysis_indicator_em",
        lambda: ak.stock_financial_analysis_indicator_em(symbol=WATCHLIST[0])
    ))

    ok_n = sum(1 for c in checks if c["ok"])
    total = len(checks)
    ratio = ok_n / total if total else 0.0

    health = "error"
    if ratio >= 0.9:
        health = "ok"
    elif ratio >= 0.5:
        health = "fallback"

    report = {
        "timestamp": _now(),
        "scope": "fundamental",
        "health": health,
        "success_rate": round(ratio, 3),
        "checks": checks,
        "summary": {
            "ok": ok_n,
            "total": total,
            "failed": total - ok_n,
            "avg_latency_ms": int(sum(c["latency_ms"] for c in checks) / total) if total else 0,
        }
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    STATE_HISTORY.parent.mkdir(parents=True, exist_ok=True)
    with STATE_HISTORY.open("a", encoding="utf-8") as f:
        f.write(json.dumps({
            "timestamp": report["timestamp"],
            "health": report["health"],
            "success_rate": report["success_rate"],
            "failed": report["summary"]["failed"],
            "total": report["summary"]["total"],
        }, ensure_ascii=False) + "\n")

    print(f"generated: {OUT}")


if __name__ == "__main__":
    main()
