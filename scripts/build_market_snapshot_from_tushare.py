import os, json
from datetime import datetime
import tushare as ts

WATCHLIST = ["000001.SZ", "000858.SZ", "600036.SH", "300750.SZ", "601318.SH"]
INDEXES = {
    "000001.SH": "上证指数",
    "399001.SZ": "深证成指",
    "399006.SZ": "创业板指",
}


def main():
    token = os.getenv("TUSHARE_TOKEN")
    if not token:
        raise SystemExit("TUSHARE_TOKEN missing")

    pro = ts.pro_api(token)
    out = {
        "timestamp": datetime.now().astimezone().isoformat(timespec="seconds"),
        "market": "CN-A",
        "index": {},
        "symbols": [],
        "news": []
    }

    # index snapshot (best effort: some accounts may not have index_daily permission)
    for code, name in INDEXES.items():
        try:
            df = pro.index_daily(ts_code=code, start_date="20260301", end_date="20260331")
            if len(df) >= 1:
                latest = df.iloc[0]
                out["index"][code] = {
                    "name": name,
                    "close": float(latest["close"]),
                    "change_pct": float(latest["pct_chg"])
                }
        except Exception:
            out["index"][code] = {
                "name": name,
                "status": "permission_denied"
            }

    # watchlist daily
    for code in WATCHLIST:
        df = pro.daily(ts_code=code, start_date="20260301", end_date="20260331")
        if len(df) >= 1:
            latest = df.iloc[0]
            out["symbols"].append({
                "symbol": code,
                "close": float(latest["close"]),
                "change_pct": float(latest["pct_chg"]),
                "trade_date": str(latest["trade_date"])
            })

    with open("data/market_snapshot.tushare.json", "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    print("generated: data/market_snapshot.tushare.json")


if __name__ == "__main__":
    main()
