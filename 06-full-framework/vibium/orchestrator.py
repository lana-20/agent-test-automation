import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from vibium import browser as vibium_browser
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

    bro = vibium_browser.start(headless=headless)
    high_contexts = []
    rest_contexts = []
    try:
        high_contexts = [bro.new_context() for _ in high]
        high_pages = [ctx.new_page() for ctx in high_contexts]
        with ThreadPoolExecutor(max_workers=min(max(len(high), 1), 3)) as pool:
            futures = {pool.submit(run, s, p): s for s, p in zip(high, high_pages)}
            for future in as_completed(futures):
                results.append(future.result())

        critical_failures = [r for r in results if not r.passed]
        if critical_failures:
            print(
                f"\n[Orchestrator] {len(critical_failures)} high-priority failure(s) — "
                "skipping remaining scenarios."
            )
        else:
            if rest:
                print(f"\n[Orchestrator] Running {len(rest)} remaining scenario(s)...")
                rest_contexts = [bro.new_context() for _ in rest]
                rest_pages = [ctx.new_page() for ctx in rest_contexts]
                with ThreadPoolExecutor(max_workers=min(len(rest), 3)) as pool:
                    futures = {pool.submit(run, s, p): s for s, p in zip(rest, rest_pages)}
                    for future in as_completed(futures):
                        results.append(future.result())
    finally:
        for ctx in high_contexts + rest_contexts:
            ctx.close()
        bro.stop()

    failed_results = [r for r in results if not r.passed]
    scenario_map = {s.id: s for s in scenarios}

    findings = []
    if failed_results:
        print(f"\n[Asserter] Classifying {len(failed_results)} failure(s)...")
        for r in failed_results:
            scenario = scenario_map[r.scenario_id]
            findings.append(classify(scenario, r))

    return TestReport(spec=spec, results=results, findings=findings)
