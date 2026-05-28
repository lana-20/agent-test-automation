import Anthropic from "@anthropic-ai/sdk";
import { TestScenario, RunnerResult, Finding } from "../models";

const client = new Anthropic();

const CLASSIFY_TOOL: Anthropic.Tool = {
  name: "classify_failure",
  description: "Classify a test failure and recommend a next action.",
  input_schema: {
    type: "object",
    properties: {
      classification: {
        type: "string",
        enum: ["bug", "expected-failure", "flaky", "environment"],
        description:
          "bug: app behaved incorrectly; " +
          "expected-failure: known issue or intentionally broken; " +
          "flaky: timing/race condition; " +
          "environment: infra or network problem",
      },
      severity: { type: "string", enum: ["critical", "high", "medium", "low"] },
      description: { type: "string", description: "2–3 sentence technical description." },
      suggestedAction: { type: "string", description: "Concrete next step." },
    },
    required: ["classification", "severity", "description", "suggestedAction"],
  },
};

const SYSTEM =
  "You are a senior QA analyst reviewing test failures.\n\n" +
  "Given a failing scenario and its execution log, determine:\n" +
  "- What type of failure it is (bug / expected-failure / flaky / environment)\n" +
  "- Severity if it is a bug\n" +
  "- A clear technical description of the root cause\n" +
  "- The most useful next action\n\n" +
  "Be precise. Avoid vague language like 'something went wrong'.";

export async function classify(
  scenario: TestScenario,
  result: RunnerResult
): Promise<Finding> {
  const logText = result.stepLog
    .map((e) => `  ${e.tool}(${JSON.stringify(e.input)}) → ${e.result}`)
    .join("\n");

  const prompt =
    `Scenario: ${scenario.title}\n` +
    `Category: ${scenario.category} · Priority: ${scenario.priority}\n` +
    `Expected outcome: ${scenario.expected_outcome}\n\n` +
    `Execution log:\n${logText}\n\n` +
    `Runner summary:\n${result.summary}`;

  const response = await client.messages.create({
    model: "claude-sonnet-4-6",
    max_tokens: 1024,
    system: SYSTEM,
    tools: [CLASSIFY_TOOL],
    tool_choice: { type: "tool", name: "classify_failure" },
    messages: [{ role: "user", content: prompt }],
  });

  const toolBlock = response.content.find((b) => b.type === "tool_use");
  if (!toolBlock || toolBlock.type !== "tool_use") {
    throw new Error("Asserter did not return a tool_use block");
  }

  const inp = toolBlock.input as {
    classification: Finding["classification"];
    severity: Finding["severity"];
    description: string;
    suggestedAction: string;
  };

  const finding: Finding = {
    scenarioId: scenario.id,
    title: scenario.title,
    classification: inp.classification,
    severity: inp.severity,
    description: inp.description,
    suggestedAction: inp.suggestedAction,
  };

  console.log(
    `[Asserter:${scenario.id}] ${finding.classification.toUpperCase()} ` +
      `(${finding.severity}) — ${finding.description.slice(0, 80)}`
  );

  return finding;
}
