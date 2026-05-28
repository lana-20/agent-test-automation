import anthropic
from models import TestScenario, RunnerResult, Finding

_CLIENT = anthropic.Anthropic()

_CLASSIFY_TOOL = {
    "name": "classify_failure",
    "description": "Classify a test failure and recommend a next action.",
    "input_schema": {
        "type": "object",
        "properties": {
            "classification": {
                "type": "string",
                "enum": ["bug", "expected-failure", "flaky", "environment"],
                "description": (
                    "bug: the app behaved incorrectly; "
                    "expected-failure: known issue or intentionally broken; "
                    "flaky: timing/race condition, likely to pass on retry; "
                    "environment: infra or network problem, not an app defect"
                ),
            },
            "severity": {
                "type": "string",
                "enum": ["critical", "high", "medium", "low"],
            },
            "description": {
                "type": "string",
                "description": "2–3 sentence technical description of what went wrong.",
            },
            "suggested_action": {
                "type": "string",
                "description": "Concrete next step: file a bug, retry, investigate env, etc.",
            },
        },
        "required": ["classification", "severity", "description", "suggested_action"],
    },
}

_SYSTEM = """You are a senior QA analyst reviewing test failures.

Given a failing scenario and its execution log, determine:
- What type of failure it is (bug / expected-failure / flaky / environment)
- Severity if it is a bug
- A clear technical description of the root cause
- The most useful next action

Be precise. Avoid vague language like "something went wrong"."""


def classify(scenario: TestScenario, result: RunnerResult) -> Finding:
    log_text = "\n".join(
        f"  {entry['tool']}({entry['input']}) → {entry['result']}"
        for entry in result.step_log
    )

    prompt = (
        f"Scenario: {scenario.title}\n"
        f"Category: {scenario.category} · Priority: {scenario.priority}\n"
        f"Expected outcome: {scenario.expected_outcome}\n\n"
        f"Execution log:\n{log_text}\n\n"
        f"Runner summary:\n{result.summary}"
    )

    response = _CLIENT.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        system=_SYSTEM,
        tools=[_CLASSIFY_TOOL],
        tool_choice={"type": "tool", "name": "classify_failure"},
        messages=[{"role": "user", "content": prompt}],
    )

    tool_block = next(b for b in response.content if b.type == "tool_use")
    inp = tool_block.input

    finding = Finding(
        scenario_id=scenario.id,
        title=scenario.title,
        classification=inp["classification"],
        severity=inp["severity"],
        description=inp["description"],
        suggested_action=inp["suggested_action"],
    )

    print(
        f"[Asserter:{scenario.id}] {finding.classification.upper()} "
        f"({finding.severity}) — {finding.description[:80]}"
    )

    return finding
