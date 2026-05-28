import Anthropic from "@anthropic-ai/sdk";
import { TestScenario } from "../models";

const client = new Anthropic();

const PLAN_TOOL: Anthropic.Tool = {
  name: "create_test_plan",
  description: "Output a structured test plan as a list of prioritised, categorised scenarios.",
  input_schema: {
    type: "object",
    properties: {
      scenarios: {
        type: "array",
        items: {
          type: "object",
          properties: {
            id:               { type: "string" },
            title:            { type: "string" },
            url:              { type: "string" },
            steps:            { type: "array", items: { type: "string" } },
            priority:         { type: "string", enum: ["high", "medium", "low"] },
            category:         { type: "string" },
            expected_outcome: { type: "string" },
          },
          required: ["id", "title", "url", "steps", "priority", "category", "expected_outcome"],
        },
      },
    },
    required: ["scenarios"],
  },
};

const SYSTEM =
  "You are a senior QA architect. Given a feature description or spec, produce a structured test plan.\n\n" +
  "Rules:\n" +
  "- Break the scope into 4–6 independent scenarios, each runnable in a fresh browser.\n" +
  "- Assign a priority (high / medium / low) and a category (smoke, regression, edge-case, etc.).\n" +
  "- Write a one-sentence expected_outcome for each scenario.\n" +
  "- High-priority scenarios cover the core happy path; medium covers variations; low covers edge cases.";

export async function plan(spec: string): Promise<TestScenario[]> {
  const response = await client.messages.create({
    model: "claude-sonnet-4-6",
    max_tokens: 2048,
    system: SYSTEM,
    tools: [PLAN_TOOL],
    tool_choice: { type: "tool", name: "create_test_plan" },
    messages: [{ role: "user", content: spec }],
  });

  const toolBlock = response.content.find((b) => b.type === "tool_use");
  if (!toolBlock || toolBlock.type !== "tool_use") {
    throw new Error("Architect did not return a tool_use block");
  }

  const scenarios = (toolBlock.input as { scenarios: TestScenario[] }).scenarios;

  console.log(`\n[Architect] Generated ${scenarios.length} scenario(s):`);
  for (const s of scenarios) {
    console.log(`  [${s.id}] [${s.priority.toUpperCase()}] ${s.title}  (${s.category})`);
  }

  return scenarios;
}
