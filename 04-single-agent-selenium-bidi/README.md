# Module 04 — Single-Agent Test Runner: Selenium WebDriver BiDi

## What's new in this module

The agent loop is still identical to Modules 02 and 03. Two things change:

1. **Driver**: Selenium 4 replaces Playwright/Vibium — same interface, different API calls
2. **Three new tools** that expose BiDi capabilities: `get_browser_logs`, `execute_script`, `intercept_network`

These extras let the agent do things the previous modules couldn't:
- Detect JavaScript errors on every page load
- Verify DOM state via JS evaluation when no accessible element exists
- Block network requests to test error-handling paths

## Why Selenium WebDriver BiDi

| Feature | Playwright | Vibium | Selenium BiDi |
|---------|-----------|--------|---------------|
| Chrome | ✅ | ✅ | ✅ |
| Firefox | ✅ | — | ✅ |
| Safari | limited | — | ✅ |
| Network intercept | ✅ | via MCP | ✅ CDP + BiDi |
| Console logs | ✅ | via MCP | ✅ |
| Real-time event stream | ✅ | ✅ | ✅ BiDi protocol |
| W3C standard | partial | — | ✅ |

Choose Selenium BiDi when you need to run the **same agent task across multiple browsers** as part of a cross-browser test matrix.

## What changes from Modules 02 & 03

### Python setup

```python
# Module 02/03
from playwright.sync_api import sync_playwright   # or vibium.browser
browser = p.chromium.launch()
page = browser.new_page()

# Module 04
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()))
```

### API comparison

| Action | Playwright | Vibium | Selenium |
|--------|-----------|--------|----------|
| Navigate | `page.goto(url)` | `page.go(url)` | `driver.get(url)` |
| Find (role+text) | `get_by_role(role, name=text)` | `page.find({role, text})` | XPath expression |
| Click | `locator.click()` | `el.click()` | `element.click()` |
| Fill | `locator.fill(value)` | `el.fill(value)` | `element.send_keys(value)` |
| Text | `locator.inner_text()` | `el.inner_text()` | `element.text` |
| Title | `page.title()` | `page.title()` | `driver.title` |
| URL | `page.url` | `page.url` | `driver.current_url` |
| Screenshot | `page.screenshot()` | `page.capture.screenshot()` | `driver.save_screenshot()` |

### The XPath tradeoff

Selenium has no built-in role locator (unlike Playwright and Vibium). `tools.py` maps ARIA roles to XPath — for example:

```python
# role="button", text="Delete" becomes:
//button[contains(normalize-space(), 'Delete')]
| //*[@role='button'][contains(normalize-space(), 'Delete')]
```

This is less ergonomic than `get_by_role()` but works across all browsers and is worth understanding.

### Cross-browser in one command

```bash
# Chrome (default)
python run.py

# Firefox — same task, same agent, different browser
python run.py firefox
```

TypeScript:
```bash
npm start               # Chrome
npm run start:firefox   # Firefox
```

## BiDi-specific tools

### `get_browser_logs`
Retrieves the last 10 browser console entries. The system prompt instructs the agent to call this after every navigation, so JS errors surface as FAIL before assertions even run.

```
-> get_browser_logs({})
   [WARNING] https://demo.playwright.dev/todomvc 1:1 "Slow network detected"
   [SEVERE]  Uncaught ReferenceError: foo is not defined
```

### `execute_script`
Evaluates any JavaScript expression and returns the result. Useful when the DOM state you need to verify has no accessible element.

```
-> execute_script({"expression": "document.querySelectorAll('.todo-list li').length"})
   3
```

### `intercept_network`
Blocks requests matching a URL pattern (Chrome/Edge only, via CDP). Use to test how the app handles failed API calls.

```
-> intercept_network({"url_pattern": "*/api/todos*"})
   Network intercept active — blocking: */api/todos*
```

## Files

```
python/
├── requirements.txt
├── tools.py      ← Selenium 4 wrappers + XPath helpers + 3 BiDi tools
├── agent.py      ← Chrome/Firefox driver setup; identical loop
└── run.py        ← entry point; pass 'firefox' as arg for cross-browser

typescript/
├── package.json  ← selenium-webdriver dependency
├── tsconfig.json
└── src/
    ├── tools.ts  ← TS equivalents; chrome.Options + firefox.Options
    ├── agent.ts  ← buildDriver() factory; identical loop
    └── index.ts  ← BROWSER env var selects Chrome or Firefox
```

## Setup — Python

```bash
pip install -r requirements.txt
cp ../../.env.example .env
python run.py           # Chrome
python run.py firefox   # Firefox
```

## Setup — TypeScript

```bash
npm install
cp ../../.env.example .env
npm start               # Chrome
npm run start:firefox   # Firefox
```

> **Note:** `webdriver-manager` (Python) and `selenium-webdriver` (Node) download the correct browser driver automatically. Chrome and Firefox must be installed on the machine.
