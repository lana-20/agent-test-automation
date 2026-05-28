# Module 03 — Single-Agent Test Runner: Vibium

> Status: 🚧 coming next

## What's different from Module 02

Vibium exposes its browser API directly as MCP tools — meaning the agent can call browser actions **without you writing wrapper code**. The tool definitions and dispatch layer are provided by the Vibium MCP server.

## Architecture preview

```
agent  →  MCP client  →  Vibium MCP server  →  browser
```

Instead of `dispatch(name, inputs, page)`, you configure the MCP server and Claude calls Vibium tools natively.

## Tools available via Vibium MCP

| Category | Tools |
|----------|-------|
| Navigation | `browser_navigate`, `browser_reload`, `browser_back` |
| Interaction | `browser_click`, `browser_fill`, `browser_type`, `browser_press` |
| Assertions | `browser_find`, `browser_is_visible`, `browser_wait_for_text` |
| Capture | `browser_screenshot`, `browser_get_text`, `browser_get_html` |

## Coming in this module

- MCP server setup
- How to use Vibium tools vs. writing your own wrappers
- Side-by-side comparison with the Playwright agent from Module 02
- When to choose each approach
