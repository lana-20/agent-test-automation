import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from agents.architect import plan
from agents.runner import run
from agents.asserter import classify
from agents import reporter
from models import TestReport


def execute(spec: str, headless: bool = True) -> TestReport:
    scenarios = plan(spec)

    high = [s for s in scenarios if s.priority == "high"]
    rest = [s for s in scenarios if s.priority != "high"]

    print(f"\n[Orchestrator] Running {len(high)} high-priority scenario(s) first...")
    print("=" * 60)

    results = []

    with ThreadPoolExecutor(max_workers=max(len(high), 1)) as pool:
        futures = {pool.submit(run, s, headless): s for s in high}
        for future in as_completed(futures):
            results.append(future.result())

    # Stop early if any high-priority scenario failed
    critical_failures = [r for r in results if not r.passed]
    if critical_failures:
        print(
            f"\n[Orchestrator] {len(critical_failures)} high-priority failure(s) — "
            "skipping remaining scenarios."
        )
    else:
        if rest:
            print(f"\n[Orchestrator] Running {len(rest)} remaining scenario(s)...")
            with ThreadPoolExecutor(max_workers=len(rest)) as pool:
                futures = {pool.submit(run, s, headless): s for s in rest}
                for future in as_completed(futures):
                    results.append(future.result())

    failed_results = [r for r in results if not r.passed]
    scenario_map = {s.id: s for s in scenarios}

    findings = []
    if failed_results:
        print(f"\n[Asserter] Classifying {len(failed_results)} failure(s)...")
        for r in failed_results:
            scenario = scenario_map[r.scenario_id]
            findings.append(classify(scenario, r))

    return TestReport(spec=spec, results=results, findings=findings)
