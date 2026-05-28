import json
import os
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.common.exceptions import TimeoutException, NoSuchElementException


# ── Locator helpers ───────────────────────────────────────────────────────────
# Selenium has no built-in role locator; we map ARIA roles to XPath.

def _by_role_and_text(role: str | None, text: str | None) -> tuple:
    """Return (By, value) for the given role + text combination."""
    if role and text:
        # Semantic element fallback covers cases where role is implicit.
        semantic = {
            "button":   "button",
            "link":     "a",
            "heading":  "h1 | h2 | h3 | h4 | h5 | h6",
            "checkbox": "input[@type='checkbox']",
            "listitem": "li",
        }
        tag = semantic.get(role)
        if tag:
            xpath = (
                f"//{tag}[contains(normalize-space(), '{text}')] "
                f"| //*[@role='{role}'][contains(normalize-space(), '{text}')]"
            )
        else:
            xpath = f"//*[@role='{role}'][contains(normalize-space(), '{text}')]"
        return By.XPATH, xpath

    if text:
        # Leaf-node match: element whose text matches but has no child with the same text.
        return (
            By.XPATH,
            f"//*[contains(normalize-space(), '{text}') "
            f"and not(.//*[contains(normalize-space(), '{text}')])]",
        )
    if role:
        semantic = {
            "button": "button", "link": "a",
            "textbox": "input | textarea",
        }
        tag = semantic.get(role, f"*[@role='{role}']")
        return By.XPATH, f"//{tag} | //*[@role='{role}']"

    raise ValueError("Provide at least one of: role, text, selector")


def _wait_for(driver: WebDriver, by: str, value: str, timeout: float = 5) -> WebElement:
    return WebDriverWait(driver, timeout).until(
        EC.presence_of_element_located((by, value))
    )


def _wait_visible(driver: WebDriver, by: str, value: str, timeout: float = 5) -> WebElement:
    return WebDriverWait(driver, timeout).until(
        EC.visibility_of_element_located((by, value))
    )


# ── Core browser tools (same interface as Modules 02 & 03) ───────────────────

def navigate(driver: WebDriver, url: str) -> str:
    driver.get(url)
    return f"Navigated to {url} — title: {driver.title}"


def find_element(driver: WebDriver, role: str | None = None, text: str | None = None) -> str:
    by, value = _by_role_and_text(role, text)
    try:
        driver.find_element(by, value)
        return f"Found element — role={role}, text={text}"
    except NoSuchElementException:
        return f"Not found — role={role}, text={text}"


def click(
    driver: WebDriver,
    role: str | None = None,
    text: str | None = None,
    selector: str | None = None,
) -> str:
    if selector:
        _wait_for(driver, By.CSS_SELECTOR, selector).click()
    else:
        by, value = _by_role_and_text(role, text)
        _wait_for(driver, by, value).click()
    return "Clicked"


def fill(
    driver: WebDriver,
    value: str,
    label: str | None = None,
    placeholder: str | None = None,
    selector: str | None = None,
) -> str:
    if selector:
        el = _wait_for(driver, By.CSS_SELECTOR, selector)
    elif placeholder:
        el = _wait_for(
            driver, By.CSS_SELECTOR,
            f"input[placeholder='{placeholder}'], textarea[placeholder='{placeholder}']",
        )
    elif label:
        # Find the input whose id matches a <label> with this text.
        el = _wait_for(
            driver, By.XPATH,
            f"//input[@id=//label[normalize-space()='{label}']/@for]",
        )
    else:
        raise ValueError("fill: provide label, placeholder, or selector")
    el.clear()
    el.send_keys(value)
    return f"Filled with: {value}"


def get_text(driver: WebDriver, selector: str) -> str:
    return driver.find_element(By.CSS_SELECTOR, selector).text


def assert_visible(
    driver: WebDriver,
    text: str | None = None,
    role: str | None = None,
    selector: str | None = None,
) -> str:
    try:
        if selector:
            _wait_visible(driver, By.CSS_SELECTOR, selector)
        else:
            by, value = _by_role_and_text(role, text)
            _wait_visible(driver, by, value)
        return f"PASS: visible — text={text}, role={role}, selector={selector}"
    except TimeoutException:
        raise AssertionError(f"Timed out waiting for visible element — text={text}, role={role}")


def assert_not_visible(
    driver: WebDriver,
    text: str | None = None,
    selector: str | None = None,
) -> str:
    try:
        by = By.CSS_SELECTOR if selector else By.XPATH
        value = selector or f"//*[contains(normalize-space(), '{text}')]"
        WebDriverWait(driver, 5).until(
            EC.invisibility_of_element_located((by, value))
        )
        return f"PASS: not visible — text={text}, selector={selector}"
    except TimeoutException:
        raise AssertionError(f"Element is still visible — text={text}")


def get_page_title(driver: WebDriver) -> str:
    return driver.title


def get_current_url(driver: WebDriver) -> str:
    return driver.current_url


def screenshot(driver: WebDriver, filename: str) -> str:
    os.makedirs("screenshots", exist_ok=True)
    path = f"screenshots/{filename}"
    driver.save_screenshot(path)
    return f"Screenshot saved: {path}"


# ── BiDi-specific tools (unique to this module) ───────────────────────────────

def get_browser_logs(driver: WebDriver) -> str:
    """Retrieve browser console logs via the WebDriver log API.

    Works on Chrome/Edge natively. On Firefox, enable logging in the
    FirefoxOptions capabilities (see agent.py).
    """
    try:
        logs = driver.get_log("browser")
        if not logs:
            return "No browser logs captured"
        entries = [
            f"[{e['level']}] {e['message']}"
            for e in logs[-10:]  # last 10 entries
        ]
        return "\n".join(entries)
    except Exception as e:
        return f"Log capture not available: {e}"


