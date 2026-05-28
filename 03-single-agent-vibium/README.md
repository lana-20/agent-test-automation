# Module 03 — Single-Agent Test Runner: Vibium

## The core lesson

Compare `tools.py` in this module with `tools.py` in Module 02. **Everything else is identical** — `TOOL_DEFINITIONS`, `agent.py`, `run.py`. The agent loop doesn't know or care which browser driver is underneath. Only the tool implementations change.

This is what makes the agent pattern powerful: swap the driver, keep the intelligence.

## Two approaches

| Approach | Code required | Best for |
|----------|--------------|----------|
| **Programmatic** (`python/`, `typescript/`) | Tool wrappers + agent loop (same structure as M02) | CI/CD, custom tools, full control |
| **MCP** (`mcp/`) | Zero — one config block | Claude Code sessions, rapid prototyping |

## What changes from Module 02 (Playwright → Vibium)

### Python

```python
# Module 02 (Playwright)
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=headless)
    page = browser.new_page()
    # ...
    browser.close()

# Module 03 (Vibium)
from vibium import browser as vibium_browser

bro = vibium_browser.start(headless=headless)
page = bro.new_page()
# ...
bro.close()
```

### API comparison

| Action | Playwright | Vibium |
|--------|-----------|--------|
| Navigate | `page.goto(url)` | `page.go(url)` |
| Find by role+text | `page.get_by_role(role, name=text)` | `page.find({role, text})` |
| Click | `locator.click()` | `el.click()` |
| Fill | `locator.fill(value)` | `el.fill(value)` |
| Inner text | `locator.inner_text()` | `el.inner_text()` |
| Check visible | `locator.is_visible()` | `el.is_visible()` |
| Screenshot | `page.screenshot(path=p)` | `page.capture.screenshot(path=p)` |
| Page title | `page.title()` | `page.title()` |
| Current URL | `page.url` | `page.url` |

### TypeScript

```typescript
// Module 02 (Playwright)
import { chromium } from "playwright";
const browser = await chromium.launch({ headless });
const page = await browser.newPage();

// Module 03 (Vibium)
import { browser } from "vibium";
const bro = await browser.start({ headless });
const page = await bro.newPage();
```

## Files

```
python/
├── requirements.txt
├── tools.py      ← Vibium Python API wrappers (compare with M02)
├── agent.py      ← identical to Module 02
└── run.py        ← same task as Module 02

typescript/
├── package.json
├── tsconfig.json
└── src/
    ├── tools.ts  ← Vibium JS API wrappers (compare with M02)
    ├── agent.ts  ← identical to Module 02
    └── index.ts  ← same task as Module 02

mcp/
└── README.md     ← MCP approach: zero wrapper code
```

## Setup — Python

```bash
pip install -r requirements.txt
cp ../../.env.example .env   # add ANTHROPIC_API_KEY
python run.py
```

## Setup — TypeScript

```bash
npm install
cp ../../.env.example .env
npm start
```

## What to observe when running

Run the same task against Module 02 and Module 03 side by side. Notice:
- The agent asks the same questions, makes the same decisions
- The only difference is which API calls execute under the hood
- Both produce the same screenshots and test report

This confirms: **the intelligence is in the loop, not the driver**.
