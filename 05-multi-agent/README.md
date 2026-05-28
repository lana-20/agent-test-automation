# Module 05 — Multi-Agent Orchestration

> Status: 🚧 coming next

## The problem single agents hit

A single agent running a large test suite is sequential. If you have 20 scenarios, they run one after another. Errors in early scenarios can block later ones.

Multi-agent fixes this by running scenarios in parallel, each with its own browser context.

## Pattern: Orchestrator + parallel runners

```
Orchestrator agent
├── receives: "Test all flows on checkout.example.com"
├── produces: list of N independent test scenarios
└── spawns N Runner agents in parallel
    ├── Runner-1: login flow        → PASS
    ├── Runner-2: cart flow         → PASS
    ├── Runner-3: checkout flow     → FAIL (missing field validation)
    └── Runner-4: order history     → PASS

Orchestrator collects results → final report
```

Each runner is an instance of the Module 02/03/04 agent with its own browser context.

## Why separate contexts matter

```python
# Each runner gets an isolated browser context
# — separate cookies, storage, auth state
context = browser.new_context()
page = context.new_page()
```

## Architecture coming in this module

```
orchestrator.py
├── analyze_scope(url, spec)       → list[TestScenario]
├── run_parallel(scenarios)        → list[TestResult]
│       ├── ThreadPoolExecutor / asyncio.gather
│       └── each thread: run_test_agent(scenario)
└── aggregate_results(results)     → TestReport

agents/
├── runner.py    ← Module 02 agent, parameterized
└── reporter.py  ← formats findings, writes output
```

## Coming in this module

- Orchestrator that splits a test scope into independent scenarios
- Parallel execution with `asyncio.gather` (Python) / `Promise.all` (TS)
- Result aggregation and failure triage
- How to pass context between orchestrator and runner (auth tokens, shared state)