def execute_script(driver: WebDriver, expression: str) -> str:
    """Evaluate a JavaScript expression and return the result.

    Wraps BiDi script.evaluate — useful for checking DOM state that
    has no accessible representation, or for timing assertions.
    """
    result = driver.execute_script(f"return {expression}")
    return str(result)


def intercept_network(driver: WebDriver, url_pattern: str) -> str:
    """Enable CDP Network domain and log matching requests.

    Uses Chrome DevTools Protocol via Selenium's execute_cdp_cmd.
    Requires Chrome or Edge — not available on Firefox without geckodriver BiDi.
    """
    try:
        driver.execute_cdp_cmd("Network.enable", {})
        driver.execute_cdp_cmd(
            "Network.setBlockedURLs", {"urls": [url_pattern]}
        )
        return f"Network intercept active — blocking: {url_pattern}"
    except Exception as e:
        return f"Network intercept unavailable (Chrome/Edge only): {e}"


# ── Tool definitions ──────────────────────────────────────────────────────────
# Core 10 are identical to Modules 02 & 03.
# Three BiDi tools are added at the end.

TOOL_DEFINITIONS = [
    {
        "name": "navigate",
        "description": "Navigate the browser to a URL and wait for the page to load.",
        "input_schema": {
            "type": "object",
            "properties": {"url": {"type": "string"}},
            "required": ["url"],
        },
    },
    {
        "name": "find_element",
        "description": "Check whether an element exists on the page.",
        "input_schema": {
            "type": "object",
            "properties": {
                "role": {"type": "string", "description": "ARIA role: button, link, textbox, heading, checkbox, …"},
                "text": {"type": "string", "description": "Visible text or accessible name"},
            },
        },
    },
    {
        "name": "click",
        "description": "Click an element. Prefer role+text over selector.",
        "input_schema": {
            "type": "object",
            "properties": {
                "role": {"type": "string"},
                "text": {"type": "string"},
                "selector": {"type": "string", "description": "CSS selector — use as fallback only"},
            },
        },
    },
    {
        "name": "fill",
        "description": "Type text into an input. Use label or placeholder to locate it.",
        "input_schema": {
            "type": "object",
            "properties": {
                "value": {"type": "string"},
                "label": {"type": "string"},
                "placeholder": {"type": "string"},
                "selector": {"type": "string"},
            },
            "required": ["value"],
        },
    },
    {
        "name": "get_text",
        "description": "Get the text content of an element by CSS selector.",
        "input_schema": {
            "type": "object",
            "properties": {"selector": {"type": "string"}},
            "required": ["selector"],
        },
    },
    {
        "name": "assert_visible",
        "description": "Assert an element is visible. Returns PASS or raises an error reported as FAIL.",
        "input_schema": {
            "type": "object",
            "properties": {
                "text": {"type": "string"},
                "role": {"type": "string"},
                "selector": {"type": "string"},
            },
        },
    },
    {
        "name": "assert_not_visible",
        "description": "Assert an element is hidden or absent.",
        "input_schema": {
            "type": "object",
            "properties": {
                "text": {"type": "string"},
                "selector": {"type": "string"},
            },
        },
    },
    {
        "name": "get_page_title",
        "description": "Get the current page <title>.",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "get_current_url",
        "description": "Get the current URL.",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "screenshot",
        "description": "Take a screenshot and save to screenshots/<filename>.",
        "input_schema": {
            "type": "object",
            "properties": {"filename": {"type": "string"}},
            "required": ["filename"],
        },
    },
    # ── BiDi extras ──────────────────────────────────────────────────────────
    {
        "name": "get_browser_logs",
        "description": "Retrieve browser console logs (errors, warnings, info). "
                       "Call after a navigation or interaction to check for JS errors.",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "execute_script",
        "description": "Evaluate a JavaScript expression and return the result. "
                       "Use for DOM state that has no accessible representation.",
        "input_schema": {
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "JS expression to evaluate, e.g. 'document.querySelectorAll(\".todo-list li\").length'",
                }
            },
            "required": ["expression"],
        },
    },
    {
        "name": "intercept_network",
        "description": "Block requests matching a URL pattern. Chrome/Edge only. "
                       "Use to verify the app handles failed requests gracefully.",
        "input_schema": {
            "type": "object",
            "properties": {
                "url_pattern": {
                    "type": "string",
                    "description": "Glob pattern, e.g. '*/api/*' or 'https://example.com/data.json'",
                }
            },
            "required": ["url_pattern"],
        },
    },
]


def dispatch(name: str, inputs: dict, driver: WebDriver) -> str:
    fn_map = {
        "navigate":           lambda: navigate(driver, **inputs),
        "find_element":       lambda: find_element(driver, **inputs),
        "click":              lambda: click(driver, **inputs),
        "fill":               lambda: fill(driver, **inputs),
        "get_text":           lambda: get_text(driver, **inputs),
        "assert_visible":     lambda: assert_visible(driver, **inputs),
        "assert_not_visible": lambda: assert_not_visible(driver, **inputs),
        "get_page_title":     lambda: get_page_title(driver),
        "get_current_url":    lambda: get_current_url(driver),
        "screenshot":         lambda: screenshot(driver, **inputs),
        "get_browser_logs":   lambda: get_browser_logs(driver),
        "execute_script":     lambda: execute_script(driver, **inputs),
        "intercept_network":  lambda: intercept_network(driver, **inputs),
    }
    handler = fn_map.get(name)
    if not handler:
        return f"Unknown tool: {name}"
    try:
        return handler()
    except Exception as e:
        return f"FAIL: {e}"
