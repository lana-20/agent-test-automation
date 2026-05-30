import json
from datetime import datetime, timezone
from pathlib import Path
from models import TestReport

_SEVERITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3}
_STATUS = {True: "PASS", False: "FAIL"}


def console(report: TestReport) -> None:
    print("\n" + "=" * 60)
    print(f"[Reporter] RESULTS  {report.passed}/{report.total} passed")
    if report.findings:
        print(f"           {report.bugs} bug(s) found\n")
    else:
        print()

    for r in sorted(report.results, key=lambda x: x.scenario_id):
        print(f"  {_STATUS[r.passed]}  [{r.scenario_id}]  {r.title}")

    if report.findings:
        print("\nFindings:")
        findings = sorted(report.findings, key=lambda f: _SEVERITY_ORDER[f.severity])
        for f in findings:
            print(f"  [{f.severity.upper()}] {f.classification}  [{f.scenario_id}]  {f.title}")
            print(f"    {f.description[:120]}")
            print(f"    → {f.suggested_action[:100]}")


def write_markdown(report: TestReport, path: str = "report.md") -> None:
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [
        f"# Test Report — {ts}",
        "",
        f"**Spec:** {report.spec[:120]}",
        "",
        f"| Total | Passed | Failed | Bugs |",
        f"|-------|--------|--------|------|",
        f"| {report.total} | {report.passed} | {report.failed} | {report.bugs} |",
        "",
        "## Results",
        "",
    ]

    for r in sorted(report.results, key=lambda x: x.scenario_id):
        status = "✅" if r.passed else "❌"
        lines.append(f"### {status} [{r.scenario_id}] {r.title}")
        lines.append("")
        lines.append(r.summary)
        lines.append("")

    if report.findings:
        lines += ["## Findings", ""]
        findings = sorted(report.findings, key=lambda f: _SEVERITY_ORDER[f.severity])
        for f in findings:
            lines.append(f"### [{f.severity.upper()}] {f.title}")
            lines.append(f"- **Classification:** {f.classification}")
            lines.append(f"- **Scenario:** {f.scenario_id}")
            lines.append(f"- **Description:** {f.description}")
            lines.append(f"- **Next action:** {f.suggested_action}")
            lines.append("")

    out = Path(path)
    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"[Reporter] Markdown report written to {out.resolve()}")


def write_json(report: TestReport, path: str = "report.json") -> None:
    data = {
        "spec": report.spec,
        "summary": {
            "total": report.total,
            "passed": report.passed,
            "failed": report.failed,
            "bugs": report.bugs,
        },
        "results": [
            {
                "scenario_id": r.scenario_id,
                "title": r.title,
                "passed": r.passed,
                "summary": r.summary,
            }
            for r in report.results
        ],
        "findings": [
            {
                "scenario_id": f.scenario_id,
                "title": f.title,
                "classification": f.classification,
                "severity": f.severity,
                "description": f.description,
                "suggested_action": f.suggested_action,
            }
            for f in report.findings
        ],
    }
    out = Path(path)
    out.write_text(json.dumps(data, indent=2), encoding="utf-8")
    print(f"[Reporter] JSON report written to {out.resolve()}")
