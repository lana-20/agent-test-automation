import Anthropic from "@anthropic-ai/sdk";
import * as fs from "fs";
import * as path from "path";
import { judgeDeterministic, judgeLLM, judgeTrajectory } from "./judges";

interface Scenario {
  id: string;
  site: string;
  task: string;
  expected_keywords: string[];
  expected_tools: string[];
  module: string;
  severity: string;
}

const GOLDEN_PATH = path.join(__dirname, "../python/golden.json");
const REPORT_PATH = path.join(__dirname, "eval_report.md");
const MAX_TURNS = 8;

const TOOLS: Anthropic.Tool[] = [
  { name: "navigate", description: "Navigate to a URL", input_schema: { type: "object", properties: { url: { type: "string" } }, required: ["url"] } },
  { name: "click", description: "Click an element", input_schema: { type: "object", properties: { selector: { type: "string" } }, required: ["selector"] } },
  { name: "fill", description: "Fill an input", input_schema: { type: "object", properties: { selector: { type: "string" }, value: { type: "string" } }, required: ["selector", "value"] } },
  { name: "find", description: "Find an element", input_schema: { type: "object", properties: { selector: { type: "string" } }, required: ["selector"] } },
  { name: "get_text", description: "Get element text", input_schema: { type: "object", properties: { selector: { type: "string" } }, required: ["selector"] } },
  { name: "count", description: "Count elements", input_schema: { type: "object", properties: { selector: { type: "string" } }, required: ["selector"] } },
  { name: "select", description: "Select dropdown option", input_schema: { type: "object", properties: { selector: { type: "string" }, value: { type: "string" } }, required: ["selector", "value"] } },
  { name: "evaluate", description: "Run JavaScript", input_schema: { type: "object", properties: { script: { type: "string" } }, required: ["script"] } },
  { name: "dialog_accept", description: "Accept dialog", input_schema: { type: "object", properties: {}, required: [] } },
  { name: "dialog_dismiss", description: "Dismiss dialog", input_schema: { type: "object", properties: {}, required: [] } },
  { name: "screenshot", description: "Take screenshot", input_schema: { type: "object", properties: {}, required: [] } },
];

async function runScenario(
  client: Anthropic,
  scenario: Scenario
): Promise<{ finding: string; toolCalls: Array<{ name: string }> }> {
  const messages: Anthropic.MessageParam[] = [
    { role: "user", content: `URL: ${scenario.site}\nTask: ${scenario.task}` },
  ];
  const toolCalls: Array<{ name: string }> = [];
  let finding = "";

  for (let turn = 0; turn < MAX_TURNS; turn++) {
    const response = await client.messages.create({
      model: "claude-haiku-4-5-20251001",
      max_tokens: 1024,
      system: "You are a QA test agent. Navigate to the URL, test the page, and report findings as a paragraph.",
      tools: TOOLS,
      messages,
    });

    const textBlocks = response.content.filter((b) => b.type === "text");
    if (textBlocks.length) finding = (textBlocks[textBlocks.length - 1] as { text: string }).text;

    const toolUses = response.content.filter((b) => b.type === "tool_use") as Anthropic.ToolUseBlock[];
    if (response.stop_reason === "end_turn" || !toolUses.length) break;

    messages.push({ role: "assistant", content: response.content });
    toolUses.forEach((tu) => toolCalls.push({ name: tu.name }));

    messages.push({
      role: "user",
      content: toolUses.map((tu) => ({
        type: "tool_result" as const,
        tool_use_id: tu.id,
        content: `[simulated: ${tu.name} executed]`,
      })),
    });
  }

  return { finding, toolCalls };
}

async function main() {
  const scenarios: Scenario[] = JSON.parse(fs.readFileSync(GOLDEN_PATH, "utf-8"));
  const moduleFilter = process.argv[2];
  const filtered = moduleFilter ? scenarios.filter((s) => s.module === moduleFilter) : scenarios;

  console.log(`Running ${filtered.length} scenarios${moduleFilter ? ` for ${moduleFilter}` : ""}`);

  const client = new Anthropic({ apiKey: process.env.ANTHROPIC_API_KEY });
  const start = Date.now();

  const rows: string[] = [];
  let detPassed = 0, llmPassed = 0, trajPassed = 0;

  for (const sc of filtered) {
    console.log(`\n[${sc.id}] ${sc.site}`);
    const { finding, toolCalls } = await runScenario(client, sc);

    const d = judgeDeterministic(sc.id, finding, sc.expected_keywords);
    const l = await judgeLLM(client, sc.id, finding, sc.task);
    const t = judgeTrajectory(sc.id, toolCalls, sc.expected_tools);

    if (d.passed) detPassed++;
    if (l.passed) llmPassed++;
    if (t.passed) trajPassed++;

    const status = d.passed && l.passed && t.passed ? "PASS" : "FAIL";
    console.log(`  ${status} | det=${(d.score * 100).toFixed(0)}% llm=${l.overall.toFixed(2)} traj=${(t.coverage * 100).toFixed(0)}%`);

    rows.push(`| ${sc.id} | ${sc.site.replace("https://", "")} | ${d.passed ? "✓" : "✗"} ${(d.score * 100).toFixed(0)}% | ${l.passed ? "✓" : "✗"} ${l.overall.toFixed(2)} | ${t.passed ? "✓" : "✗"} ${(t.coverage * 100).toFixed(0)}% |`);
  }

  const elapsed = ((Date.now() - start) / 1000).toFixed(1);
  const total = filtered.length;
  const report = [
    `# Eval Report — ${new Date().toISOString().slice(0, 16).replace("T", " ")}`,
    "",
    `**Scenarios:** ${total} | **Runtime:** ${elapsed}s`,
    "",
    "## Summary",
    "",
    "| Judge | Passed |",
    "|---|---|",
    `| Deterministic | ${detPassed}/${total} |`,
    `| LLM Judge | ${llmPassed}/${total} |`,
    `| Trajectory | ${trajPassed}/${total} |`,
    "",
    "## Per-Scenario Results",
    "",
    "| ID | Site | Det | LLM | Traj |",
    "|---|---|---|---|---|",
    ...rows,
  ].join("\n");

  fs.writeFileSync(REPORT_PATH, report);
  console.log(`\nReport written to ${REPORT_PATH}`);
}

main().catch(console.error);
