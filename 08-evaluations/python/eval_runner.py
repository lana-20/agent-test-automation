"""Eval runner: loads golden dataset, runs agent, applies all three judges, reports."""
from __future__ import annotations
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

import anthropic

import judge_deterministic as det
import judge_llm as llm
import judge_trajectory as traj

GOLDEN_PATH = Path(__file__).parent / "golden.json"
REPORT_PATH = Path(__file__).parent / "eval_report.md"
CURRENT_PATH = Path(__file__).parent / "current.json"

SYSTEM_PROMPT = """You are a QA test automation agent. Given a URL and task, use tools to test the page.
Report your findings as a single plain-English paragraph describing what you found.
Always navigate to the URL first before using other tools."""

TOOLS = [
    {"name": "navigate", "description": "Navigate to a URL", "input_schema": {"type": "object", "properties": {"url": {"type": "string"}}, "required": ["url"]}},
    {"name": "click", "description": "Click an element", "input_schema": {"type": "object", "properties": {"selector": {"type": "string"}}, "required": ["selector"]}},
    {"name": "fill", "description": "Fill an input field", "input_schema": {"type": "object", "properties": {"selector": {"type": "string"}, "value": {"type": "string"}}, "required": ["selector", "value"]}},
    {"name": "find", "description": "Find an element on the page", "input_schema": {"type": "object", "properties": {"selector": {"type": "string"}}, "required": ["selector"]}},
    {"name": "get_text", "description": "Get text content of an element", "input_schema": {"type": "object", "properties": {"selector": {"type": "string"}}, "required": ["selector"]}},
    {"name": "is_visible", "description": "Check if element is visible", "input_schema": {"type": "object", "properties": {"selector": {"type": "string"}}, "required": ["selector"]}},
    {"name": "select", "description": "Select an option from a dropdown", "input_schema": {"type": "object", "properties": {"selector": {"type": "string"}, "value": {"type": "string"}}, "required": ["selector", "value"]}},
    {"name": "screenshot", "description": "Take a screenshot", "input_schema": {"type": "object", "properties": {}, "required": []}},
    {"name": "evaluate", "description": "Run JavaScript in the page", "input_schema": {"type": "object", "properties": {"script": {"type": "string"}}, "required": ["script"]}},
    {"name": "count", "description": "Count elements matching a selector", "input_schema": {"type": "object", "properties": {"selector": {"type": "string"}}, "required": ["selector"]}},
    {"name": "dialog_accept", "description": "Accept a browser dialog", "input_schema": {"type": "object", "properties": {}, "required": []}},
    {"name": "dialog_dismiss", "description": "Dismiss a browser dialog", "input_schema": {"type": "object", "properties": {}, "required": []}},
    {"name": "wait", "description": "Wait for milliseconds", "input_schema": {"type": "object", "properties": {"ms": {"type": "integer"}}, "required": ["ms"]}},
]

MAX_TURNS = 8


def run_scenario(client: anthropic.Anthropic, scenario: dict) -> tuple[str, list[dict]]:
    """Run agent on one scenario. Returns (final_finding, tool_calls)."""
    messages = [{"role": "user", "content": f"URL: {scenario['site']}\nTask: {scenario['task']}"}]
    tool_calls_log: list[dict] = []
    finding = ""

    for _ in range(MAX_TURNS):
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            tools=TOOLS,
            messages=messages,
        )

        tool_uses = [b for b in response.content if b.type == "tool_use"]
        text_blocks = [b for b in response.content if b.type == "text"]

        if text_blocks:
            finding = text_blocks[-1].text

        if response.stop_reason == "end_turn" or not tool_uses:
            break

        messages.append({"role": "assistant", "content": response.content})

        tool_results = []
        for tu in tool_uses:
            tool_calls_log.append({"name": tu.name, "input": tu.input})
            tool_results.append({
                "type": "tool_result",
                "tool_use_id": tu.id,
                "content": f"[simulated: {tu.name} executed]",
            })

        messages.append({"role": "user", "content": tool_results})

    return finding, tool_calls_log


