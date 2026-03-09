import os
import json
from pathlib import Path
from datetime import datetime

import tushare as ts

ROOT = Path(__file__).resolve().parents[1]
CFG = ROOT / "config" / "backtest_rules.yaml"
PORTFOLIO = ROOT / "config" / "portfolio.yaml"
OUT = ROOT / "outputs" / "backtest_baseline_report.json"


def _load_yaml_like(path: Path):
    data = {}
    if not path.exists():
        return data
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or ":" not in line:
            continue
        k, v = [x.strip() for x in line.split(":", 1)]
        data[k] = v
    return data


def _normalize_symbol(symbol: str) -> str:
    s = (symbol or "").strip().upper()
    if "." not in s:
        return s
    a, b = s.split(".", 1)
    # 兼容 SH.600519 / 600519.SH 两种写法
    if a in ("SH", "SZ", "BJ"):
        return f"{b}.{a}"
    return s


def _load_watchlist(path: Path):
    if not path.exists():
        return ["600519.SH", "000858.SZ", "600036.SH"]
    watch = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if line.startswith("- symbol:"):
            watch.append(_normalize_symbol(line.split(":", 1)[1].strip()))
    return watch or ["600519.SH", "000858.SZ", "600036.SH"]


def _to_num(x, default=0.0):
    try:
        return float(x)
    except Exception:
        return default


def _calc_sma(seq, n, i):
    if i + 1 < n:
        return None
    window = seq[i - n + 1:i + 1]
    return sum(window) / n if window else None


def backtest_single(closes, short_n, long_n, fee_rate):
    if len(closes) < long_n + 5:
        return {"total_return": 0.0, "trades": 0, "max_drawdown": 0.0, "equity_curve": [1.0]}

    equity = 1.0
    peak = 1.0
    max_dd = 0.0
    in_pos = False
    trades = 0
    curve = [equity]

    for i in range(len(closes)):
        s = _calc_sma(closes, short_n, i)
        l = _calc_sma(closes, long_n, i)
        if s is None or l is None or i == 0:
            curve.append(equity)
            continue

        # 交易信号
        if (not in_pos) and s > l:
            in_pos = True
            trades += 1
            equity *= (1 - fee_rate)
        elif in_pos and s < l:
            in_pos = False
            trades += 1
            equity *= (1 - fee_rate)

        # 持仓收益
        if in_pos:
            prev = closes[i - 1]
            cur = closes[i]
            if prev > 0:
                equity *= (cur / prev)

        if equity > peak:
            peak = equity
        dd = (equity - peak) / peak if peak > 0 else 0.0
        if dd < max_dd:
            max_dd = dd

        curve.append(equity)

    return {
        "total_return": round(equity - 1.0, 4),
        "trades": trades,
        "max_drawdown": round(max_dd, 4),
        "equity_curve": [round(x, 4) for x in curve[-120:]],
    }


def main():
    token = os.getenv("TUSHARE_TOKEN")
    if not token:
        raise SystemExit("TUSHARE_TOKEN missing")

    c = _load_yaml_like(CFG)
    start_date = c.get("start_date", "20230101")
    end_date = c.get("end_date", "20261231")
    short_n = int(_to_num(c.get("ma_short", 20), 20))
    long_n = int(_to_num(c.get("ma_long", 60), 60))
    fee_rate = _to_num(c.get("fee_rate", 0.001), 0.001)

    watchlist = _load_watchlist(PORTFOLIO)

    pro = ts.pro_api(token)
    details = []

    for sym in watchlist:
        try:
            df = pro.daily(ts_code=sym, start_date=start_date, end_date=end_date)
            if len(df) < long_n + 5:
                continue
            # tushare 默认按 trade_date 降序，回测需升序
            closes = [float(x) for x in df.sort_values("trade_date")["close"].tolist()]
            r = backtest_single(closes, short_n, long_n, fee_rate)
            details.append({"symbol": sym, **r})
        except Exception as e:
            details.append({"symbol": sym, "error": str(e)[:200]})

    valid = [x for x in details if "total_return" in x]
    avg_ret = round(sum(x["total_return"] for x in valid) / len(valid), 4) if valid else 0.0
    worst_dd = round(min((x["max_drawdown"] for x in valid), default=0.0), 4)

    out = {
        "timestamp": datetime.now().astimezone().isoformat(timespec="seconds"),
        "strategy": {
            "name": "ma_crossover_baseline",
            "short": short_n,
            "long": long_n,
            "fee_rate": fee_rate,
            "source_ref": "Building-A-Trading-Strategy-With-Python (MA crossover idea)",
        },
        "period": {"start_date": start_date, "end_date": end_date},
        "summary": {
            "symbols": len(valid),
            "avg_total_return": avg_ret,
            "worst_max_drawdown": worst_dd,
        },
        "details": details,
        "note": "用于策略 sanity-check 的轻量回测基线，不代表可实盘收益承诺。",
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"generated: {OUT}")


if __name__ == "__main__":
    main()
