"""Trajectory judge: validates tool call sequences against expected tools."""
from __future__ import annotations
from dataclasses import dataclass, field

VALID_TOOLS = {
    "navigate", "click", "fill", "find", "find_all", "get_text", "get_attribute",
    "get_value", "is_visible", "is_enabled", "is_checked", "check", "uncheck",
    "select", "hover", "scroll", "wait", "wait_for_text", "wait_for_url",
    "screenshot", "evaluate", "count", "get_url", "get_title",
    "dialog_accept", "dialog_dismiss", "keys", "press", "type",
}


@dataclass
class TrajectoryResult:
    scenario_id: str
    tool_sequence: list[str]
    expected_tools: list[str]
    coverage: float           # fraction of expected tools actually called
    hallucinated: list[str]   # tools called that don't exist
    redundant_calls: int      # same tool called >3 times in a row
    passed: bool


def judge(scenario_id: str, tool_calls: list[dict], expected_tools: list[str]) -> TrajectoryResult:
    sequence = [tc.get("name", tc.get("tool", "")) for tc in tool_calls]
    called_set = set(sequence)
    expected_set = set(expected_tools)

    coverage = len(expected_set & called_set) / len(expected_set) if expected_set else 0.0
    hallucinated = [t for t in sequence if t not in VALID_TOOLS]

    redundant = 0
    for i in range(2, len(sequence)):
        if sequence[i] == sequence[i - 1] == sequence[i - 2]:
            redundant += 1

    passed = coverage >= 0.6 and not hallucinated and redundant == 0
    return TrajectoryResult(
        scenario_id=scenario_id,
        tool_sequence=sequence,
        expected_tools=expected_tools,
        coverage=round(coverage, 3),
        hallucinated=hallucinated,
        redundant_calls=redundant,
        passed=passed,
    )


def aggregate(results: list[TrajectoryResult]) -> dict:
    total = len(results)
    if not total:
        return {}
    hallucination_rate = sum(1 for r in results if r.hallucinated) / total
    return {
        "total": total,
        "passed": sum(1 for r in results if r.passed),
        "avg_coverage": round(sum(r.coverage for r in results) / total, 3),
        "hallucination_rate": round(hallucination_rate, 3),
        "total_hallucinated_calls": sum(len(r.hallucinated) for r in results),
        "scenarios_with_redundancy": sum(1 for r in results if r.redundant_calls > 0),
    }
