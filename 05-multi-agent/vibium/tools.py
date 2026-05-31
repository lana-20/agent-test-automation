import os
from vibium import Page

TOOL_DEFINITIONS = [
    {
        "name": "navigate",
        "description": "Navigate to a URL.",
        "input_schema": {
            "type": "object",
            "properties": {"url": {"type": "string"}},
            "required": ["url"],
        },
    },
    {
        "name": "click",
        "description": "Click an element. Use selector (CSS) for reliability, or role+text as ARIA locator.",
        "input_schema": {
            "type": "object",
            "properties": {
                "selector": {"type": "string", "description": "CSS selector (preferred)"},
                "role": {"type": "string"},
                "text": {"type": "string"},
            },
        },
    },
    {
        "name": "hover",
        "description": "Hover over an element to reveal hidden controls (e.g. delete buttons). Use selector (CSS) or role+text.",
        "input_schema": {
            "type": "object",
            "properties": {
                "selector": {"type": "string", "description": "CSS selector (preferred)"},
                "role": {"type": "string"},
                "text": {"type": "string"},
            },
        },
    },
    {
        "name": "fill",
        "description": "Fill a text input. Locate by label, placeholder, or ARIA role.",
        "input_schema": {
            "type": "object",
            "properties": {
                "label": {"type": "string"},
                "value": {"type": "string"},
            },
            "required": ["label", "value"],
        },
    },
    {
        "name": "press",
        "description": "Press a keyboard key on the focused element. Common keys: Enter, Tab, Escape.",
        "input_schema": {
            "type": "object",
            "properties": {
                "key": {"type": "string", "description": "e.g. 'Enter', 'Tab', 'Escape'"},
            },
            "required": ["key"],
        },
    },
    {
        "name": "assert_visible",
        "description": "Assert an element is visible. Use selector (CSS) for reliability, or role+text as ARIA locator.",
        "input_schema": {
            "type": "object",
            "properties": {
                "selector": {"type": "string", "description": "CSS selector (preferred)"},
                "role": {"type": "string"},
                "text": {"type": "string"},
            },
        },
    },
    {
        "name": "assert_not_visible",
        "description": "Assert an element is NOT visible. Use selector (CSS) or role+text.",
        "input_schema": {
            "type": "object",
            "properties": {
                "selector": {"type": "string", "description": "CSS selector (preferred)"},
                "role": {"type": "string"},
                "text": {"type": "string"},
            },
        },
    },
    {
        "name": "get_text",
        "description": "Return the inner text of an element. Prefer selector (CSS); role+text as alternative.",
        "input_schema": {
            "type": "object",
            "properties": {
                "selector": {"type": "string", "description": "CSS selector (preferred)"},
                "role": {"type": "string"},
                "text": {"type": "string"},
            },
        },
    },
    {
        "name": "get_title",
        "description": "Return the current page title.",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "get_url",
        "description": "Return the current page URL.",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "screenshot",
        "description": "Take a screenshot and save it to the given path.",
        "input_schema": {
            "type": "object",
            "properties": {"path": {"type": "string"}},
            "required": ["path"],
        },
    },
    {
        "name": "count_elements",
        "description": "Count elements matching a CSS selector.",
        "input_schema": {
            "type": "object",
            "properties": {
                "selector": {"type": "string"},
            },
            "required": ["selector"],
        },
    },
]


def _locate(page: Page, selector: str | None, role: str | None, text: str | None):
    if selector:
        return page.find(selector)
    query: dict = {}
    if role:
        query["role"] = role
    if text:
        query["text"] = text
    return page.find(query)


def dispatch(name: str, inputs: dict, page: Page) -> str:
    try:
        if name == "navigate":
            page.go(inputs["url"])
            return f"Navigated to {inputs['url']}"

        if name == "click":
            sel, role, text = inputs.get("selector"), inputs.get("role"), inputs.get("text")
            _locate(page, sel, role, text).click()
            return f"Clicked selector={sel} role={role} text={text}"

        if name == "hover":
            sel, role, text = inputs.get("selector"), inputs.get("role"), inputs.get("text")
            _locate(page, sel, role, text).hover()
            return f"Hovered selector={sel} role={role} text={text}"

        if name == "fill":
            label, value = inputs["label"], inputs["value"]
            el = page.find({"role": "textbox", "text": label})
            if not el:
                el = page.find({"placeholder": label})
            el.fill(value)
            return f"Filled '{label}' with '{value}'"

        if name == "press":
            page.keyboard.press(inputs["key"])
            return f"Pressed: {inputs['key']}"

        if name == "assert_visible":
            sel, role, text = inputs.get("selector"), inputs.get("role"), inputs.get("text")
            el = _locate(page, sel, role, text)
            if not el.is_visible():
                return f"FAIL: not visible — selector={sel} role={role} text={text}"
            return f"VISIBLE: selector={sel} role={role} text={text}"

        if name == "assert_not_visible":
            sel, role, text = inputs.get("selector"), inputs.get("role"), inputs.get("text")
            el = _locate(page, sel, role, text)
            if el.is_visible():
                return f"FAIL: still visible — selector={sel} role={role} text={text}"
            return f"HIDDEN: selector={sel} role={role} text={text}"

        if name == "get_text":
            sel, role, text = inputs.get("selector"), inputs.get("role"), inputs.get("text")
            return _locate(page, sel, role, text).info.text

        if name == "get_title":
            return page.title()

        if name == "get_url":
            return page.url()

        if name == "screenshot":
            # page.screenshot() pipes raw PNG bytes over stdout, overflowing
            # asyncio's 64 KB readline buffer and corrupting the connection.
            # Short-circuit until vibium fixes its transport layer.
            return "FAIL: screenshot unavailable (vibium buffer limitation — skip and continue)"

        if name == "count_elements":
            return str(len(page.find_all(inputs["selector"])))

        return f"Unknown tool: {name}"

    except Exception as e:
        return f"FAIL: {e}"
