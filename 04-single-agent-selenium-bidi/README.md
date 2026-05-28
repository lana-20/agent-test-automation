# Module 04 — Single-Agent Test Runner: Selenium WebDriver BiDi

> Status: 🚧 coming next

## Why Selenium WebDriver BiDi

WebDriver BiDi is the W3C-standardized bidirectional protocol — the successor to the classic WebDriver protocol. It gives Selenium:
- Real-time event streaming (no polling)
- Native CDP-equivalent capabilities across Chrome, Firefox, and Safari
- Low-level network interception, console capture, and script evaluation

This makes it the right choice when you need cross-browser coverage beyond Chromium.

## Architecture preview

```python
# Python — selenium 4.x with BiDi
from selenium import webdriver
from selenium.webdriver.common.bidi.cdp import CDP

options = webdriver.ChromeOptions()
driver = webdriver.Chrome(options=options)

async with driver.bidi_connection() as connection:
    # BiDi commands and events available here
```

## Tools planned for this module

| Tool | BiDi capability used |
|------|---------------------|
| `navigate` | `browsingContext.navigate` |
| `click` | `script.callFunction` on element |
| `intercept_request` | `network.addIntercept` |
| `listen_console` | `log.entryAdded` event |
| `assert_visible` | `script.evaluate` + visibility check |

## Coming in this module

- BiDi session setup for Chrome and Firefox
- Agent tool definitions using Selenium 4 BiDi API
- Network interception as a test tool (stub responses, capture requests)
- When BiDi gives you something Playwright can't
