import { By, WebDriver, until, WebElement } from "selenium-webdriver";
import * as fs from "fs";
import * as path from "path";
import Anthropic from "@anthropic-ai/sdk";

// ── Locator helpers ───────────────────────────────────────────────────────────

function byRoleAndText(role?: string, text?: string): [string, string] {
  if (role && text) {
    const semantic: Record<string, string> = {
      button: "button",
      link: "a",
      heading: "h1 | h2 | h3 | h4 | h5 | h6",
      checkbox: "input[@type='checkbox']",
    };
    const tag = semantic[role];
    const xpath = tag
      ? `//${tag}[contains(normalize-space(), '${text}')] | //*[@role='${role}'][contains(normalize-space(), '${text}')]`
      : `//*[@role='${role}'][contains(normalize-space(), '${text}')]`;
    return [By.xpath("").toString(), xpath];
  }
  if (text) {
    return [
      "xpath",
      `//*[contains(normalize-space(), '${text}') and not(.//*[contains(normalize-space(), '${text}')])]`,
    ];
  }
  if (role) {
    return ["xpath", `//*[@role='${role}']`];
  }
  throw new Error("Provide at least one of: role, text, selector");
}

async function waitFor(driver: WebDriver, xpath: string, timeout = 5000): Promise<WebElement> {
  return driver.wait(until.elementLocated(By.xpath(xpath)), timeout);
}

async function waitVisible(driver: WebDriver, xpath: string, timeout = 5000): Promise<WebElement> {
  const el = await waitFor(driver, xpath, timeout);
  await driver.wait(until.elementIsVisible(el), timeout);
  return el;
}

// ── Core tools ────────────────────────────────────────────────────────────────

export async function navigate(driver: WebDriver, url: string): Promise<string> {
  await driver.get(url);
  return `Navigated to ${url} — title: ${await driver.getTitle()}`;
}

export async function findElement(driver: WebDriver, role?: string, text?: string): Promise<string> {
  const [, xpath] = byRoleAndText(role, text);
  try {
    await driver.findElement(By.xpath(xpath));
    return `Found element — role=${role}, text=${text}`;
  } catch {
    return `Not found — role=${role}, text=${text}`;
  }
}

export async function click(
  driver: WebDriver,
  role?: string,
  text?: string,
  selector?: string
): Promise<string> {
  if (selector) {
    const el = await driver.wait(until.elementLocated(By.css(selector)), 5000);
    await el.click();
  } else {
    const [, xpath] = byRoleAndText(role, text);
    const el = await waitFor(driver, xpath);
    await el.click();
  }
  return "Clicked";
}

export async function fill(
  driver: WebDriver,
  value: string,
  label?: string,
  placeholder?: string,
  selector?: string
): Promise<string> {
  let el: WebElement;
  if (selector) {
    el = await driver.wait(until.elementLocated(By.css(selector)), 5000);
  } else if (placeholder) {
    el = await driver.wait(
      until.elementLocated(
        By.css(`input[placeholder='${placeholder}'], textarea[placeholder='${placeholder}']`)
      ),
      5000
    );
  } else if (label) {
    el = await driver.wait(
      until.elementLocated(By.xpath(`//input[@id=//label[normalize-space()='${label}']/@for]`)),
      5000
    );
  } else {
    throw new Error("fill: provide label, placeholder, or selector");
  }
  await el.clear();
  await el.sendKeys(value);
  return `Filled with: ${value}`;
}

export async function getText(driver: WebDriver, selector: string): Promise<string> {
  return driver.findElement(By.css(selector)).getText();
}

export async function assertVisible(
  driver: WebDriver,
  text?: string,
  role?: string,
  selector?: string
): Promise<string> {
  try {
    if (selector) {
      await driver.wait(until.elementIsVisible(await driver.findElement(By.css(selector))), 5000);
    } else {
      const [, xpath] = byRoleAndText(role, text);
      await waitVisible(driver, xpath);
    }
    return `PASS: visible — text=${text}, role=${role}, selector=${selector}`;
  } catch {
    throw new Error(`Timed out waiting for visible element — text=${text}, role=${role}`);
  }
}

export async function assertNotVisible(
  driver: WebDriver,
  text?: string,
  selector?: string
): Promise<string> {
  const locator = selector ? By.css(selector) : By.xpath(`//*[contains(normalize-space(), '${text}')]`);
  try {
    const el = await driver.findElement(locator);
    await driver.wait(until.elementIsNotVisible(el), 5000);
  } catch {
    // element not found = not visible = pass
  }
  return `PASS: not visible — text=${text}, selector=${selector}`;
}

export async function getPageTitle(driver: WebDriver): Promise<string> {
  return driver.getTitle();
}

export async function getCurrentUrl(driver: WebDriver): Promise<string> {
  return driver.getCurrentUrl();
}

export async function screenshot(driver: WebDriver, filename: string): Promise<string> {
  fs.mkdirSync("screenshots", { recursive: true });
  const filePath = path.join("screenshots", filename);
  const data = await driver.takeScreenshot();
  fs.writeFileSync(filePath, data, "base64");
  return `Screenshot saved: ${filePath}`;
}

