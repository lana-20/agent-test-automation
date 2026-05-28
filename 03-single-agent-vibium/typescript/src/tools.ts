import { browser, type Page, type Element } from "vibium";
import * as fs from "fs";
import * as path from "path";
import Anthropic from "@anthropic-ai/sdk";

// ── Tool implementations (Vibium JS API) ─────────────────────────────────────

export async function navigate(page: Page, url: string): Promise<string> {
  await page.go(url);
  return `Navigated to ${url} — title: ${await page.title()}`;
}

export async function findElement(
  page: Page,
  role?: string,
  text?: string
): Promise<string> {
  const query: Record<string, string> = {};
  if (role) query.role = role;
  if (text) query.text = text;
  try {
    await page.find(query);
    return `Found element — role=${role}, text=${text}`;
  } catch {
    return `Not found — role=${role}, text=${text}`;
  }
}

export async function click(
  page: Page,
  role?: string,
  text?: string,
  selector?: string
): Promise<string> {
  const el: Element = selector
    ? await page.find(selector)
    : await page.find({ ...(role && { role }), ...(text && { text }) });
  await el.click();
  return "Clicked";
}

export async function fill(
  page: Page,
  value: string,
  label?: string,
  placeholder?: string,
  selector?: string
): Promise<string> {
  let el: Element;
  if (selector) {
    el = await page.find(selector);
  } else if (label) {
    el = await page.find({ role: "textbox", text: label });
  } else if (placeholder) {
    el = await page.find({ placeholder });
  } else {
    throw new Error("fill: provide label, placeholder, or selector");
  }
  await el.fill(value);
  return `Filled with: ${value}`;
}

export async function getText(page: Page, selector: string): Promise<string> {
  const el = await page.find(selector);
  return (await el.innerText()) ?? "";
}

export async function assertVisible(
  page: Page,
  text?: string,
  role?: string,
  selector?: string
): Promise<string> {
  const query = selector
    ? selector
    : { ...(role && { role }), ...(text && { text }) };
  const el = await page.find(query);
  if (!(await el.isVisible())) {
    throw new Error(`Element not visible — text=${text}, role=${role}`);
  }
  return `PASS: visible — text=${text}, role=${role}, selector=${selector}`;
}

export async function assertNotVisible(
  page: Page,
  text?: string,
  selector?: string
): Promise<string> {
  try {
    const query = selector ?? { text: text! };
    const el = await page.find(query);
    if (await el.isVisible()) {
      throw new Error(`Element is still visible — text=${text}`);
    }
  } catch (e) {
    if ((e as Error).message.includes("still visible")) throw e;
  }
  return `PASS: not visible — text=${text}, selector=${selector}`;
}

export async function getPageTitle(page: Page): Promise<string> {
  return page.title();
}

export async function getCurrentUrl(page: Page): Promise<string> {
  return page.url;
}

export async function screenshot(page: Page, filename: string): Promise<string> {
  fs.mkdirSync("screenshots", { recursive: true });
  const filePath = path.join("screenshots", filename);
  await page.capture.screenshot({ path: filePath });
  return `Screenshot saved: ${filePath}`;
}

// ── Tool definitions (identical to Module 02) ─────────────────────────────────

export const TOOL_DEFINITIONS: Anthropic.Tool[] = [
  {
    name: "navigate",
    description: "Navigate the browser to a URL and wait for the page to load.",
    input_schema: {
      type: "object",
      properties: { url: { type: "string" } },
      required: ["url"],
    },
  },
  {
    name: "find_element",
    description: "Check whether an element exists on the page. Returns count of matches.",
    input_schema: {
      type: "object",
      properties: {
        role: { type: "string", description: "ARIA role: button, link, textbox, heading, checkbox, …" },
        text: { type: "string", description: "Visible text or accessible name" },
      },
    },
  },
  {
    name: "click",
    description: "Click an element. Prefer role+text over selector.",
    input_schema: {
      type: "object",
      properties: {
        role: { type: "string" },
        text: { type: "string" },
        selector: { type: "string", description: "CSS selector — use as fallback only" },
      },
    },
  },
  {
    name: "fill",
    description: "Type text into an input. Use label or placeholder to locate it.",
    input_schema: {
      type: "object",
      properties: {
        value: { type: "string" },
        label: { type: "string" },
        placeholder: { type: "string" },
        selector: { type: "string" },
      },
      required: ["value"],
    },
  },
  {
    name: "get_text",
    description: "Get the inner text of an element by CSS selector.",
    input_schema: {
      type: "object",
      properties: { selector: { type: "string" } },
      required: ["selector"],
    },
  },
  {
    name: "assert_visible",
    description: "Assert an element is visible. Returns PASS or raises an error reported as FAIL.",
    input_schema: {
      type: "object",
      properties: {
        text: { type: "string" },
        role: { type: "string" },
        selector: { type: "string" },
      },
    },
  },
  {
    name: "assert_not_visible",
    description: "Assert an element is hidden or absent.",
    input_schema: {
      type: "object",
      properties: {
        text: { type: "string" },
        selector: { type: "string" },
      },
    },
  },
  {
    name: "get_page_title",
    description: "Get the current page <title>.",
    input_schema: { type: "object", properties: {} },
  },
  {
    name: "get_current_url",
    description: "Get the current URL.",
    input_schema: { type: "object", properties: {} },
  },
  {
    name: "screenshot",
    description: "Take a screenshot and save to screenshots/<filename>.",
    input_schema: {
      type: "object",
      properties: { filename: { type: "string", description: "e.g. step-01.png" } },
      required: ["filename"],
    },
  },
];

// ── Tool dispatcher ───────────────────────────────────────────────────────────

type ToolInput = Record<string, unknown>;

export async function dispatch(
  name: string,
  inputs: ToolInput,
  page: Page
): Promise<string> {
  try {
    switch (name) {
      case "navigate":        return navigate(page, inputs.url as string);
      case "find_element":    return findElement(page, inputs.role as string, inputs.text as string);
      case "click":           return click(page, inputs.role as string, inputs.text as string, inputs.selector as string);
      case "fill":            return fill(page, inputs.value as string, inputs.label as string, inputs.placeholder as string, inputs.selector as string);
      case "get_text":        return getText(page, inputs.selector as string);
      case "assert_visible":  return assertVisible(page, inputs.text as string, inputs.role as string, inputs.selector as string);
      case "assert_not_visible": return assertNotVisible(page, inputs.text as string, inputs.selector as string);
      case "get_page_title":  return getPageTitle(page);
      case "get_current_url": return getCurrentUrl(page);
      case "screenshot":      return screenshot(page, inputs.filename as string);
      default:                return `Unknown tool: ${name}`;
    }
  } catch (e) {
    return `FAIL: ${(e as Error).message}`;
  }
}
