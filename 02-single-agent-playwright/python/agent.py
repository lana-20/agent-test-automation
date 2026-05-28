import json
import anthropic
from playwright.sync_api import sync_playwright, Page
from tools import TOOL_DEFINITIONS, dispatch

SYSTEM_PROMPT = """You are a senior test automation engineer executing browser-based tests.

Rules:
- Work step by step. After each action, verify the result before proceeding.
- Prefer locating elements by ARIA role + visible text. Fall back to CSS selectors only when needed.
- When an assertion fails, stop and report FAIL with the exact reason.
- At the end, output a concise test report: overall PASS or FAIL, with one bullet per step.
- Take a screenshot after key steps to document evidence."""


def run(task: str, headless: bool = False) -> list[dict]:
    client = anthropic.Anthropic()
    log: list[dict] = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        context = browser.new_context(viewport={"width": 1280, "height": 800})
        page: Page = context.new_page()

        messages: list[dict] = [{"role": "user", "content": task}]

        print(f"\nTask: {task}")
        print("=" * 60)

        while True:
            response = client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=4096,
                system=SYSTEM_PROMPT,
                tools=TOOL_DEFINITIONS,
                messages=messages,
            )

            messages.append({"role": "assistant", "content": response.content})

            tool_results = []
            for block in response.content:
                if block.type == "text":
                    print(f"\nAgent: {block.text}")
                elif block.type == "tool_use":
                    print(f"  -> {block.name}({json.dumps(block.input, ensure_ascii=False)})")
                    result = dispatch(block.name, block.input, page)
                    print(f"     {result}")
                    log.append({"tool": block.name, "input": block.input, "result": result})
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result,
                    })

            if tool_results:
                messages.append({"role": "user", "content": tool_results})

            if response.stop_reason == "end_turn":
                break

        context.close()
        browser.close()

    return log
