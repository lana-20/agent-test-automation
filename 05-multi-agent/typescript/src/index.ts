import * as dotenv from "dotenv";
import { plan } from "./orchestrator";
import { runScenario } from "./runner";
import { buildReport } from "./models";

dotenv.config();

const FEATURE = `
Test the TodoMVC application at https://demo.playwright.dev/todomvc

Cover these independent scenarios:
1. Adding and verifying multiple todos
2. Marking a todo as complete and checking the Completed filter
3. Deleting a todo and verifying the count drops
4. Using the Active filter to show only incomplete todos
5. Clearing all completed todos at once
`;

const headless = process.argv.includes("--headless");

async function main() {
  const scenarios = await plan(FEATURE);

  console.log(`\nRunning ${scenarios.length} scenario(s) in parallel...\n` + "=".repeat(60));

  const results = await Promise.all(
    scenarios.map((s) => runScenario(s, headless))
  );

  results.sort((a, b) => a.scenarioId.localeCompare(b.scenarioId));
  const report = buildReport(results);

  console.log("\n" + "=".repeat(60));
  console.log(`RESULTS  ${report.passed}/${report.total} passed\n`);
  for (const r of report.scenarios) {
    console.log(`  [${r.scenarioId}] ${r.passed ? "PASS" : "FAIL"}  ${r.title}`);
  }

  if (report.failed > 0) process.exit(1);
}

main().catch(console.error);