def write_report(
    scenarios: list[dict],
    det_results: list[det.DeterministicResult],
    llm_results: list[llm.LLMJudgeResult],
    traj_results: list[traj.TrajectoryResult],
    elapsed: float,
) -> None:
    det_agg = det.precision_recall(det_results)
    llm_agg = llm.aggregate(llm_results)
    traj_agg = traj.aggregate(traj_results)

    lines = [
        f"# Eval Report — {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "",
        f"**Scenarios:** {len(scenarios)} | **Runtime:** {elapsed:.1f}s",
        "",
        "## Summary",
        "",
        "| Judge | Pass Rate | Key Metric |",
        "|---|---|---|",
        f"| Deterministic | {det_agg['pass_rate']:.0%} | avg keyword coverage: {det_agg['avg_keyword_coverage']:.0%} |",
        f"| LLM Judge | {llm_agg['passed']}/{llm_agg['total']} passed | avg overall: {llm_agg['avg_overall']:.2f} |",
        f"| Trajectory | {traj_agg['passed']}/{traj_agg['total']} passed | hallucination rate: {traj_agg['hallucination_rate']:.0%} |",
        "",
        "## Per-Scenario Results",
        "",
        "| ID | Site | Det | LLM | Traj |",
        "|---|---|---|---|---|",
    ]

    for i, sc in enumerate(scenarios):
        d = det_results[i]
        l = llm_results[i]
        t = traj_results[i]
        lines.append(
            f"| {sc['id']} | {sc['site'].replace('https://', '')} "
            f"| {'✓' if d.passed else '✗'} {d.score:.0%} "
            f"| {'✓' if l.passed else '✗'} {l.overall:.2f} "
            f"| {'✓' if t.passed else '✗'} {t.coverage:.0%} |"
        )

    lines += [
        "",
        "## LLM Judge Detail",
        "",
        "| ID | Accuracy | Specificity | Actionability | Reasoning |",
        "|---|---|---|---|---|",
    ]
    for l in llm_results:
        lines.append(f"| {l.scenario_id} | {l.accuracy:.2f} | {l.specificity:.2f} | {l.actionability:.2f} | {l.reasoning} |")

    REPORT_PATH.write_text("\n".join(lines))
    print(f"\nReport written to {REPORT_PATH}")


def main() -> None:
    scenarios = json.loads(GOLDEN_PATH.read_text())

    # Filter by module if passed as arg
    if len(sys.argv) > 1:
        module_filter = sys.argv[1]
        scenarios = [s for s in scenarios if s.get("module") == module_filter]
        if not scenarios:
            print(f"No scenarios found for module: {module_filter}")
            sys.exit(1)
        print(f"Running {len(scenarios)} scenarios for module {module_filter}")
    else:
        print(f"Running all {len(scenarios)} scenarios")

    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    det_results: list[det.DeterministicResult] = []
    llm_results: list[llm.LLMJudgeResult] = []
    traj_results: list[traj.TrajectoryResult] = []

    start = time.time()
    for sc in scenarios:
        print(f"\n[{sc['id']}] {sc['site']}")
        finding, tool_calls = run_scenario(client, sc)

        d = det.judge(sc["id"], finding, sc["expected_keywords"])
        l = llm.judge(sc["id"], finding, sc["task"])
        t = traj.judge(sc["id"], tool_calls, sc["expected_tools"])

        det_results.append(d)
        llm_results.append(l)
        traj_results.append(t)

        status = "PASS" if d.passed and l.passed and t.passed else "FAIL"
        print(f"  {status} | det={d.score:.0%} llm={l.overall:.2f} traj_cov={t.coverage:.0%}")

    elapsed = time.time() - start

    det_agg = det.precision_recall(det_results)
    llm_agg = llm.aggregate(llm_results)
    traj_agg = traj.aggregate(traj_results)
    current = {
        "det_pass_rate": det_agg["pass_rate"],
        "llm_avg_overall": llm_agg["avg_overall"],
        "traj_pass_rate": round(traj_agg["passed"] / traj_agg["total"], 3) if traj_agg["total"] else 0.0,
        "hallucination_rate": traj_agg["hallucination_rate"],
    }
    CURRENT_PATH.write_text(json.dumps(current, indent=2))
    print(f"Metrics written to {CURRENT_PATH}")

    write_report(scenarios, det_results, llm_results, traj_results, elapsed)


if __name__ == "__main__":
    main()
