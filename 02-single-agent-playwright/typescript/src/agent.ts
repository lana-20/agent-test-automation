import Anthropic from "@anthropic-ai/sdk";
import { chromium, Page } from "playwright";
import { TOOL_DEFINITIONS, dispatch } from "./tools";

const SYSTEM_PROMPT = `You are a senior test automation engineer executing browser-based tests.

Rules:
- Work step by step. After each action, verify the result before proceeding.
- Prefer locating elements by ARIA role + visible text. Fall back to CSS selectors only when needed.
- When an assertion fails, stop and report FAIL with the exact reason.
- At the end, output a concise test report: overall PASS or FAIL, with one bullet per step.
- Take a screenshot after key steps to document evidence.`;

export interface StepLog {
  tool: string;
  input: Record<string, unknown>;
  result: string;
}

export async function run(task: string, headless = false): Promise<StepLog[]> {
  const client = new Anthropic();
  const log: StepLog[] = [];

  const browser = await chromium.launch({ headless });
  const context = await browser.newContext({ viewport: { width: 1280, height: 800 } });
  const page: Page = await context.newPage();

  const messages: Anthropic.MessageParam[] = [
    { role: "user", content: task },
  ];

  console.log(`\nTask: ${task}`);
  console.log("=".repeat(60));

  try {
    while (true) {
      const response = await client.messages.create({
        model: "claude-sonnet-4-6",
        max_tokens: 4096,
        system: SYSTEM_PROMPT,
        tools: TOOL_DEFINITIONS,
        messages,
      });

      messages.push({ role: "assistant", content: response.content });

      const toolResults: Anthropic.ToolResultBlockParam[] = [];

      for (const block of response.content) {
        if (block.type === "text") {
          console.log(`\nAgent: ${block.text}`);
        } else if (block.type === "tool_use") {
          const inputs = block.input as Record<string, unknown>;
          console.log(`  -> ${block.name}(${JSON.stringify(inputs)})`);
          const result = await dispatch(block.name, inputs, page);
          console.log(`     ${result}`);
          log.push({ tool: block.name, input: inputs, result });
          toolResults.push({
            type: "tool_result",
            tool_use_id: block.id,
            content: result,
          });
        }
      }

      if (toolResults.length > 0) {
        messages.push({ role: "user", content: toolResults });
      }

      if (response.stop_reason === "end_turn") break;
    }
  } finally {
    await context.close();
    await browser.close();
  }

  return log;
}
