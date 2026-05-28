import Anthropic from "@anthropic-ai/sdk";
import { TestScenario } from "./models";

const client = new Anthropic();

const PLAN_TOOL: Anthropic.Tool = {
  name: "create_test_plan",
  description: "Output a structured test plan as a list of independent scenarios.",
  input_schema: {
    type: "object",
    properties: {
      scenarios: {
        type: "array",
        items: {
          type: "object",
          properties: {
            id:    { type: "string", description: "Short identifier, e.g. TC-01" },
            title: { type: "string", description: "One-line scenario title" },
            url:   { type: "string", description: "Starting URL for this scenario" },
            steps: {
              type: "array",
              items: { type: "string" },
              description: "Ordered list of test steps",
            },
          },
          required: ["id", "title", "url", "steps"],
        },
      },
    },
    required: ["scenarios"],
  },
};

const SYSTEM =
  "You are a senior QA architect. Given a feature description, produce a " +
  "concise test plan broken into independent scenarios. Each scenario must " +
  "be runnable in isolation in a fresh browser. Aim for 3–5 scenarios.";

export async function plan(feature: string): Promise<TestScenario[]> {
  const response = await client.messages.create({
    model: "claude-sonnet-4-6",
    max_tokens: 2048,
    system: SYSTEM,
    tools: [PLAN_TOOL],
    tool_choice: { type: "tool", name: "create_test_plan" },
    messages: [{ role: "user", content: feature }],
  });

  const toolBlock = response.content.find((b) => b.type === "tool_use");
  if (!toolBlock || toolBlock.type !== "tool_use") {
    throw new Error("Orchestrator did not return a tool_use block");
  }

  const raw = (toolBlock.input as { scenarios: TestScenario[] }).scenarios;

  console.log(`\nOrchestrator generated ${raw.length} scenario(s):`);
  for (const s of raw) {
    console.log(`  [${s.id}] ${s.title}  (${s.steps.length} steps)`);
  }

  return raw;
}
