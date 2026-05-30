from playwright.sync_api import Page, TimeoutError as PlaywrightTimeout

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
        "description": "Fill a text input. Locate by label or placeholder.",
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
        "description": "Press a keyboard key on the focused element or a specific selector. Common keys: Enter, Tab, Escape.",
        "input_schema": {
            "type": "object",
            "properties": {
                "key":      {"type": "string", "description": "e.g. 'Enter', 'Tab', 'Escape'"},
                "selector": {"type": "string", "description": "CSS selector to focus first (optional)"},
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
        "description": "Return the inner text of an element. Prefer selector (CSS) for reliability; role+text as alternative.",
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
        "description": "Count elements matching a role (and optionally text).",
        "input_schema": {
            "type": "object",
            "properties": {
                "role": {"type": "string"},
                "text": {"type": "string"},
            },
            "required": ["role"],
        },
    },
]


def dispatch(name: str, inputs: dict, page: Page) -> str:
    if name == "navigate":
        page.goto(inputs["url"])
        return f"Navigated to {inputs['url']}"

    if name == "click":
        sel, role, text = inputs.get("selector"), inputs.get("role"), inputs.get("text")
        loc = page.locator(sel) if sel else page.get_by_role(role, name=text)  # type: ignore[arg-type]
        try:
            loc.first.click(timeout=5000)
            return f"Clicked selector={sel} role={role} text={text}"
        except PlaywrightTimeout:
            return f"TIMEOUT: element not found or not clickable — selector={sel} role={role} text={text}"

    if name == "hover":
        sel, role, text = inputs.get("selector"), inputs.get("role"), inputs.get("text")
        loc = page.locator(sel) if sel else page.get_by_role(role, name=text)  # type: ignore[arg-type]
        try:
            loc.first.hover(timeout=5000)
            return f"Hovered selector={sel} role={role} text={text}"
        except PlaywrightTimeout:
            return f"TIMEOUT: element not found or not visible — selector={sel} role={role} text={text}"

    if name == "fill":
        label = inputs["label"]
        value = inputs["value"]
        loc = page.get_by_label(label)
        if not loc.count():
            loc = page.get_by_placeholder(label)
        loc.fill(value)
        return f"Filled '{label}' with '{value}'"

    if name == "assert_visible":
        sel, role, text = inputs.get("selector"), inputs.get("role"), inputs.get("text")
        loc = page.locator(sel) if sel else page.get_by_role(role, name=text)  # type: ignore[arg-type]
        try:
            loc.first.wait_for(state="visible", timeout=5000)
            return f"VISIBLE: selector={sel} role={role} text={text}"
        except PlaywrightTimeout:
            return f"FAIL: not visible — selector={sel} role={role} text={text}"

    if name == "assert_not_visible":
        sel, role, text = inputs.get("selector"), inputs.get("role"), inputs.get("text")
        loc = page.locator(sel) if sel else page.get_by_role(role, name=text)  # type: ignore[arg-type]
        try:
            loc.first.wait_for(state="hidden", timeout=3000)
            return f"HIDDEN: selector={sel} role={role} text={text}"
        except PlaywrightTimeout:
            return f"FAIL: still visible — selector={sel} role={role} text={text}"

    if name == "get_text":
        sel, role, text = inputs.get("selector"), inputs.get("role"), inputs.get("text")
        loc = page.locator(sel) if sel else page.get_by_role(role, name=text)  # type: ignore[arg-type]
        try:
            return loc.first.inner_text(timeout=5000)
        except PlaywrightTimeout:
            return f"TIMEOUT: element not found or not visible — selector={sel} role={role} text={text}"

    if name == "get_title":
        return page.title()

    if name == "get_url":
        return page.url

    if name == "screenshot":
        page.screenshot(path=inputs["path"])
        return f"Screenshot saved to {inputs['path']}"

    if name == "press":
        key = inputs["key"]
        selector = inputs.get("selector")
        if selector:
            page.locator(selector).press(key)
        else:
            page.keyboard.press(key)
        return f"Pressed: {key}"

    if name == "count_elements":
        text = inputs.get("text")
        loc = (
            page.get_by_role(inputs["role"], name=text)
            if text
            else page.get_by_role(inputs["role"])
        )
        return str(loc.count())

    return f"Unknown tool: {name}"
