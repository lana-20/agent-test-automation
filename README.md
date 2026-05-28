# Agent-Driven Test Automation

A progressive course on building AI test agents with Playwright, Vibium, and Selenium WebDriver BiDi.

## Course structure

| Module | Topic | Status |
|--------|-------|--------|
| [01 — Foundations](01-foundations/) | What is a test agent? Core concepts. | ✅ |
| [02 — Playwright](02-single-agent-playwright/) | Single-agent runner: Python + TypeScript | ✅ |
| [03 — Vibium](03-single-agent-vibium/) | Single-agent runner via MCP | 🚧 |
| [04 — Selenium BiDi](04-single-agent-selenium-bidi/) | Single-agent runner with WebDriver BiDi | 🚧 |
| [05 — Multi-agent](05-multi-agent/) | Orchestrator + parallel runners | 🚧 |
| [06 — Full framework](06-full-framework/) | Specialist agents + reporter | 🚧 |

## Prerequisites

- Python 3.11+ or Node.js 20+
- An [Anthropic API key](https://console.anthropic.com/)
- `ANTHROPIC_API_KEY` set in your environment

## Quick start (Module 02 — Python)

```bash
cd 02-single-agent-playwright/python
pip install -r requirements.txt
playwright install chromium
python run.py
```

## Quick start (Module 02 — TypeScript)

```bash
cd 02-single-agent-playwright/typescript
npm install
npx playwright install chromium
npm start
```

## Published resources

- Course page: [daisyladybug.com/courses/agent-test-automation](https://daisyladybug.com/courses/agent-test-automation)
- YouTube playlist: coming soon
- Udemy: coming soon
