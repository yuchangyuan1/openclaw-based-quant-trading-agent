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


def safe_pct(a, b):
    if b == 0:
        return 0.0
    return (a - b) / b


def build_factor_inputs(df):
    if df is None or len(df) < 2:
        return {"ret_1d": 0.0, "ret_5d": 0.0, "ret_20d": 0.0, "volatility_20d": 0.0, "volume_ratio_5d": 1.0}

    closes = [float(x) for x in df["close"].tolist()]
    vols = [float(x) for x in df["vol"].tolist()]

    ret_1d = safe_pct(closes[0], closes[1]) if len(closes) >= 2 else 0.0
    ret_5d = safe_pct(closes[0], closes[5]) if len(closes) >= 6 else safe_pct(closes[0], closes[-1])
    ret_20d = safe_pct(closes[0], closes[20]) if len(closes) >= 21 else safe_pct(closes[0], closes[-1])

    recent = closes[:20] if len(closes) >= 20 else closes
    mean = sum(recent) / len(recent)
    variance = sum((x - mean) ** 2 for x in recent) / max(len(recent), 1)
    volatility_20d = (variance ** 0.5) / mean if mean != 0 else 0.0

    vol_5 = sum(vols[:5]) / min(len(vols), 5)
    vol_rest = sum(vols[5:20]) / max(min(len(vols), 20) - 5, 1) if len(vols) > 5 else vol_5
    volume_ratio_5d = vol_5 / vol_rest if vol_rest > 0 else 1.0

    return {
        "ret_1d": round(ret_1d, 6),
        "ret_5d": round(ret_5d, 6),
        "ret_20d": round(ret_20d, 6),
        "volatility_20d": round(volatility_20d, 6),
        "volume_ratio_5d": round(volume_ratio_5d, 4),
    }


def fetch_valuation(pro, ts_code: str):
    try:
        df = pro.daily_basic(ts_code=ts_code, start_date="20260101", end_date="20261231", fields="ts_code,trade_date,pe,pb")
        if len(df) >= 1:
            latest = df.iloc[0]
            return {
                "trade_date": str(latest.get("trade_date", "")),
                "pe": float(latest.get("pe")) if latest.get("pe") is not None else None,
                "pb": float(latest.get("pb")) if latest.get("pb") is not None else None,
            }
    except Exception:
        pass
    return {"trade_date": None, "pe": None, "pb": None}


def fetch_earnings_quality(pro, ts_code: str):
    try:
        df = pro.fina_indicator(ts_code=ts_code, start_date="20240101", end_date="20261231", fields="ts_code,end_date,roe,grossprofit_margin,debt_to_assets")
        if len(df) >= 1:
            latest = df.iloc[0]
            return {
                "end_date": str(latest.get("end_date", "")),
                "roe": float(latest.get("roe")) if latest.get("roe") is not None else None,
                "grossprofit_margin": float(latest.get("grossprofit_margin")) if latest.get("grossprofit_margin") is not None else None,
                "debt_to_assets": float(latest.get("debt_to_assets")) if latest.get("debt_to_assets") is not None else None,
            }
    except Exception:
        pass
    return {"end_date": None, "roe": None, "grossprofit_margin": None, "debt_to_assets": None}


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
            df = pro.index_daily(ts_code=code, start_date="20260101", end_date="20261231")
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
    valuation_ok = 0
    earnings_ok = 0

    for code in watchlist:
        try:
            df = pro.daily(ts_code=code, start_date="20260101", end_date="20261231")
            if len(df) >= 1:
                latest = df.iloc[0]
                valuation = fetch_valuation(pro, code)
                earnings = fetch_earnings_quality(pro, code)
                if valuation.get("pe") is not None or valuation.get("pb") is not None:
                    valuation_ok += 1
                if earnings.get("roe") is not None:
                    earnings_ok += 1

                out["symbols"].append(
                    {
                        "symbol": code,
                        "close": float(latest["close"]),
                        "change_pct": float(latest["pct_chg"]),
                        "trade_date": str(latest["trade_date"]),
                        "factor_inputs": build_factor_inputs(df.head(30)),
                        "valuation": valuation,
                        "earnings": earnings,
                    }
                )
                sym_ok += 1
        except Exception:
            continue

    out["source_health"]["quote"] = health_from_flags(idx_ok + sym_ok, len(indexes) + len(watchlist))
    out["source_health"]["fundamental"] = health_from_flags(valuation_ok + earnings_ok, len(watchlist) * 2)

    required_top_fields = ["timestamp", "market", "symbols", "index", "sector", "news"]
    for key in required_top_fields:
        if key not in out or out[key] in (None, "", []):
            if key not in ("news", "sector"):
                out["missing_fields"].append(key)

    quote_base = {"ok": 50, "fallback": 30, "cached": 40, "error": 10}.get(out["source_health"]["quote"], 10)
    sym_cov = 0 if len(watchlist) == 0 else int(25 * (sym_ok / len(watchlist)))
    idx_cov = 0 if len(indexes) == 0 else int(15 * (idx_ok / len(indexes)))
    fundamental_cov = 0 if len(watchlist) == 0 else int(10 * ((valuation_ok + earnings_ok) / max(len(watchlist) * 2, 1)))
    quality_score = max(0, min(100, quote_base + sym_cov + idx_cov + fundamental_cov - len(out["missing_fields"]) * 10))
    out["snapshot_quality_score"] = quality_score

    out["data_freshness_sec"] = int((datetime.now(timezone.utc) - now.astimezone(timezone.utc)).total_seconds())

    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"generated: {OUT}")


if __name__ == "__main__":
    main()
