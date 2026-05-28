# Module 03 — Approach B: Vibium via MCP (zero wrapper code)

The `python/` and `typescript/` folders show the **programmatic API** approach — you write tool wrappers, same as Module 02, just different API calls.

This folder shows the **MCP approach**: Vibium's MCP server exposes every browser action as a native MCP tool. No wrapper code. No `tools.py`. No `dispatch()`. Claude calls browser tools directly.

## How it works

```
Claude (model)  →  MCP client  →  vibium mcp  →  browser
```

When you configure the Vibium MCP server, Claude sees tools like:
- `browser_navigate` — navigate to a URL
- `browser_click` — click an element
- `browser_fill` — fill an input
- `browser_find` — find an element
- `browser_is_visible` — check visibility
- `browser_screenshot` — take a screenshot
- …85 tools total

You write no tool definitions. You write no dispatch logic. You describe a test task and Claude drives the browser.

## Setup — Claude Code

Add Vibium to `.claude/settings.json` in your project (or the global `~/.claude/settings.json`):

```json
{
  "mcpServers": {
    "vibium": {
      "command": "vibium",
      "args": ["mcp"]
    }
  }
}
```

Then in Claude Code, just type:

```
Go to https://demo.playwright.dev/todomvc and test the todo workflow:
add three todos, complete one, verify the filters work, delete one.
```

Claude uses the Vibium MCP tools directly — no code file needed.

## Setup — Claude Desktop

Add the same block to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "vibium": {
      "command": "vibium",
      "args": ["mcp"]
    }
  }
}
```

## Setup — Standalone Python (programmatic MCP)

If you want to drive the MCP server from a Python script (not Claude Code), use the Anthropic SDK's MCP support:

```python
import anthropic

client = anthropic.Anthropic()

# Point at the running Vibium MCP server
# vibium mcp --port 8080   (start the server first)

response = client.beta.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=4096,
    mcp_servers=[
        {
            "type": "url",
            "url": "http://localhost:8080/mcp",
            "name": "vibium",
        }
    ],
    messages=[{
        "role": "user",
        "content": "Go to https://demo.playwright.dev/todomvc and add a todo called 'Buy groceries', then verify it appears."
    }],
    betas=["mcp-client-2025-04-04"],
)

print(response.content[-1].text)
```

## Programmatic vs MCP — when to use each

| | Programmatic (python/ typescript/) | MCP |
|---|---|---|
| Setup | Install library, write tool wrappers | Install Vibium, add one config block |
| Code | tools.py + dispatch + agent loop | Zero (or 10-line MCP client) |
| Control | Full — you own the tool definitions | Limited to Vibium's built-in tools |
| CI/CD | Easy — plain Python/TS script | Requires MCP server process |
| Custom tools | Add any tool you need | Fixed to Vibium's 85 tools |
| Best for | Extending with domain-specific tools | Rapid prototyping, Claude Code sessions |
