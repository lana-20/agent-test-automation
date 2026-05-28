import Anthropic from "@anthropic-ai/sdk";
import { chromium } from "playwright";
import { TestScenario, RunnerResult } from "../models";
import { TOOL_DEFINITIONS, dispatch } from "../tools";

const SYSTEM = `You are a senior test automation engineer executing browser-based tests.

Rules:
- Work step by step. After each action, verify the result before proceeding.
- Prefer locating elements by ARIA role + visible text.
- When an assertion fails, stop and report FAIL with the exact reason.
- At the end, output a concise report starting with PASS or FAIL, followed by one bullet per step.`;

export async function run(scenario: TestScenario, headless = true): Promise<RunnerResult> {
  const client = new Anthropic();
  const prefix = `[Runner:${scenario.id}]`;

  const task =
    `Scenario: ${scenario.title}\n` +
    `Category: ${scenario.category} · Priority: ${scenario.priority}\n` +
    `Expected outcome: ${scenario.expected_outcome}\n\n` +
    `Start URL: ${scenario.url}\n\n` +
    "Steps:\n" +
    scenario.steps.map((s, i) => `${i + 1}. ${s}`).join("\n");

  const messages: Anthropic.MessageParam[] = [{ role: "user", content: task }];
  const stepLog: RunnerResult["stepLog"] = [];

  const browser = await chromium.launch({ headless });
  const context = await browser.newContext({ viewport: { width: 1280, height: 800 } });
  const page = await context.newPage();
  let finalText = "";

  try {
    while (true) {
      const response = await client.messages.create({
        model: "claude-sonnet-4-6",
        max_tokens: 4096,
        system: SYSTEM,
        tools: TOOL_DEFINITIONS,
        messages,
      });
      messages.push({ role: "assistant", content: response.content });
      const toolResults: Anthropic.ToolResultBlockParam[] = [];

      for (const block of response.content) {
        if (block.type === "text") {
          finalText = block.text;
          console.log(`${prefix} ${block.text.slice(0, 120)}`);
        } else if (block.type === "tool_use") {
          const inputs = block.input as Record<string, unknown>;
          const result = await dispatch(block.name, inputs, page);
          console.log(`${prefix}   -> ${block.name}: ${result.slice(0, 80)}`);
          stepLog.push({ tool: block.name, input: inputs, result });
          toolResults.push({ type: "tool_result", tool_use_id: block.id, content: result });
        }
      }

      if (toolResults.length > 0) messages.push({ role: "user", content: toolResults });
      if (response.stop_reason === "end_turn") break;
    }
  } finally {
    await browser.close();
  }

  const firstWord = finalText.trim().split(/\s+/)[0]?.toUpperCase() ?? "";
  return {
    scenarioId: scenario.id,
    title: scenario.title,
    passed: firstWord !== "FAIL",
    summary: finalText,
    stepLog,
  };
}
