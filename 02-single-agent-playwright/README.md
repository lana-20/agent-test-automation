# Module 02 — Single-Agent Test Runner: Playwright

## What you'll build

A single AI agent that drives a Playwright browser to execute test tasks described in plain English.

## How it works

```
run.py / index.ts
      │
      ▼
  agent.run(task)          ← your test task as a string
      │
      │  loop until stop_reason == "end_turn"
      │
      ├─ client.messages.create(tools=TOOL_DEFINITIONS)
      │         │
      │         ▼ (model returns tool_use blocks)
      │
      ├─ dispatch(tool_name, inputs, page)
      │         │
      │         ▼
      │   Playwright API call  (navigate / click / fill / assert…)
      │         │
      │         ▼
      └─ append tool_result → next loop iteration
```

## Files

```
python/
├── requirements.txt
├── tools.py      ← Playwright wrappers + TOOL_DEFINITIONS + dispatch()
├── agent.py      ← Anthropic client + agent loop
└── run.py        ← entry point with example task

typescript/
├── package.json
├── tsconfig.json
└── src/
    ├── tools.ts  ← same as above, TypeScript
    ├── agent.ts  ← agent loop
    └── index.ts  ← entry point
```

## Setup — Python

```bash
pip install -r requirements.txt
playwright install chromium
cp ../../.env.example .env   # add your ANTHROPIC_API_KEY
python run.py
```

## Setup — TypeScript

```bash
npm install
npx playwright install chromium
cp ../../.env.example .env
npm start
```

## Key concepts in this module

### Tool definitions
The model needs to know what tools exist. Each definition has:
- `name` — matches your dispatch switch
- `description` — tells the model WHEN to use it (write this carefully)
- `input_schema` — JSON Schema describing the parameters

### The agent loop
```
while stop_reason != "end_turn":
    response = create(messages)
    if tool_use in response:
        execute tool → append tool_result
    else:
        done
```

### Grounding assertions in the DOM
The agent uses `assert_visible` and `assert_not_visible` as test checkpoints. If Playwright raises a timeout, it comes back as `FAIL: ...` in the tool result — the model sees it and stops, reports failure.

## Extending this

- Add a `press_key` tool for keyboard interactions
- Add a `wait_for_text` tool for dynamic content
- Pass a different `TASK` string to test any scenario on any site
