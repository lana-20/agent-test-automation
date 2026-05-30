import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from orchestrator import plan
from runner import run_scenario
from models import TestReport

FEATURE = """
Test the TodoMVC application at https://demo.playwright.dev/todomvc

Cover these independent scenarios:
1. Adding and verifying multiple todos
2. Marking a todo as complete and checking the Completed filter
3. Deleting a todo and verifying the count drops
4. Using the Active filter to show only incomplete todos
5. Clearing all completed todos at once
"""


def main(headless: bool = True) -> None:
    scenarios = plan(FEATURE)

    print(f"\nRunning {len(scenarios)} scenario(s) in parallel...\n" + "=" * 60)

    results = []
    with ThreadPoolExecutor(max_workers=min(len(scenarios), 3)) as pool:
        futures = {
            pool.submit(run_scenario, s, headless): s for s in scenarios
        }
        for future in as_completed(futures):
            results.append(future.result())

    results.sort(key=lambda r: r.scenario_id)
    report = TestReport(scenarios=results)

    print("\n" + "=" * 60)
    print(f"RESULTS  {report.passed}/{report.total} passed\n")
    for r in report.scenarios:
        status = "PASS" if r.passed else "FAIL"
        print(f"  [{r.scenario_id}] {status}  {r.title}")

    if report.failed:
        sys.exit(1)


if __name__ == "__main__":
    headless = "--headless" in sys.argv
    main(headless=headless)
