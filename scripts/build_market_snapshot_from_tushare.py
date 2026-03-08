import os
import json
from datetime import datetime, timezone
from pathlib import Path
import tushare as ts

ROOT = Path(__file__).resolve().parents[1]
CFG = ROOT / "config" / "portfolio.yaml"
OUT = ROOT / "data" / "market_snapshot.tushare.json"

DEFAULT_INDEXES = {
    "000001.SH": "上证指数",
    "399001.SZ": "深证成指",
    "399006.SZ": "创业板指",
}


def normalize_symbol(symbol: str) -> str:
    s = symbol.strip().upper()
    if "." not in s:
        return s
    a, b = s.split(".", 1)
    if a in ("SH", "SZ", "BJ"):
        return f"{b}.{a}"
    return s


def load_portfolio_config(path: Path):
    market = "CN-A"
    watchlist = []
    indexes = {}

    if not path.exists():
        return market, watchlist, indexes

    section = None
    pending_index_code = None

    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue

        if line.startswith("market:"):
            market = line.split(":", 1)[1].strip() or market
            continue

        if line == "watchlist:":
            section = "watchlist"
            continue

        if line == "indexes:":
            section = "indexes"
            continue

        if section == "watchlist":
            if line.startswith("- symbol:"):
                sym = line.split(":", 1)[1].strip()
                if sym:
                    watchlist.append(normalize_symbol(sym))
            elif not line.startswith("name:") and not line.startswith("-"):
                section = None

        elif section == "indexes":
            if line.startswith("- code:"):
                pending_index_code = line.split(":", 1)[1].strip().upper()
                indexes[pending_index_code] = pending_index_code
            elif line.startswith("name:") and pending_index_code:
                indexes[pending_index_code] = line.split(":", 1)[1].strip() or pending_index_code
            elif not line.startswith("-") and not line.startswith("name:"):
                section = None
                pending_index_code = None

    return market, watchlist, indexes


def health_from_flags(ok_count: int, total: int) -> str:
    if total == 0:
        return "error"
    ratio = ok_count / total
    if ratio >= 0.95:
        return "ok"
    if ratio >= 0.7:
        return "fallback"
    return "error"


def main():
    token = os.getenv("TUSHARE_TOKEN")
    if not token:
        raise SystemExit("TUSHARE_TOKEN missing")

    market, watchlist, indexes = load_portfolio_config(CFG)
    if not watchlist:
        watchlist = ["600519.SH", "000858.SZ", "600036.SH", "300750.SZ", "601318.SH"]
    if not indexes:
        indexes = DEFAULT_INDEXES.copy()

    pro = ts.pro_api(token)
    now = datetime.now().astimezone()

    out = {
        "timestamp": now.isoformat(timespec="seconds"),
        "market": market,
        "index": {},
        "sector": {"leaders": [], "laggards": []},
        "symbols": [],
        "news": [],
        "data_freshness_sec": 0,
        "source_health": {"quote": "error", "news": "fallback", "fundamental": "fallback"},
        "missing_fields": [],
        "snapshot_quality_score": 0,
    }

    idx_ok = 0
    for code, name in indexes.items():
        try:
            df = pro.index_daily(ts_code=code, start_date="20260301", end_date="20260331")
            if len(df) >= 1:
                latest = df.iloc[0]
                out["index"][code] = {
                    "name": name,
                    "close": float(latest["close"]),
                    "change_pct": float(latest["pct_chg"]),
                }
                idx_ok += 1
            else:
                out["index"][code] = {"name": name, "status": "no_data"}
        except Exception:
            out["index"][code] = {"name": name, "status": "permission_denied"}

    sym_ok = 0
    for code in watchlist:
        try:
            df = pro.daily(ts_code=code, start_date="20260301", end_date="20260331")
            if len(df) >= 1:
                latest = df.iloc[0]
                out["symbols"].append(
                    {
                        "symbol": code,
                        "close": float(latest["close"]),
                        "change_pct": float(latest["pct_chg"]),
                        "trade_date": str(latest["trade_date"]),
                    }
                )
                sym_ok += 1
        except Exception:
            continue

    out["source_health"]["quote"] = health_from_flags(idx_ok + sym_ok, len(indexes) + len(watchlist))

    required_top_fields = ["timestamp", "market", "symbols", "index", "sector", "news"]
    for key in required_top_fields:
        if key not in out or out[key] in (None, "", []):
            if key not in ("news", "sector"):
                out["missing_fields"].append(key)

    # quality score: 50 for quote health + 30 for symbol coverage + 20 for index coverage
    quote_base = {"ok": 50, "fallback": 30, "cached": 40, "error": 10}.get(out["source_health"]["quote"], 10)
    sym_cov = 0 if len(watchlist) == 0 else int(30 * (sym_ok / len(watchlist)))
    idx_cov = 0 if len(indexes) == 0 else int(20 * (idx_ok / len(indexes)))
    quality_score = max(0, min(100, quote_base + sym_cov + idx_cov - len(out["missing_fields"]) * 10))
    out["snapshot_quality_score"] = quality_score

    # current generated file is real-time, so freshness is 0 at write time
    out["data_freshness_sec"] = int((datetime.now(timezone.utc) - now.astimezone(timezone.utc)).total_seconds())

    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"generated: {OUT}")


if __name__ == "__main__":
    main()
