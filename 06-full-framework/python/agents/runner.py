import time
import anthropic
from playwright.sync_api import sync_playwright
from models import TestScenario, RunnerResult
from tools import TOOL_DEFINITIONS, dispatch


def _api_call_with_retry(client: anthropic.Anthropic, **kwargs) -> anthropic.types.Message:
    for attempt in range(4):
        try:
            return client.messages.create(**kwargs)
        except anthropic.RateLimitError:
            if attempt == 3:
                raise
            time.sleep(60)  # wait 1 minute for token window to reset

_SYSTEM = """You are a senior test automation engineer executing browser-based tests.

Rules:
- Work step by step. After each action, verify the result before proceeding.
- Prefer locating elements by ARIA role + visible text.
- When an assertion fails, stop and report FAIL with the exact reason.
- At the end, output a concise report starting with PASS or FAIL, followed by one bullet per step."""


def run(scenario: TestScenario, headless: bool = True) -> RunnerResult:
    client = anthropic.Anthropic()
    prefix = f"[Runner:{scenario.id}]"

    task = (
        f"Scenario: {scenario.title}\n"
        f"Category: {scenario.category} · Priority: {scenario.priority}\n"
        f"Expected outcome: {scenario.expected_outcome}\n\n"
        f"Start URL: {scenario.url}\n\n"
        "Steps:\n" + "\n".join(f"{i+1}. {s}" for i, s in enumerate(scenario.steps))
    )

    messages = [{"role": "user", "content": task}]
    step_log = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        context = browser.new_context(viewport={"width": 1280, "height": 800})
        page = context.new_page()
        final_text = ""

        try:
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
                        step_log.append({"tool": block.name, "input": block.input, "result": result})
                        tool_results.append(
                            {"type": "tool_result", "tool_use_id": block.id, "content": result}
                        )

                if tool_results:
                    messages.append({"role": "user", "content": tool_results})
                if response.stop_reason == "end_turn":
                    break
        finally:
            browser.close()

    first_word = final_text.strip().split()[0].upper() if final_text.strip() else ""
    passed = first_word != "FAIL"

    return RunnerResult(
        scenario_id=scenario.id,
        title=scenario.title,
        passed=passed,
        summary=final_text,
        step_log=step_log,
    )
