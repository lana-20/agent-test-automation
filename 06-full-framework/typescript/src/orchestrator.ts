import { plan } from "./agents/architect";
import { run } from "./agents/runner";
import { classify } from "./agents/asserter";
import { TestReport, buildReport } from "./models";

export async function execute(spec: string, headless = true): Promise<TestReport> {
  const scenarios = await plan(spec);

  const high = scenarios.filter((s) => s.priority === "high");
  const rest = scenarios.filter((s) => s.priority !== "high");

  console.log(`\n[Orchestrator] Running ${high.length} high-priority scenario(s) first...`);
  console.log("=".repeat(60));

  const highResults = await Promise.all(high.map((s) => run(s, headless)));

  const criticalFailures = highResults.filter((r) => !r.passed);
  let restResults: typeof highResults = [];

  if (criticalFailures.length > 0) {
    console.log(
      `\n[Orchestrator] ${criticalFailures.length} high-priority failure(s) — ` +
        "skipping remaining scenarios."
    );
  } else if (rest.length > 0) {
    console.log(`\n[Orchestrator] Running ${rest.length} remaining scenario(s)...`);
    restResults = await Promise.all(rest.map((s) => run(s, headless)));
  }

  const allResults = [...highResults, ...restResults];
  const failedResults = allResults.filter((r) => !r.passed);
  const scenarioMap = new Map(scenarios.map((s) => [s.id, s]));

  const findings = await Promise.all(
    failedResults.map((r) => {
      const scenario = scenarioMap.get(r.scenarioId)!;
      return classify(scenario, r);
    })
  );

  return buildReport(spec, allResults, findings);
}
