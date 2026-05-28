# Module 03 — Single-Agent Test Runner: vibium

> Status: 🚧 coming next

## What's different from Module 02

vibium exposes its browser API directly as MCP tools — meaning the agent can call browser actions **without you writing wrapper code**. The tool definitions and dispatch layer are provided by the vibium MCP server.

## Architecture preview

```
agent  →  MCP client  →  vibium MCP server  →  browser
```

Instead of `dispatch(name, inputs, page)`, you configure the MCP server and Claude calls vibium tools natively.

## Tools available via vibium MCP

| Category | Tools |
|----------|-------|
| Navigation | `browser_navigate`, `browser_reload`, `browser_back` |
| Interaction | `browser_click`, `browser_fill`, `browser_type`, `browser_press` |
| Assertions | `browser_find`, `browser_is_visible`, `browser_wait_for_text` |
| Capture | `browser_screenshot`, `browser_get_text`, `browser_get_html` |

## Coming in this module

- MCP server setup
- How to use vibium tools vs. writing your own wrappers
- Side-by-side comparison with the Playwright agent from Module 02
- When to choose each approach
