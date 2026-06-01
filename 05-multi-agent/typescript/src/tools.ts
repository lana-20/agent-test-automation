import Anthropic from "@anthropic-ai/sdk";
import { Page } from "playwright";

export const TOOL_DEFINITIONS: Anthropic.Tool[] = [
  {
    name: "navigate",
    description: "Navigate to a URL.",
    input_schema: {
      type: "object",
      properties: { url: { type: "string" } },
      required: ["url"],
    },
  },
  {
    name: "click",
    description: "Click an element. Use selector (CSS) for reliability, or role+text as ARIA locator.",
    input_schema: {
      type: "object",
      properties: {
        selector: { type: "string", description: "CSS selector (preferred)" },
        role: { type: "string" },
        text: { type: "string" },
      },
    },
  },
  {
    name: "hover",
    description: "Hover over an element to reveal hidden controls (e.g. delete buttons). Use selector (CSS) or role+text.",
    input_schema: {
      type: "object",
      properties: {
        selector: { type: "string", description: "CSS selector (preferred)" },
        role: { type: "string" },
        text: { type: "string" },
      },
    },
  },
  {
    name: "fill",
    description: "Fill a text input. Locate by label or placeholder.",
    input_schema: {
      type: "object",
      properties: {
        label: { type: "string" },
        value: { type: "string" },
      },
      required: ["label", "value"],
    },
  },
  {
    name: "press",
    description: "Press a keyboard key on the focused element or a specific selector. Common keys: Enter, Tab, Escape.",
    input_schema: {
      type: "object",
      properties: {
        key: { type: "string", description: "e.g. 'Enter', 'Tab', 'Escape'" },
        selector: { type: "string", description: "CSS selector to focus first (optional)" },
      },
      required: ["key"],
    },
  },
  {
    name: "assert_visible",
    description: "Assert an element is visible. Use selector (CSS) for reliability, or role+text as ARIA locator.",
    input_schema: {
      type: "object",
      properties: {
        selector: { type: "string", description: "CSS selector (preferred)" },
        role: { type: "string" },
        text: { type: "string" },
      },
    },
  },
  {
    name: "assert_not_visible",
    description: "Assert an element is NOT visible. Use selector (CSS) or role+text.",
    input_schema: {
      type: "object",
      properties: {
        selector: { type: "string", description: "CSS selector (preferred)" },
        role: { type: "string" },
        text: { type: "string" },
      },
    },
  },
  {
    name: "get_text",
    description: "Return the inner text of an element. Prefer selector (CSS); role+text as alternative.",
    input_schema: {
      type: "object",
      properties: {
        selector: { type: "string", description: "CSS selector (preferred)" },
        role: { type: "string" },
        text: { type: "string" },
      },
    },
  },
  {
    name: "get_title",
    description: "Return the current page title.",
    input_schema: { type: "object", properties: {} },
  },
  {
    name: "get_url",
    description: "Return the current page URL.",
    input_schema: { type: "object", properties: {} },
  },
  {
    name: "screenshot",
    description: "Take a screenshot and save it to the given path.",
    input_schema: {
      type: "object",
      properties: { path: { type: "string" } },
      required: ["path"],
    },
  },
  {
    name: "count_elements",
    description: "Count elements matching a role (and optionally text).",
    input_schema: {
      type: "object",
      properties: {
        role: { type: "string" },
        text: { type: "string" },
      },
      required: ["role"],
    },
  },
];

type AriaRole = Parameters<Page["getByRole"]>[0];

export async function dispatch(
  name: string,
  inputs: Record<string, unknown>,
  page: Page
): Promise<string> {
  if (name === "navigate") {
    await page.goto(inputs.url as string);
    return `Navigated to ${inputs.url}`;
  }

  if (name === "click") {
    const sel = inputs.selector as string | undefined;
    const loc = sel
      ? page.locator(sel)
      : page.getByRole(inputs.role as AriaRole, { name: inputs.text as string });
    try {
      await loc.first().click({ timeout: 5000 });
      return `Clicked selector=${sel} role=${inputs.role} text=${inputs.text}`;
    } catch {
      return `TIMEOUT: element not found or not clickable — selector=${sel} role=${inputs.role} text=${inputs.text}`;
    }
  }

  if (name === "hover") {
    const sel = inputs.selector as string | undefined;
    const loc = sel
      ? page.locator(sel)
      : page.getByRole(inputs.role as AriaRole, { name: inputs.text as string });
    try {
      await loc.first().hover({ timeout: 5000 });
      return `Hovered selector=${sel} role=${inputs.role} text=${inputs.text}`;
    } catch {
      return `TIMEOUT: element not found or not visible — selector=${sel} role=${inputs.role} text=${inputs.text}`;
    }
  }

  if (name === "fill") {
    const label = inputs.label as string;
    const value = inputs.value as string;
    let loc = page.getByLabel(label);
    if (!(await loc.count())) loc = page.getByPlaceholder(label);
    await loc.fill(value);
    return `Filled '${label}' with '${value}'`;
  }

  if (name === "press") {
    const key = inputs.key as string;
    const sel = inputs.selector as string | undefined;
    if (sel) {
      await page.locator(sel).press(key);
    } else {
      await page.keyboard.press(key);
    }
    return `Pressed: ${key}`;
  }

  if (name === "assert_visible") {
    const sel = inputs.selector as string | undefined;
    const loc = sel
      ? page.locator(sel)
      : page.getByRole(inputs.role as AriaRole, { name: inputs.text as string });
    try {
      await loc.first().waitFor({ state: "visible", timeout: 5000 });
      return `VISIBLE: selector=${sel} role=${inputs.role} text=${inputs.text}`;
    } catch {
      return `FAIL: not visible — selector=${sel} role=${inputs.role} text=${inputs.text}`;
    }
  }

  if (name === "assert_not_visible") {
    const sel = inputs.selector as string | undefined;
    const loc = sel
      ? page.locator(sel)
      : page.getByRole(inputs.role as AriaRole, { name: inputs.text as string });
    try {
      await loc.first().waitFor({ state: "hidden", timeout: 3000 });
      return `HIDDEN: selector=${sel} role=${inputs.role} text=${inputs.text}`;
    } catch {
      return `FAIL: still visible — selector=${sel} role=${inputs.role} text=${inputs.text}`;
    }
  }

  if (name === "get_text") {
    const sel = inputs.selector as string | undefined;
    const loc = sel
      ? page.locator(sel)
      : page.getByRole(inputs.role as AriaRole, { name: inputs.text as string });
    try {
      return await loc.first().innerText({ timeout: 5000 });
    } catch {
      return `TIMEOUT: element not found — selector=${sel} role=${inputs.role} text=${inputs.text}`;
    }
  }

  if (name === "get_title") {
    return await page.title();
  }

  if (name === "get_url") {
    return page.url();
  }

  if (name === "screenshot") {
    await page.screenshot({ path: inputs.path as string });
    return `Screenshot saved to ${inputs.path}`;
  }

  if (name === "count_elements") {
    const text = inputs.text as string | undefined;
    const loc = text
      ? page.getByRole(inputs.role as AriaRole, { name: text })
      : page.getByRole(inputs.role as AriaRole);
    return String(await loc.count());
  }

  return `Unknown tool: ${name}`;
}
