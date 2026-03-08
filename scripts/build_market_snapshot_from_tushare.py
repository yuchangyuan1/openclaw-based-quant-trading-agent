import os
import json
from datetime import datetime
from pathlib import Path
import tushare as ts

ROOT = Path(__file__).resolve().parents[1]
CFG = ROOT / "config" / "portfolio.yaml"

DEFAULT_INDEXES = {
    "000001.SH": "上证指数",
    "399001.SZ": "深证成指",
    "399006.SZ": "创业板指",
}


def normalize_symbol(symbol: str) -> str:
    # SH.600519 -> 600519.SH
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
    out = {
        "timestamp": datetime.now().astimezone().isoformat(timespec="seconds"),
        "market": market,
        "index": {},
        "symbols": [],
        "news": [],
    }

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
        except Exception:
            out["index"][code] = {"name": name, "status": "permission_denied"}

    for code in watchlist:
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

    out_path = ROOT / "data" / "market_snapshot.tushare.json"
    out_path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"generated: {out_path}")


if __name__ == "__main__":
    main()