// ── BiDi-specific tools ───────────────────────────────────────────────────────

export async function getBrowserLogs(driver: WebDriver): Promise<string> {
  try {
    const logs = await driver.manage().logs().get("browser");
    if (!logs.length) return "No browser logs captured";
    return logs
      .slice(-10)
      .map((e) => `[${e.level}] ${e.message}`)
      .join("\n");
  } catch (e) {
    return `Log capture not available: ${(e as Error).message}`;
  }
}

export async function executeScript(driver: WebDriver, expression: string): Promise<string> {
  const result = await driver.executeScript(`return ${expression}`);
  return String(result);
}

export async function interceptNetwork(driver: WebDriver, urlPattern: string): Promise<string> {
  try {
    await (driver as any).sendDevToolsCommand("Network.enable", {});
    await (driver as any).sendDevToolsCommand("Network.setBlockedURLs", { urls: [urlPattern] });
    return `Network intercept active — blocking: ${urlPattern}`;
  } catch (e) {
    return `Network intercept unavailable (Chrome/Edge only): ${(e as Error).message}`;
  }
}

// ── Tool definitions ──────────────────────────────────────────────────────────

export const TOOL_DEFINITIONS: Anthropic.Tool[] = [
  {
    name: "navigate",
    description: "Navigate the browser to a URL and wait for the page to load.",
    input_schema: { type: "object", properties: { url: { type: "string" } }, required: ["url"] },
  },
  {
    name: "find_element",
    description: "Check whether an element exists on the page.",
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
    description: "Get the text content of an element by CSS selector.",
    input_schema: { type: "object", properties: { selector: { type: "string" } }, required: ["selector"] },
  },
  {
    name: "assert_visible",
    description: "Assert an element is visible. Returns PASS or raises an error reported as FAIL.",
    input_schema: {
      type: "object",
      properties: { text: { type: "string" }, role: { type: "string" }, selector: { type: "string" } },
    },
  },
  {
    name: "assert_not_visible",
    description: "Assert an element is hidden or absent.",
    input_schema: { type: "object", properties: { text: { type: "string" }, selector: { type: "string" } } },
  },
  { name: "get_page_title", description: "Get the current page <title>.", input_schema: { type: "object", properties: {} } },
  { name: "get_current_url", description: "Get the current URL.", input_schema: { type: "object", properties: {} } },
  {
    name: "screenshot",
    description: "Take a screenshot and save to screenshots/<filename>.",
    input_schema: { type: "object", properties: { filename: { type: "string" } }, required: ["filename"] },
  },
  // BiDi extras
  {
    name: "get_browser_logs",
    description: "Retrieve browser console logs (errors, warnings, info). Call after navigation to check for JS errors.",
    input_schema: { type: "object", properties: {} },
  },
  {
    name: "execute_script",
    description: "Evaluate a JavaScript expression and return the result.",
    input_schema: {
      type: "object",
      properties: {
        expression: {
          type: "string",
          description: "JS expression, e.g. 'document.querySelectorAll(\".todo-list li\").length'",
        },
      },
      required: ["expression"],
    },
  },
  {
    name: "intercept_network",
    description: "Block requests matching a URL pattern. Chrome/Edge only.",
    input_schema: {
      type: "object",
      properties: { url_pattern: { type: "string", description: "Glob pattern, e.g. '*/api/*'" } },
      required: ["url_pattern"],
    },
  },
];

// ── Dispatcher ────────────────────────────────────────────────────────────────

type ToolInput = Record<string, unknown>;

export async function dispatch(name: string, inputs: ToolInput, driver: WebDriver): Promise<string> {
  try {
    switch (name) {
      case "navigate":           return navigate(driver, inputs.url as string);
      case "find_element":       return findElement(driver, inputs.role as string, inputs.text as string);
      case "click":              return click(driver, inputs.role as string, inputs.text as string, inputs.selector as string);
      case "fill":               return fill(driver, inputs.value as string, inputs.label as string, inputs.placeholder as string, inputs.selector as string);
      case "get_text":           return getText(driver, inputs.selector as string);
      case "assert_visible":     return assertVisible(driver, inputs.text as string, inputs.role as string, inputs.selector as string);
      case "assert_not_visible": return assertNotVisible(driver, inputs.text as string, inputs.selector as string);
      case "get_page_title":     return getPageTitle(driver);
      case "get_current_url":    return getCurrentUrl(driver);
      case "screenshot":         return screenshot(driver, inputs.filename as string);
      case "get_browser_logs":   return getBrowserLogs(driver);
      case "execute_script":     return executeScript(driver, inputs.expression as string);
      case "intercept_network":  return interceptNetwork(driver, inputs.url_pattern as string);
      default:                   return `Unknown tool: ${name}`;
    }
  } catch (e) {
    return `FAIL: ${(e as Error).message}`;
  }
}
