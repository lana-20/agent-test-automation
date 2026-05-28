# Module 06 — Full Framework: Specialist Agents

> Status: 🚧 coming next

## Specialist vs. generalist agents

In Module 05, every runner is the same agent doing everything. A specialist architecture assigns different agents to what they're best at.

```
Test Architect agent
│   reads: spec / URL / user story
│   produces: test plan (scenarios, priorities, coverage areas)
│
├── Runner agents (parallel, from Module 05)
│   each: executes one scenario, returns pass/fail + evidence
│
├── Assertion agent
│   reads: raw runner output
│   produces: structured findings (bug vs. expected, severity)
│
└── Reporter agent
    reads: structured findings
    produces: Markdown report / JSON / GitHub issue body
```

## Why specialists win at scale

| Concern | Generalist | Specialist |
|---------|------------|------------|
| Prompt size | Grows with all capabilities | Focused, small |
| Reasoning quality | Diluted across roles | Deep in one role |
| Reusability | Monolithic | Mix and match |
| Debugging | Hard to isolate failures | Clear responsibility |

## Full framework structure (coming)

```
06-full-framework/
├── python/
│   ├── agents/
│   │   ├── architect.py   ← generates test plan from spec
│   │   ├── runner.py      ← executes scenario (Module 02 core)
│   │   ├── asserter.py    ← evaluates results, classifies failures
│   │   └── reporter.py    ← formats final output
│   ├── orchestrator.py    ← wires specialists together
│   ├── models.py          ← shared data classes (TestPlan, Result, Finding)
│   └── run.py
└── typescript/
    └── src/
        ├── agents/
        ├── orchestrator.ts
        ├── models.ts
        └── index.ts
```

## Coming in this module

- Structured outputs (JSON mode) for agent-to-agent communication
- Shared data models passed between specialists
- How to handle failures in the pipeline (retry, escalate, skip)
- Exporting results to files, GitHub issues, or a test management system
