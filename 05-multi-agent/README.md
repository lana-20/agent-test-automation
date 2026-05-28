# Module 05 — Multi-Agent Test Orchestration

## What's new in this module

Modules 02–04 each used a single agent that executed one task from start to finish. This module splits that into two agents:

1. **Orchestrator** — reads a feature description and produces a structured test plan (a list of independent scenarios)
2. **Runner** — executes a single scenario in an isolated browser context

Multiple runners execute in parallel, each talking to the model independently.

## Architecture

```
run.py / index.ts
│
├── orchestrator  ←  feature description → test plan (structured JSON via tool_choice)
│
└── parallel dispatch
    ├── runner [TC-01] → isolated browser → RunnerResult
    ├── runner [TC-02] → isolated browser → RunnerResult
    ├── runner [TC-03] → isolated browser → RunnerResult
    └── ...
         ↓
     TestReport (aggregated PASS / FAIL)
```

## Why two agents instead of one

A single agent serialises every step. Two agents let you:

| Concern | Agent |
|---------|-------|
| Test planning (what to test) | Orchestrator |
| Test execution (how to test) | Runner × N |

Separating planning from execution makes each agent smaller and easier to reason about. The orchestrator never touches a browser; the runner never decides what to test.

## Structured output from the orchestrator

The orchestrator uses `tool_choice` to force a specific tool call instead of asking the model to output JSON in free text:

```python
response = client.messages.create(
    tools=[PLAN_TOOL],
    tool_choice={"type": "tool", "name": "create_test_plan"},
    ...
)
tool_block = next(b for b in response.content if b.type == "tool_use")
scenarios = tool_block.input["scenarios"]
```

Because the schema is enforced by the API, no regex or JSON parsing is needed — the output is always valid.

## Parallel execution

### Python — `ThreadPoolExecutor`

Playwright's sync API is not safe to call from multiple asyncio tasks, but it is thread-safe. `ThreadPoolExecutor` launches one thread per scenario, each with its own `sync_playwright()` context:

```python
with ThreadPoolExecutor(max_workers=len(scenarios)) as pool:
    futures = {pool.submit(run_scenario, s, headless): s for s in scenarios}
    for future in as_completed(futures):
        results.append(future.result())
```

### TypeScript — `Promise.all`

Playwright's async API works naturally with `Promise.all`:

```typescript
const results = await Promise.all(
  scenarios.map((s) => runScenario(s, headless))
);
```

Each call to `runScenario` creates its own `chromium.launch()` instance, so there is no shared state.

## Isolation

Every runner gets its own browser instance (`p.chromium.launch()` or `chromium.launch()`). Scenarios can run in any order and cannot interfere with each other — one scenario's cookies, local-storage, or navigation state never affects another.

## Console output

Each runner prefixes its lines with `[scenario-id]` so you can follow interleaved parallel output:

```
[TC-01]   -> navigate: Navigated to https://demo.playwright.dev/todomvc
[TC-03]   -> navigate: Navigated to https://demo.playwright.dev/todomvc
[TC-02]   -> navigate: Navigated to https://demo.playwright.dev/todomvc
[TC-01]   -> fill: Filled 'What needs to be done?' with 'Buy groceries'
...
```

## Files

```
python/
├── requirements.txt
├── models.py       ← TestScenario, RunnerResult, TestReport dataclasses
├── tools.py        ← Playwright core tools (self-contained)
├── orchestrator.py ← feature → structured test plan via tool_choice
├── runner.py       ← single scenario runner (one browser per call)
└── run.py          ← entry point: plan → parallel → report

typescript/
├── package.json
├── tsconfig.json
└── src/
    ├── models.ts
    ├── tools.ts
    ├── orchestrator.ts
    ├── runner.ts
    └── index.ts
```

## Setup — Python

```bash
cd 05-multi-agent/python
pip install -r requirements.txt
playwright install chromium
cp ../../.env.example .env
python run.py             # headed
python run.py --headless  # headless
```

## Setup — TypeScript

```bash
cd 05-multi-agent/typescript
npm install
npx playwright install chromium
cp ../../.env.example .env
npm start                  # headed
npm run start:headless     # headless
```

## What the report looks like

```
Orchestrator generated 5 scenario(s):
  [TC-01] Add and verify multiple todos  (4 steps)
  [TC-02] Mark todo complete, check Completed filter  (5 steps)
  [TC-03] Delete a todo, verify count drops  (4 steps)
  [TC-04] Active filter shows only incomplete todos  (5 steps)
  [TC-05] Clear all completed todos  (4 steps)

Running 5 scenario(s) in parallel...
============================================================
[TC-01] Navigated to https://demo.playwright.dev/todomvc
[TC-03] Navigated to https://demo.playwright.dev/todomvc
...

============================================================
RESULTS  5/5 passed

  [TC-01] PASS  Add and verify multiple todos
  [TC-02] PASS  Mark todo complete, check Completed filter
  [TC-03] PASS  Delete a todo, verify count drops
  [TC-04] PASS  Active filter shows only incomplete todos
  [TC-05] PASS  Clear all completed todos
```
