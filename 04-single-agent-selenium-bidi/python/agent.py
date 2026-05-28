import json
import anthropic
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.firefox.service import Service as FirefoxService
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.firefox import GeckoDriverManager
from tools import TOOL_DEFINITIONS, dispatch

# Identical to Modules 02 & 03 — the loop is driver-agnostic.
SYSTEM_PROMPT = """You are a senior test automation engineer executing browser-based tests.

Rules:
- Work step by step. After each action, verify the result before proceeding.
- Prefer locating elements by ARIA role + visible text. Fall back to CSS selectors only when needed.
- When an assertion fails, stop and report FAIL with the exact reason.
- At the end, output a concise test report: overall PASS or FAIL, with one bullet per step.
- Take a screenshot after key steps to document evidence.
- After each navigation, call get_browser_logs to surface any JavaScript errors."""


def _build_driver(browser: str, headless: bool):
    if browser == "chrome":
        options = webdriver.ChromeOptions()
        if headless:
            options.add_argument("--headless=new")
        options.add_argument("--window-size=1280,800")
        options.set_capability("goog:loggingPrefs", {"browser": "ALL"})
        return webdriver.Chrome(
            service=ChromeService(ChromeDriverManager().install()),
            options=options,
        )

    if browser == "firefox":
        options = webdriver.FirefoxOptions()
        if headless:
            options.add_argument("--headless")
        # Firefox requires geckodriver with BiDi enabled for log capture.
        options.set_capability("webSocketUrl", True)
        return webdriver.Firefox(
            service=FirefoxService(GeckoDriverManager().install()),
            options=options,
        )

    raise ValueError(f"Unsupported browser: {browser!r}. Use 'chrome' or 'firefox'.")


def run(task: str, browser: str = "chrome", headless: bool = False) -> list[dict]:
    client = anthropic.Anthropic()
    log: list[dict] = []

    # This is the only section that differs from Modules 02 & 03.
    driver = _build_driver(browser, headless)
    driver.implicitly_wait(4)

    messages: list[dict] = [{"role": "user", "content": task}]

    print(f"\nTask: {task}")
    print(f"Browser: {browser}")
    print("=" * 60)

    try:
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
                    result = dispatch(block.name, block.input, driver)
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
    finally:
        driver.quit()

    return log
