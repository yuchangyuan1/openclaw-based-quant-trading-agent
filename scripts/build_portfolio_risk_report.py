import json
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
OUT = ROOT / "outputs"
CFG = ROOT / "config" / "portfolio.yaml"


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def parse_portfolio_constraints(path: Path):
    constraints = {
        "max_single_position": 0.20,
        "max_sector_exposure": 0.35,
        "max_drawdown": -0.08,
    }
    if not path.exists():
        return constraints

    in_section = False
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line == "portfolio_constraints:":
            in_section = True
            continue
        if in_section and line.endswith(":"):
            in_section = False
        if in_section and ":" in line:
            k, v = [x.strip() for x in line.split(":", 1)]
            try:
                num = float(v)
            except ValueError:
                continue
            if k == "max_position_per_stock":
                constraints["max_single_position"] = num
            elif k == "max_sector_exposure":
                constraints["max_sector_exposure"] = num
            elif k == "max_portfolio_drawdown":
                constraints["max_drawdown"] = num
    return constraints


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    signal_path = DATA / "signal_report.generated.json"
    if not signal_path.exists():
        signal_path = DATA / "signal_report.json"
    if not signal_path.exists():
        raise SystemExit("signal_report(.generated).json missing")

    report = load_json(signal_path)
    constraints = parse_portfolio_constraints(CFG)

    # MVP: if no live holdings file, estimate current risk from signals distribution
    signals = report.get("signals", [])
    high_risk = sum(1 for s in signals if s.get("risk_level") == "high")
    n = max(len(signals), 1)

    current = {
        "largest_position": round(min(0.2, 1 / n + 0.05), 4),
        "largest_sector_exposure": round(min(0.35, 2 / n + 0.12), 4),
        "drawdown": round(-0.01 * high_risk, 4),
    }

    violations = []
    if current["largest_position"] > constraints["max_single_position"]:
        violations.append("single_position_limit")
    if current["largest_sector_exposure"] > constraints["max_sector_exposure"]:
        violations.append("sector_exposure_limit")
    if current["drawdown"] < constraints["max_drawdown"]:
        violations.append("portfolio_drawdown_limit")

    risk_state = report.get("global_risk_state", "normal")
    if violations and risk_state == "normal":
        risk_state = "cautious"
    if len(violations) >= 2:
        risk_state = "defensive"

    out = {
        "timestamp": report.get("timestamp") or datetime.now().astimezone().isoformat(timespec="seconds"),
        "constraints": constraints,
        "current": current,
        "violations": violations,
        "risk_state": risk_state,
    }

    payload = json.dumps(out, ensure_ascii=False, indent=2)
    out_path = OUT / "portfolio_risk_report.json"
    out_data_path = DATA / "portfolio_risk_report.json"
    out_path.write_text(payload, encoding="utf-8")
    out_data_path.write_text(payload, encoding="utf-8")
    print(f"generated: {out_path}")
    print(f"generated: {out_data_path}")


if __name__ == "__main__":
    main()
