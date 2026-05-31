import time
import anthropic
from vibium import Page
from models import TestScenario, RunnerResult
from tools import TOOL_DEFINITIONS, dispatch


def _api_call_with_retry(client: anthropic.Anthropic, **kwargs) -> anthropic.types.Message:
    for attempt in range(4):
        try:
            return client.messages.create(**kwargs)
        except anthropic.RateLimitError:
            if attempt == 3:
                raise
            time.sleep(60)

_SYSTEM = """You are a senior test automation engineer executing browser-based tests.

Rules:
- Work step by step. After each action, verify the result before proceeding.
- Prefer locating elements by CSS selector. Use role+text as fallback.
- When an assertion fails, stop and report FAIL with the exact reason.
- At the end, output a concise report starting with PASS or FAIL, followed by one bullet per step.

Typing into inputs:
- Use type(selector=<css>, text=<value>) to type into any input field, then press(Enter) to submit.
- Do NOT use fill() — it requires a <label> element and fails on placeholder-only inputs.
- Do NOT press keys one character at a time."""


def run_scenario(scenario: TestScenario, page: Page) -> RunnerResult:
    client = anthropic.Anthropic()
    prefix = f"[{scenario.id}]"

    task = (
        f"Scenario: {scenario.title}\n\n"
        f"Start URL: {scenario.url}\n\n"
        "Steps:\n" + "\n".join(f"{i+1}. {s}" for i, s in enumerate(scenario.steps))
    )

    messages = [{"role": "user", "content": task}]
    step_log = []
    final_text = ""

    while True:
        response = _api_call_with_retry(
            client,
            model="claude-sonnet-4-6",
            max_tokens=4096,
            system=_SYSTEM,
            tools=TOOL_DEFINITIONS,
            messages=messages,
        )

        messages.append({"role": "assistant", "content": response.content})
        tool_results = []

        for block in response.content:
            if block.type == "text":
                final_text = block.text
                print(f"{prefix} {block.text[:120]}")
            elif block.type == "tool_use":
                result = dispatch(block.name, block.input, page)
                print(f"{prefix}   -> {block.name}: {result[:80]}")
                step_log.append(
                    {"tool": block.name, "input": block.input, "result": result}
                )
                tool_results.append(
                    {"type": "tool_result", "tool_use_id": block.id, "content": result}
                )

        if tool_results:
            messages.append({"role": "user", "content": tool_results})
        if response.stop_reason == "end_turn":
            break

    passed = "FAIL" not in final_text.upper().split()[0] if final_text else False
    return RunnerResult(
        scenario_id=scenario.id,
        title=scenario.title,
        passed=passed,
        summary=final_text,
        step_log=step_log,
    )
