# Module 01 — Foundations: What is a Test Agent?

## The core loop

Traditional test automation is **scripted**: you write every step in order.  
An AI test agent is **goal-driven**: you describe what to test, the agent decides the steps.

```
You: "Test the login flow on example.com"

Agent loop:
  observe  →  decide  →  act  →  observe  →  decide  →  act  →  …  →  done
  (DOM)      (LLM)    (tool)    (result)    (LLM)    (tool)
```

The LLM is the reasoning engine. The browser tools (navigate, click, fill, assert) are its hands.

## Why this matters for testing

| Scripted test | Agent-driven test |
|---------------|-------------------|
| Breaks when selectors change | Finds elements by role/text, resilient to markup changes |
| You write every assertion | Agent decides what to verify based on the goal |
| One script = one scenario | One prompt = many possible paths explored |
| Maintenance burden grows with coverage | Agent adapts; prompt stays small |

## Anatomy of an agent

```
┌─────────────────────────────────────────────┐
│                   Agent                      │
│                                             │
│   system prompt  ←  defines agent persona  │
│   tool list      ←  what it can do         │
│   message loop   ←  observe/decide/act     │
└─────────────────────────────────────────────┘
         │ tool calls
         ▼
┌─────────────────────────────────────────────┐
│              Browser driver                  │
│   (Playwright / vibium / Selenium BiDi)     │
└─────────────────────────────────────────────┘
```

## Key vocabulary

- **Tool** — a function the LLM can call (navigate, click, assert_visible, …)
- **Tool use** — the model returns a `tool_use` block; your code executes it, returns the result
- **Stop reason** — `tool_use` means keep looping; `end_turn` means the agent is done
- **System prompt** — shapes the agent's behavior (tester persona, output format, strictness)
- **Orchestrator** — an agent that spawns and coordinates other agents (Module 05)

## What's next

Module 02 wires this up with a real browser using Playwright.
