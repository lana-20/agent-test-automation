import os
from vibium import Page


def navigate(page: Page, url: str) -> str:
    page.go(url)
    return f"Navigated to {url} — title: {page.title()}"


def find_element(page: Page, role: str | None = None, text: str | None = None) -> str:
    query: dict = {}
    if role:
        query["role"] = role
    if text:
        query["text"] = text
    try:
        page.find(query)
        return f"Found element — role={role}, text={text}"
    except Exception:
        return f"Not found — role={role}, text={text}"


def click(
    page: Page,
    role: str | None = None,
    text: str | None = None,
    selector: str | None = None,
) -> str:
    if selector:
        page.find(selector).click()
    else:
        query: dict = {}
        if role:
            query["role"] = role
        if text:
            query["text"] = text
        page.find(query).click()
    return "Clicked"


def fill(
    page: Page,
    value: str,
    label: str | None = None,
    placeholder: str | None = None,
    selector: str | None = None,
) -> str:
    if selector:
        page.find(selector).fill(value)
    elif label:
        page.find({"role": "textbox", "text": label}).fill(value)
    elif placeholder:
        page.find({"placeholder": placeholder}).fill(value)
    return f"Filled with: {value}"


def press(page: Page, key: str) -> str:
    page.keyboard.press(key)
    return f"Pressed: {key}"


def get_text(page: Page, selector: str) -> str:
    return page.find(selector).info.text


def assert_visible(
    page: Page,
    text: str | None = None,
    role: str | None = None,
    selector: str | None = None,
) -> str:
    if selector:
        el = page.find(selector)
    elif role:
        query: dict = {"role": role}
        if text:
            query["text"] = text
        el = page.find(query)
    else:
        el = page.find({"text": text})
    if not el.is_visible():
        raise AssertionError(f"Element not visible — text={text}, role={role}")
    return f"PASS: visible — text={text}, role={role}, selector={selector}"


def assert_not_visible(
    page: Page,
    text: str | None = None,
    selector: str | None = None,
) -> str:
    try:
        query = selector if selector else {"text": text}
        el = page.find(query)
        if el.is_visible():
            raise AssertionError(f"Element is still visible — text={text}")
    except Exception as e:
        if "still visible" in str(e):
            raise
    return f"PASS: not visible — text={text}, selector={selector}"


def get_page_title(page: Page) -> str:
    return page.title()


def get_current_url(page: Page) -> str:
    return page.url()


def screenshot(page: Page, filename: str) -> str:
    os.makedirs("screenshots", exist_ok=True)
    path = f"screenshots/{filename}"
    with open(path, "wb") as f:
        f.write(page.screenshot())
    return f"Screenshot saved: {path}"


# ── Tool definitions (identical to Module 02 — the agent loop doesn't change) ─

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
        "description": "Press a keyboard key (e.g. Enter, Tab, Escape) on the currently focused element.",
        "input_schema": {
            "type": "object",
            "properties": {
                "key": {"type": "string", "description": "Key name, e.g. 'Enter', 'Tab', 'Escape'"},
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
            "properties": {
                "filename": {"type": "string", "description": "e.g. step-01.png"},
            },
            "required": ["filename"],
        },
    },
]


def dispatch(name: str, inputs: dict, page: Page) -> str:
    fn_map = {
        "navigate":          lambda: navigate(page, **inputs),
        "find_element":      lambda: find_element(page, **inputs),
        "click":             lambda: click(page, **inputs),
        "fill":              lambda: fill(page, **inputs),
        "press":             lambda: press(page, **inputs),
        "get_text":          lambda: get_text(page, **inputs),
        "assert_visible":    lambda: assert_visible(page, **inputs),
        "assert_not_visible": lambda: assert_not_visible(page, **inputs),
        "get_page_title":    lambda: get_page_title(page),
        "get_current_url":   lambda: get_current_url(page),
        "screenshot":        lambda: screenshot(page, **inputs),
    }
    handler = fn_map.get(name)
    if not handler:
        return f"Unknown tool: {name}"
    try:
        return handler()
    except Exception as e:
        return f"FAIL: {e}"
