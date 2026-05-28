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
    description: "Click an element by ARIA role and visible text.",
    input_schema: {
      type: "object",
      properties: {
        role: { type: "string" },
        text: { type: "string" },
      },
      required: ["role", "text"],
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
    name: "assert_visible",
    description: "Assert that an element with given role and text is visible.",
    input_schema: {
      type: "object",
      properties: {
        role: { type: "string" },
        text: { type: "string" },
      },
      required: ["role", "text"],
    },
  },
  {
    name: "assert_not_visible",
    description: "Assert that an element with given role and text is NOT visible.",
    input_schema: {
      type: "object",
      properties: {
        role: { type: "string" },
        text: { type: "string" },
      },
      required: ["role", "text"],
    },
  },
  {
    name: "get_text",
    description: "Return the inner text of an element by role and text.",
    input_schema: {
      type: "object",
      properties: {
        role: { type: "string" },
        text: { type: "string" },
      },
      required: ["role", "text"],
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
    await page.getByRole(inputs.role as AriaRole, { name: inputs.text as string }).click();
    return `Clicked ${inputs.role} '${inputs.text}'`;
  }

  if (name === "fill") {
    const label = inputs.label as string;
    const value = inputs.value as string;
    let loc = page.getByLabel(label);
    if (!(await loc.count())) loc = page.getByPlaceholder(label);
    await loc.fill(value);
    return `Filled '${label}' with '${value}'`;
  }

  if (name === "assert_visible") {
    const loc = page.getByRole(inputs.role as AriaRole, { name: inputs.text as string });
    try {
      await loc.waitFor({ state: "visible", timeout: 5000 });
      return `VISIBLE: ${inputs.role} '${inputs.text}'`;
    } catch {
      return `FAIL: ${inputs.role} '${inputs.text}' not visible`;
    }
  }

  if (name === "assert_not_visible") {
    const loc = page.getByRole(inputs.role as AriaRole, { name: inputs.text as string });
    try {
      await loc.waitFor({ state: "hidden", timeout: 3000 });
      return `HIDDEN: ${inputs.role} '${inputs.text}'`;
    } catch {
      return `FAIL: ${inputs.role} '${inputs.text}' is still visible`;
    }
  }

  if (name === "get_text") {
    return await page.getByRole(inputs.role as AriaRole, { name: inputs.text as string }).innerText();
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
