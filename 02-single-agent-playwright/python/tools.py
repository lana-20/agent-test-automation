import os
from playwright.sync_api import Page


def navigate(page: Page, url: str) -> str:
    page.goto(url, wait_until="domcontentloaded")
    return f"Navigated to {url} — title: {page.title()}"


def find_element(page: Page, role: str | None = None, text: str | None = None) -> str:
    locator = page.get_by_role(role, name=text) if role else page.get_by_text(text)  # type: ignore[arg-type]
    count = locator.count()
    return f"Found {count} element(s) — role={role}, text={text}"


def click(
    page: Page,
    role: str | None = None,
    text: str | None = None,
    selector: str | None = None,
) -> str:
    if selector:
        page.locator(selector).click()
    elif role:
        page.get_by_role(role, name=text).click()  # type: ignore[arg-type]
    else:
        page.get_by_text(text).first.click()  # type: ignore[arg-type]
    return "Clicked"


def fill(
    page: Page,
    value: str,
    label: str | None = None,
    placeholder: str | None = None,
    selector: str | None = None,
) -> str:
    if selector:
        page.locator(selector).fill(value)
    elif label:
        page.get_by_label(label).fill(value)
    elif placeholder:
        page.get_by_placeholder(placeholder).fill(value)
    return f"Filled with: {value}"


def press(page: Page, key: str, selector: str | None = None) -> str:
    if selector:
        page.locator(selector).press(key)
    else:
        page.keyboard.press(key)
    return f"Pressed: {key}"


def get_text(page: Page, selector: str) -> str:
    return page.locator(selector).first.inner_text()


def assert_visible(
    page: Page,
    text: str | None = None,
    role: str | None = None,
    selector: str | None = None,
) -> str:
    if selector:
        locator = page.locator(selector)
    elif role:
        locator = page.get_by_role(role, name=text)  # type: ignore[arg-type]
    else:
        locator = page.get_by_text(text)  # type: ignore[arg-type]
    locator.first.wait_for(state="visible", timeout=5000)
    return f"PASS: visible — text={text}, role={role}, selector={selector}"


def assert_not_visible(
    page: Page,
    text: str | None = None,
    selector: str | None = None,
) -> str:
    locator = page.locator(selector) if selector else page.get_by_text(text)  # type: ignore[arg-type]
    locator.first.wait_for(state="hidden", timeout=5000)
    return f"PASS: not visible — text={text}, selector={selector}"


def get_page_title(page: Page) -> str:
    return page.title()


def get_current_url(page: Page) -> str:
    return page.url


def screenshot(page: Page, filename: str) -> str:
    os.makedirs("screenshots", exist_ok=True)
    path = f"screenshots/{filename}"
    page.screenshot(path=path)
    return f"Screenshot saved: {path}"


TOOL_DEFINITIONS = [
    {
        "name": "navigate",
        "description": "Navigate the browser to a URL and wait for the page to load.",
        "input_schema": {
            "type": "object",
            "properties": {
                "url": {"type": "string"},
            },
            "required": ["url"],
        },
    },
    {
        "name": "find_element",
        "description": "Check whether an element exists on the page. Returns count of matches.",
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
        "name": "press",
        "description": "Press a keyboard key. Use selector to focus a specific element first, or omit to press on the focused element. Common keys: Enter, Tab, Escape, ArrowDown.",
        "input_schema": {
            "type": "object",
            "properties": {
                "key":      {"type": "string", "description": "Key name, e.g. 'Enter', 'Tab', 'Escape'"},
                "selector": {"type": "string", "description": "CSS selector to focus before pressing (optional)"},
            },
            "required": ["key"],
        },
    },
    {
        "name": "get_text",
        "description": "Get the inner text of an element by CSS selector.",
        "input_schema": {
            "type": "object",
            "properties": {
                "selector": {"type": "string"},
            },
            "required": ["selector"],
        },
    },
    {
        "name": "assert_visible",
        "description": "Assert an element is visible. Returns PASS or raises an error that will be reported as FAIL.",
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
            "properties": {
                "filename": {"type": "string", "description": "e.g. step-01.png"},
            },
            "required": ["filename"],
        },
    },
]


def dispatch(name: str, inputs: dict, page: Page) -> str:
    fn_map = {
        "navigate": lambda: navigate(page, **inputs),
        "find_element": lambda: find_element(page, **inputs),
        "click": lambda: click(page, **inputs),
        "fill": lambda: fill(page, **inputs),
        "press": lambda: press(page, **inputs),
        "get_text": lambda: get_text(page, **inputs),
        "assert_visible": lambda: assert_visible(page, **inputs),
        "assert_not_visible": lambda: assert_not_visible(page, **inputs),
        "get_page_title": lambda: get_page_title(page),
        "get_current_url": lambda: get_current_url(page),
        "screenshot": lambda: screenshot(page, **inputs),
    }
    handler = fn_map.get(name)
    if not handler:
        return f"Unknown tool: {name}"
    try:
        return handler()
    except Exception as e:
        return f"FAIL: {e}"
