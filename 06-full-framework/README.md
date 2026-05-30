# Module 06 — Full Framework: Specialist Agents

## What's new in this module

Module 05 used one type of agent (runner) for everything — planning was a one-off structured call, but all runners were identical. This module introduces **four specialist agents**, each owning a single responsibility, and a typed data model that acts as the API contract between them.

```
Architect  →  Runner × N  →  Asserter  →  Reporter
   plan          execute       classify      output
```

## The four specialists

| Agent | Input | Output | Uses tool_choice? |
|-------|-------|--------|-------------------|
| **Architect** | Feature spec | `list[TestScenario]` | Yes — `create_test_plan` |
| **Runner** | `TestScenario` | `RunnerResult` | No — free agent loop |
| **Asserter** | `RunnerResult` + scenario | `Finding` | Yes — `classify_failure` |
| **Reporter** | `TestReport` | console + `.md` + `.json` | No — pure formatting |

### Why specialist agents win at scale

| Concern | Generalist | Specialist |
|---------|------------|------------|
| System prompt | Describes all roles | Focused on one role |
| Context window | Full execution history | Only what this role needs |
| Reusability | Monolithic | Mix and match |
| Failure isolation | Hard to debug | Clear responsibility boundary |

## Shared data model

The models file is the API contract between specialists. Every agent reads and writes the same types:

```python
TestScenario       # Architect produces  → Runner consumes
    id, title, url, steps
    priority       # high / medium / low
    category       # smoke / regression / edge-case …
    expected_outcome

RunnerResult       # Runner produces     → Asserter consumes
    scenario_id, title, passed, summary, step_log

Finding            # Asserter produces   → Reporter consumes
    classification # bug / expected-failure / flaky / environment
    severity       # critical / high / medium / low
    description, suggested_action

TestReport         # Orchestrator builds → Reporter formats
    spec, results, findings
```

## Structured output at two points

Both the Architect and Asserter use `tool_choice` to force structured output:

```python
# Architect
response = client.messages.create(
    tools=[PLAN_TOOL],
    tool_choice={"type": "tool", "name": "create_test_plan"},
    ...
)

# Asserter — same pattern, different schema
response = client.messages.create(
    tools=[CLASSIFY_TOOL],
    tool_choice={"type": "tool", "name": "classify_failure"},
    ...
)
```

This pattern replaces fragile regex/JSON parsing with schema-validated output at the API boundary.

## Priority-aware execution

The orchestrator runs high-priority scenarios first and stops early if they fail:

```python
high = [s for s in scenarios if s.priority == "high"]
rest = [s for s in scenarios if s.priority != "high"]

# Run high-priority in parallel
high_results = run_parallel(high)

# Only continue if high-priority passed
if no_failures(high_results):
    rest_results = run_parallel(rest)
```

This mirrors how a real CI pipeline works: smoke tests gate regression tests.

## Asserter only runs on failures

The Asserter is not called for passing scenarios — only for failures. This keeps the pipeline efficient and focuses AI analysis where it adds value:

```python
failed = [r for r in results if not r.passed]
findings = [classify(scenario_map[r.scenario_id], r) for r in failed]
```

## Reporter writes files

Unlike previous modules that only printed to stdout, the Reporter writes persistent output:

- `report.md` — Markdown with per-scenario summaries and finding details
- `report.json` — machine-readable, suitable for CI artifact upload or test management ingestion

## Files

```
python/
├── requirements.txt
├── models.py           ← shared types: TestScenario, RunnerResult, Finding, TestReport
├── tools.py            ← Playwright core tools (self-contained)
├── agents/
│   ├── __init__.py
│   ├── architect.py    ← spec → structured test plan (tool_choice)
│   ├── runner.py       ← single scenario execution
│   ├── asserter.py     ← failure classification (tool_choice)
│   └── reporter.py     ← console + markdown + JSON output
├── orchestrator.py     ← priority-aware dispatch + pipeline wiring
└── run.py              ← entry point

typescript/
├── package.json
├── tsconfig.json
└── src/
    ├── models.ts
    ├── tools.ts
    ├── agents/
    │   ├── architect.ts
    │   ├── runner.ts
    │   ├── asserter.ts
    │   └── reporter.ts
    ├── orchestrator.ts
    └── index.ts

vibium/
├── requirements.txt
├── models.py           ← identical to python/
├── tools.py            ← Vibium browser tools (same interface, different driver)
├── agents/
│   ├── __init__.py
│   ├── architect.py    ← identical to python/ (no browser)
│   ├── runner.py       ← Vibium runner: vibium_browser.start() instead of sync_playwright()
│   ├── asserter.py     ← identical to python/ (no browser)
│   └── reporter.py     ← identical to python/ (no browser)
├── orchestrator.py     ← identical to python/
└── run.py              ← identical to python/
```

## Setup — Python

```bash
cd 06-full-framework/python
pip install -r requirements.txt
playwright install chromium
cp ../../.env.example .env
python run.py             # headed
python run.py --headless  # headless
```

## Setup — TypeScript

```bash
cd 06-full-framework/typescript
npm install
npx playwright install chromium
cp ../../.env.example .env
npm start                  # headed
npm run start:headless     # headless
```

## Setup — Vibium

```bash
cd 06-full-framework/vibium
pip install -r requirements.txt
cp ../../.env.example .env
python run.py             # headed
python run.py --headless  # headless
```

## What the output looks like

```
[Architect] Generated 5 scenario(s):
  [TC-01] [HIGH] Add and verify multiple todos  (smoke)
  [TC-02] [HIGH] Mark todo complete and verify filter  (smoke)
  [TC-03] [MEDIUM] Delete a todo, verify count  (regression)
  [TC-04] [MEDIUM] Active filter shows only incomplete todos  (regression)
  [TC-05] [LOW] Clear all completed todos at once  (edge-case)

[Orchestrator] Running 2 high-priority scenario(s) first...
[Runner:TC-01] ...
[Runner:TC-02] ...

[Orchestrator] Running 3 remaining scenario(s)...
[Runner:TC-03] ...
[Runner:TC-04] ...
[Runner:TC-05] ...

============================================================
[Reporter] RESULTS  5/5 passed

  PASS  [TC-01]  Add and verify multiple todos
  PASS  [TC-02]  Mark todo complete and verify filter
  PASS  [TC-03]  Delete a todo, verify count
  PASS  [TC-04]  Active filter shows only incomplete todos
  PASS  [TC-05]  Clear all completed todos at once

[Reporter] Markdown report written to report.md
[Reporter] JSON report written to report.json
```

If a scenario fails, the Asserter classifies it before the Reporter runs:

```
[Asserter:TC-03] BUG (high) — Delete button was not found after clicking the item...
...
Findings:
  [HIGH] bug  [TC-03]  Delete a todo, verify count
    Delete button did not appear on hover; item remained in the list after the
    attempted deletion. The app may require a hover state before the button renders.
    → File a bug report; add a hover step before the delete action.
```
