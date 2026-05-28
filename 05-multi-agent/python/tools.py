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
        "description": "Click an element by ARIA role and visible text.",
        "input_schema": {
            "type": "object",
            "properties": {
                "role": {"type": "string"},
                "text": {"type": "string"},
            },
            "required": ["role", "text"],
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
        "name": "assert_visible",
        "description": "Assert that an element with given role and text is visible.",
        "input_schema": {
            "type": "object",
            "properties": {
                "role": {"type": "string"},
                "text": {"type": "string"},
            },
            "required": ["role", "text"],
        },
    },
    {
        "name": "assert_not_visible",
        "description": "Assert that an element with given role and text is NOT visible.",
        "input_schema": {
            "type": "object",
            "properties": {
                "role": {"type": "string"},
                "text": {"type": "string"},
            },
            "required": ["role", "text"],
        },
    },
    {
        "name": "get_text",
        "description": "Return the inner text of an element by role and text.",
        "input_schema": {
            "type": "object",
            "properties": {
                "role": {"type": "string"},
                "text": {"type": "string"},
            },
            "required": ["role", "text"],
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
        page.get_by_role(inputs["role"], name=inputs["text"]).click()
        return f"Clicked {inputs['role']} '{inputs['text']}'"

    if name == "fill":
        label = inputs["label"]
        value = inputs["value"]
        loc = page.get_by_label(label)
        if not loc.count():
            loc = page.get_by_placeholder(label)
        loc.fill(value)
        return f"Filled '{label}' with '{value}'"

    if name == "assert_visible":
        loc = page.get_by_role(inputs["role"], name=inputs["text"])
        try:
            loc.wait_for(state="visible", timeout=5000)
            return f"VISIBLE: {inputs['role']} '{inputs['text']}'"
        except PlaywrightTimeout:
            return f"FAIL: {inputs['role']} '{inputs['text']}' not visible"

    if name == "assert_not_visible":
        loc = page.get_by_role(inputs["role"], name=inputs["text"])
        try:
            loc.wait_for(state="hidden", timeout=3000)
            return f"HIDDEN: {inputs['role']} '{inputs['text']}'"
        except PlaywrightTimeout:
            return f"FAIL: {inputs['role']} '{inputs['text']}' is still visible"

    if name == "get_text":
        return page.get_by_role(inputs["role"], name=inputs["text"]).inner_text()

    if name == "get_title":
        return page.title()

    if name == "get_url":
        return page.url

    if name == "screenshot":
        page.screenshot(path=inputs["path"])
        return f"Screenshot saved to {inputs['path']}"

    if name == "count_elements":
        text = inputs.get("text")
        loc = (
            page.get_by_role(inputs["role"], name=text)
            if text
            else page.get_by_role(inputs["role"])
        )
        return str(loc.count())

    return f"Unknown tool: {name}"
