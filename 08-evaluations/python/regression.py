"""Regression harness: compare baseline eval results against current run."""
from __future__ import annotations
import json
import sys
from pathlib import Path

BASELINE_PATH = Path(__file__).parent / "baseline.json"
CURRENT_PATH = Path(__file__).parent / "current.json"

THRESHOLDS = {
    "det_pass_rate": 0.7,
    "llm_avg_overall": 0.65,
    "traj_pass_rate": 0.8,
    "hallucination_rate": 0.1,  # must stay BELOW this
}


def load(path: Path) -> dict:
    return json.loads(path.read_text())


def compare(baseline: dict, current: dict) -> list[dict]:
    regressions = []

    def check(metric: str, current_val: float, threshold: float, higher_is_better: bool = True) -> None:
        baseline_val = baseline.get(metric)
        if baseline_val is None:
            return
        if higher_is_better and current_val < threshold:
            regressions.append({"metric": metric, "baseline": baseline_val, "current": current_val, "threshold": threshold})
        elif not higher_is_better and current_val > threshold:
            regressions.append({"metric": metric, "baseline": baseline_val, "current": current_val, "threshold": threshold})

    check("det_pass_rate", current.get("det_pass_rate", 0), THRESHOLDS["det_pass_rate"])
    check("llm_avg_overall", current.get("llm_avg_overall", 0), THRESHOLDS["llm_avg_overall"])
    check("traj_pass_rate", current.get("traj_pass_rate", 0), THRESHOLDS["traj_pass_rate"])
    check("hallucination_rate", current.get("hallucination_rate", 1), THRESHOLDS["hallucination_rate"], higher_is_better=False)

    return regressions


def save_baseline(current: dict) -> None:
    BASELINE_PATH.write_text(json.dumps(current, indent=2))
    print(f"Baseline saved to {BASELINE_PATH}")


def main() -> None:
    if not CURRENT_PATH.exists():
        print("No current.json found — run eval_runner.py first")
        sys.exit(1)

    current = load(CURRENT_PATH)

    if "--save-baseline" in sys.argv:
        save_baseline(current)
        return

    if not BASELINE_PATH.exists():
        print("No baseline found — saving current as baseline")
        save_baseline(current)
        return

    baseline = load(BASELINE_PATH)
    regressions = compare(baseline, current)

    if regressions:
        print(f"\nREGRESSION DETECTED — {len(regressions)} metric(s) below threshold:\n")
        for r in regressions:
            print(f"  {r['metric']}: baseline={r['baseline']:.3f} current={r['current']:.3f} threshold={r['threshold']:.3f}")
        sys.exit(1)
    else:
        print("No regressions detected.")
        for key in ["det_pass_rate", "llm_avg_overall", "traj_pass_rate", "hallucination_rate"]:
            b = baseline.get(key, "n/a")
            c = current.get(key, "n/a")
            delta = f"+{c - b:.3f}" if isinstance(b, float) and isinstance(c, float) and c >= b else (f"{c - b:.3f}" if isinstance(b, float) and isinstance(c, float) else "")
            print(f"  {key}: {b} → {c}  {delta}")


if __name__ == "__main__":
    main()
