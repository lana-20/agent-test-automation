#!/usr/bin/env python3
"""Read report.json and print a GitHub Actions step summary (Markdown)."""
import json
import sys

path = sys.argv[1] if len(sys.argv) > 1 else "report.json"

with open(path) as f:
    report = json.load(f)

summary = report["summary"]
icon = "✅" if summary["failed"] == 0 else "❌"

lines = [
    f"## {icon} Test Results",
    "",
    f"| Total | Passed | Failed | Bugs |",
    f"|-------|--------|--------|------|",
    f"| {summary['total']} | {summary['passed']} | {summary['failed']} | {summary['bugs']} |",
    "",
    "### Scenarios",
    "",
    "| ID | Title | Result |",
    "|----|-------|--------|",
]

for r in sorted(report["results"], key=lambda x: x["scenarioId"]):
    status = "✅ PASS" if r["passed"] else "❌ FAIL"
    lines.append(f"| {r['scenarioId']} | {r['title']} | {status} |")

if report["findings"]:
    severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    lines += [
        "",
        "### Findings",
        "",
        "| Severity | Classification | Scenario | Description |",
        "|----------|---------------|----------|-------------|",
    ]
    findings = sorted(report["findings"], key=lambda f: severity_order[f["severity"]])
    for f in findings:
        desc = f["description"][:80] + ("…" if len(f["description"]) > 80 else "")
        lines.append(
            f"| {f['severity'].upper()} | {f['classification']} | {f['scenarioId']} | {desc} |"
        )

print("\n".join(lines))
