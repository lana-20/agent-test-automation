import * as fs from "fs";
import { TestReport, Finding } from "../models";

const SEVERITY_ORDER: Record<string, number> = {
  critical: 0, high: 1, medium: 2, low: 3,
};

function sortFindings(findings: Finding[]): Finding[] {
  return [...findings].sort((a, b) => SEVERITY_ORDER[a.severity] - SEVERITY_ORDER[b.severity]);
}

export function console_(report: TestReport): void {
  console.log("\n" + "=".repeat(60));
  console.log(`[Reporter] RESULTS  ${report.passed}/${report.total} passed`);
  if (report.findings.length) {
    console.log(`           ${report.bugs} bug(s) found\n`);
  } else {
    console.log();
  }

  for (const r of [...report.results].sort((a, b) => a.scenarioId.localeCompare(b.scenarioId))) {
    console.log(`  ${r.passed ? "PASS" : "FAIL"}  [${r.scenarioId}]  ${r.title}`);
  }

  if (report.findings.length) {
    console.log("\nFindings:");
    for (const f of sortFindings(report.findings)) {
      console.log(`  [${f.severity.toUpperCase()}] ${f.classification}  [${f.scenarioId}]  ${f.title}`);
      console.log(`    ${f.description.slice(0, 120)}`);
      console.log(`    → ${f.suggestedAction.slice(0, 100)}`);
    }
  }
}

export function writeMarkdown(report: TestReport, path = "report.md"): void {
  const ts = new Date().toISOString().replace("T", " ").slice(0, 16) + " UTC";
  const lines: string[] = [
    `# Test Report — ${ts}`,
    "",
    `**Spec:** ${report.spec.slice(0, 120)}`,
    "",
    "| Total | Passed | Failed | Bugs |",
    "|-------|--------|--------|------|",
    `| ${report.total} | ${report.passed} | ${report.failed} | ${report.bugs} |`,
    "",
    "## Results",
    "",
  ];

  for (const r of [...report.results].sort((a, b) => a.scenarioId.localeCompare(b.scenarioId))) {
    lines.push(`### ${r.passed ? "✅" : "❌"} [${r.scenarioId}] ${r.title}`);
    lines.push("", r.summary, "");
  }

  if (report.findings.length) {
    lines.push("## Findings", "");
    for (const f of sortFindings(report.findings)) {
      lines.push(`### [${f.severity.toUpperCase()}] ${f.title}`);
      lines.push(
        `- **Classification:** ${f.classification}`,
        `- **Scenario:** ${f.scenarioId}`,
        `- **Description:** ${f.description}`,
        `- **Next action:** ${f.suggestedAction}`,
        ""
      );
    }
  }

  fs.writeFileSync(path, lines.join("\n"), "utf-8");
  console.log(`[Reporter] Markdown report written to ${path}`);
}

export function writeJson(report: TestReport, path = "report.json"): void {
  const data = {
    spec: report.spec,
    summary: {
      total: report.total,
      passed: report.passed,
      failed: report.failed,
      bugs: report.bugs,
    },
    results: report.results.map((r) => ({
      scenarioId: r.scenarioId,
      title: r.title,
      passed: r.passed,
      summary: r.summary,
    })),
    findings: report.findings.map((f) => ({
      scenarioId: f.scenarioId,
      title: f.title,
      classification: f.classification,
      severity: f.severity,
      description: f.description,
      suggestedAction: f.suggestedAction,
    })),
  };
  fs.writeFileSync(path, JSON.stringify(data, null, 2), "utf-8");
  console.log(`[Reporter] JSON report written to ${path}`);
}
