#!/usr/bin/env ts-node
// Read report.json and print a GitHub Actions step summary (Markdown).
import * as fs from "fs";

const path = process.argv[2] ?? "report.json";
const report = JSON.parse(fs.readFileSync(path, "utf-8"));
const s = report.summary;

const icon = s.failed === 0 ? "✅" : "❌";
const severityOrder: Record<string, number> = { critical: 0, high: 1, medium: 2, low: 3 };

const lines: string[] = [
  `## ${icon} Test Results`,
  "",
  "| Total | Passed | Failed | Bugs |",
  "|-------|--------|--------|------|",
  `| ${s.total} | ${s.passed} | ${s.failed} | ${s.bugs} |`,
  "",
  "### Scenarios",
  "",
  "| ID | Title | Result |",
  "|----|-------|--------|",
];

for (const r of [...report.results].sort((a: any, b: any) =>
  a.scenarioId.localeCompare(b.scenarioId)
)) {
  lines.push(`| ${r.scenarioId} | ${r.title} | ${r.passed ? "✅ PASS" : "❌ FAIL"} |`);
}

if (report.findings?.length) {
  lines.push(
    "",
    "### Findings",
    "",
    "| Severity | Classification | Scenario | Description |",
    "|----------|---------------|----------|-------------|"
  );
  const sorted = [...report.findings].sort(
    (a: any, b: any) => severityOrder[a.severity] - severityOrder[b.severity]
  );
  for (const f of sorted) {
    const desc = f.description.length > 80 ? f.description.slice(0, 80) + "…" : f.description;
    lines.push(`| ${f.severity.toUpperCase()} | ${f.classification} | ${f.scenarioId} | ${desc} |`);
  }
}

console.log(lines.join("\n"));
