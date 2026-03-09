import json
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs"
DATA = ROOT / "data"


def _load(path: Path, default):
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def main():
    # 避免 Windows 控制台中文乱码
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    parser = argparse.ArgumentParser(description="Explain current advice by symbol")
    parser.add_argument("--symbol", type=str, default="", help="e.g. 600519.SH")
    args = parser.parse_args()
    symbol = (args.symbol or "").strip().upper()

    advice = _load(OUT / "advice_actions.json", {"items": []})
    signals = _load(DATA / "signal_report.generated.json", {"signals": []})

    items = advice.get("items") or signals.get("signals") or []
    if symbol:
        items = [x for x in items if (x.get("symbol") or "").upper() == symbol]

    if not items:
        print("未找到对应标的建议。可先运行日流水线后再查询。")
        return

    for i in items:
        print("=" * 60)
        print(f"标的: {i.get('symbol')}")
        print(f"建议: {i.get('signal')}")
        print(f"分数/置信度: {i.get('score')} / {i.get('confidence')}")
        print(f"风险等级: {i.get('risk_level')}")
        print(f"与上次变化: {i.get('change_vs_last', i.get('delta_vs_last', '无'))}")
        print("理由:")
        for r in i.get("reasons", [])[:6]:
            print(f"- {r}")
        q = i.get("data_quality_gate", {})
        if q:
            print(f"数据质量闸门: passed={q.get('passed')} quality_score={q.get('quality_score')}")


if __name__ == "__main__":
    main()
