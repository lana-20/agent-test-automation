---
name: agent-test-automation
description: Build and publish the "Agent-Driven Test Automation" video course — scaffold modules, write Python + TypeScript + Vibium implementations, update the DLB landing page, commit to GitHub, and deploy. Use when asked to add a module, update the course, or work on anything in the agent-test-automation repo.
---

# Agent-Driven Test Automation — Course Build

Build and maintain a progressive video course on AI-powered test agents. Published on YouTube, Udemy, and `daisyladybug.com/courses/agent-test-automation/`.

---

## Paths

| Resource | Location |
|----------|----------|
| Local repo | `~/agent-test-automation/` |
| GitHub | `https://github.com/lana-20/agent-test-automation` |
| Landing page (local) | `~/Desktop/daisyladybug/courses/agent-test-automation/index.html` |
| Landing page (live) | `https://www.daisyladybug.com/courses/agent-test-automation/` |
| Slides (local) | `~/agent-test-automation/slides/` (also copied to `~/Desktop/daisyladybug/courses/agent-test-automation/slides/`) |
| S3 bucket | `s3://www.daisyladybug.com/` |
| CloudFront (www) | `E1TT5YX87OV074` |
| CloudFront (root) | `E18R3J3JT1XIUC` |

**Always invalidate both distributions when deploying.**

---

## Course structure

| # | Module | Status | Key tech |
|---|--------|--------|----------|
| 01 | Foundations — concepts, vocabulary, observe→decide→act | ✅ | README only |
| 02 | Single-agent: Playwright | ✅ | Playwright sync/async API |
| 03 | Single-agent: Vibium | ✅ | Vibium programmatic + MCP |
| 04 | Single-agent: Selenium BiDi | ✅ | Selenium 4 + CDP, Chrome + Firefox |
| 05 | Multi-agent orchestration | ✅ | ThreadPoolExecutor / Promise.all + Vibium |
| 06 | Full framework: specialist agents | ✅ | Architect + Runner + Asserter + Reporter + Vibium |
| 07 | CI/CD integration | ✅ | GitHub Actions, step summaries |
| 08 | Evaluations | ✅ | Three-judge harness, regression, golden dataset |

---

## Core agent loop pattern (identical across modules 02–06)

```python
messages = [{"role": "user", "content": task}]
while True:
    response = client.messages.create(
        model="claude-sonnet-4-6", max_tokens=4096,
        system=SYSTEM_PROMPT, tools=TOOL_DEFINITIONS, messages=messages)
    messages.append({"role": "assistant", "content": response.content})
    tool_results = []
    for block in response.content:
        if block.type == "text": print(block.text)
        elif block.type == "tool_use":
            result = dispatch(block.name, block.input, page)
            tool_results.append({"type": "tool_result", "tool_use_id": block.id, "content": result})
    if tool_results:
        messages.append({"role": "user", "content": tool_results})
    if response.stop_reason == "end_turn":
        break
```

**The key teaching point of the entire course**: `TOOL_DEFINITIONS` and the agent loop are identical across all modules. Only `tools.py` changes — the implementation layer, not the loop.

---

## File pattern per module (02–04, single-agent)

```
python/
├── requirements.txt
├── tools.py        ← browser wrappers + TOOL_DEFINITIONS + dispatch()
├── agent.py        ← browser setup + agent loop + run()
└── run.py          ← entry point, task string, headless flag

typescript/
├── package.json
├── tsconfig.json
└── src/
    ├── tools.ts    ← TOOL_DEFINITIONS: Anthropic.Tool[] + async dispatch()
    ├── agent.ts    ← driver setup + run()
    └── index.ts    ← TASK constant + entry point
```

---

## Module-specific notes

### Module 02 — Playwright

- Python: `playwright.sync_api` — `page.get_by_role(role, name=text)`, `locator.wait_for(state="visible", timeout=5000)`
- TypeScript: `playwright` async — `page.getByRole(role as AriaRole, {name: text}).waitFor({state: "visible", timeout: 5000})`
- 11 tools: navigate, find_element, click, press, fill, get_text, assert_visible, assert_not_visible, get_page_title, get_current_url, screenshot
- Task: TodoMVC at `https://demo.playwright.dev/todomvc` — add 3 todos, mark, filter, delete, screenshot

### Module 03 — Vibium

- `from vibium import browser as vibium_browser` / `import { browser } from "vibium"`
- API diff: `page.go(url)`, `page.find({role, text})`, `el.click()`, `el.fill(value)`, `page.capture.screenshot({path})`
- Also covers MCP approach: `mcp_servers` in `client.beta.messages.create` — zero wrapper code
- Same TOOL_DEFINITIONS as Module 02 — only dispatch() differs

### Module 04 — Selenium BiDi

- XPath helper `_by_role_and_text()` maps ARIA roles to `//button[contains(normalize-space(),'text')] | //*[@role='button'][contains(normalize-space(),'text')]`
- 3 extra BiDi tools: `get_browser_logs` → `driver.get_log('browser')`, `execute_script` → `driver.execute_script(f"return {expression}")`, `intercept_network` → CDP `Network.setBlockedURLs`
- Chrome: `goog:loggingPrefs: {browser: ALL}` capability; Firefox: `webSocketUrl: True` capability + `remote.active-protocols: 3`
- Cross-browser: `python run.py` (Chrome) or `python run.py firefox`

### Module 05 — Multi-agent

```
models.py: TestScenario, RunnerResult, TestReport
orchestrator.py: tool_choice={"type":"tool","name":"create_test_plan"} → list[TestScenario]
runner.py: run_scenario(scenario, page) → RunnerResult  ← accepts Page, no browser lifecycle
run.py: one browser → N contexts → N pages → ThreadPoolExecutor(max_workers=2)
```

- `[scenario_id]` prefix on all console output — readable interleaved parallel output
- Orchestrator never touches a browser; runners never decide what to test
- **Vibium variant** (`05-multi-agent/vibium/`): one browser started in `run.py`, one `BrowserContext` per scenario (isolated cookies/storage), one page per context. `runner.py` accepts a `Page` — no `browser.start()`/`stop()` inside. Max 2 parallel workers to stay under the 30K TPM rate limit.

```python
# run.py — correct Vibium parallel pattern
bro = vibium_browser.start(headless=headless)
try:
    contexts = [bro.new_context() for _ in scenarios]
    pages = [ctx.new_page() for ctx in contexts]
    with ThreadPoolExecutor(max_workers=min(len(scenarios), 2)) as pool:
        futures = {pool.submit(run_scenario, s, p): s for s, p in zip(scenarios, pages)}
        for future in as_completed(futures):
            results.append(future.result())
finally:
    for ctx in contexts:
        ctx.close()
    bro.stop()
```

### Module 06 — Full framework (specialist agents)

```
models.py: TestScenario (+ priority/category/expected_outcome), RunnerResult, Finding, TestReport
agents/architect.py:  tool_choice → create_test_plan (richer schema with priority/category)
agents/runner.py:     identical loop to M02, passes priority+category+expected_outcome to task
agents/asserter.py:   tool_choice → classify_failure → Finding (classification/severity/description/suggested_action)
agents/reporter.py:   console() + write_markdown("report.md") + write_json("report.json")
orchestrator.py:      run high-priority first → stop early on high failures → asserter only on failures
```

- Two `tool_choice` boundaries: Architect + Asserter
- `if: always()` pattern for artifact upload (discussed in Module 07)
- Reporter writes `report.md` + `report.json` — persistent CI artifacts
- **Vibium variant** (`06-full-framework/vibium/`): only `tools.py` and `agents/runner.py` differ; all other files are identical copies. Same one-browser/N-contexts pattern as Module 05 Vibium. `orchestrator.py` owns the browser lifecycle; `agents/runner.py` accepts a `Page`.  High-priority and remaining batches each get their own contexts created sequentially before threading.

### Module 07 — CI/CD

```
.github/workflows/agents.yml:       push+PR → parallel python + typescript jobs → artifact upload + step summary
.github/workflows/agents-smoke.yml: workflow_dispatch → matrix across all single-agent modules
07-ci-cd/scripts/step-summary.py:   reads report.json → $GITHUB_STEP_SUMMARY markdown table
07-ci-cd/scripts/step-summary.js:   same, plain Node (used by workflow — no compile step needed)
```

- `playwright install chromium --with-deps` — required on Ubuntu runners
- `if: always()` on summary + upload steps — get the report even when the run fails
- `fail-fast: false` in smoke matrix — all jobs finish regardless of individual failures
- Cost awareness: `paths` filter to skip on docs-only changes

### Module 08 — Evaluations

```
08-evaluations/python/
├── requirements.txt          (anthropic, python-dotenv)
├── golden_dataset.json       ← 10 scenarios: id, task, expected_tools, expected_keywords, rubric
├── sim_tools.py              ← simulated dispatch: returns "[simulated: X executed]" strings
├── eval_runner.py            ← runs all 10 scenarios against sim_tools, writes current.json
├── judges/
│   ├── deterministic.py      ← keyword coverage check (fast, free)
│   ├── llm_judge.py          ← claude-haiku-4-5 rubric scoring (0–1 per dimension)
│   └── trajectory.py         ← tool sequence check + hallucination detection
├── regression.py             ← compares current.json vs baseline.json; --save-baseline flag
├── baseline.json             ← committed reference; update with --save-baseline after improvements
└── current.json              ← gitignored, generated each run
```

**Three judges:**
- **Deterministic**: checks `expected_keywords` appear in the agent's final text — fast, no API cost
- **LLM (haiku)**: scores on 4 rubric dimensions (task_completion, step_clarity, error_handling, report_quality); average = `llm_avg_overall`
- **Trajectory**: checks `expected_tools` are all called, flags any tool call not in the allowed set as hallucination

**current.json schema** (written by eval_runner.py after each run):
```json
{
  "det_pass_rate": 0.3,
  "llm_avg_overall": 0.28,
  "traj_pass_rate": 0.5,
  "hallucination_rate": 0.0
}
```

**Simulation mode**: `sim_tools.py` returns `"[simulated: X executed]"` for every tool call — agent can't see real page content, so keyword coverage will be low. This is expected; trajectory judge shows whether the agent called valid tools.

**Run commands:**
```bash
cd 08-evaluations/python
python3 eval_runner.py              # run evals, write current.json
python3 regression.py               # compare current vs baseline
python3 regression.py --save-baseline  # promote current to baseline
```

**gitignore**: `current.json` and `eval_report.md` are gitignored (generated); `baseline.json` is committed.

---

## Vibium Python API — dispatch() pattern

All Vibium `tools.py` files (modules 03, 05, 06) follow this pattern:

```python
from vibium import Page

def _locate(page, selector, role, text):
    if selector:
        return page.find(selector)
    query = {}
    if role: query["role"] = role
    if text: query["text"] = text
    return page.find(query)

def dispatch(name, inputs, page):
    try:
        if name == "navigate":
            page.go(inputs["url"])
            return f"Navigated to {inputs['url']}"
        if name == "click":
            _locate(page, inputs.get("selector"), inputs.get("role"), inputs.get("text")).click()
            return "Clicked"
        if name == "hover":
            _locate(page, inputs.get("selector"), inputs.get("role"), inputs.get("text")).hover()
            return "Hovered"
        if name == "fill":
            el = page.find({"role": "textbox", "text": inputs["label"]}) or page.find({"placeholder": inputs["label"]})
            el.fill(inputs["value"])
            return f"Filled '{inputs['label']}' with '{inputs['value']}'"
        if name == "type":
            el = page.find(inputs["selector"])
            el.type(inputs["text"])
            return f"Typed '{inputs['text']}' into {inputs['selector']}"
        if name == "press":
            page.keyboard.press(inputs["key"])
            return f"Pressed: {inputs['key']}"
        if name == "assert_visible":
            el = _locate(page, inputs.get("selector"), inputs.get("role"), inputs.get("text"))
            return "VISIBLE" if el.is_visible() else f"FAIL: not visible"
        if name == "assert_not_visible":
            el = _locate(page, inputs.get("selector"), inputs.get("role"), inputs.get("text"))
            return "HIDDEN" if not el.is_visible() else f"FAIL: still visible"
        if name == "get_text":
            return _locate(page, inputs.get("selector"), inputs.get("role"), inputs.get("text")).info.text
        if name == "get_title":
            return page.title()
        if name == "get_url":
            return page.url()
        if name == "screenshot":
            # page.screenshot() pipes raw PNG bytes over stdout, overflowing
            # asyncio's 64 KB readline buffer and corrupting the connection.
            # Short-circuit until vibium fixes its transport layer.
            return "FAIL: screenshot unavailable (vibium buffer limitation — skip and continue)"
        if name == "count_elements":
            return str(len(page.find_all(inputs["selector"])))
    except Exception as e:
        return f"FAIL: {e}"
```

Key Vibium API facts:
- `page.go(url)` not `page.navigate(url)`
- `page.url()` is a method call, not a property
- `el.info.text` for text content (not `.inner_text()`)
- `page.screenshot()` — **DO NOT CALL**: returns raw PNG bytes over stdout, overflows asyncio's 64 KB readline buffer, corrupts the entire browser connection. Short-circuit in dispatch() instead.
- `page.find({})` finds by dict query; `page.find("css")` finds by CSS string
- `page.find_all("css")` returns list for count
- `page.keyboard.press(key)` for keyboard input
- `el.type(text)` — types a full string into a focused element via simulated keystrokes; bypasses `el.fill()`'s editable/label check. Use for placeholder-only inputs (e.g. TodoMVC `.new-todo`). Follow with `press(Enter)` to submit.
- `el.fill(value)` — requires a `<label>` element; fails with "editable check failed" on placeholder-only inputs
- `bro.new_context()` → `BrowserContext` with `new_page()` and `close()` — use for test isolation
- `BrowserContext` has: `new_page`, `close`, `cookies`, `set_cookies`, `clear_cookies`, `storage`, `set_storage`, `clear_storage`

---

## Playwright Python tools.py — CSS selector dispatch pattern

TodoMVC `<li>` elements have no ARIA accessible name, so `get_by_role("listitem", name="text")` fails silently. All modules (M02–M06) support `selector` as the primary locator param, with role+text as fallback:

```python
from playwright.sync_api import TimeoutError as PlaywrightTimeout

def dispatch(name, inputs, page):
    if name == "click":
        sel, role, text = inputs.get("selector"), inputs.get("role"), inputs.get("text")
        loc = page.locator(sel) if sel else page.get_by_role(role, name=text)
        try:
            loc.first.click(timeout=5000)
            return f"Clicked selector={sel} role={role} text={text}"
        except PlaywrightTimeout:
            return f"TIMEOUT: element not found or not clickable"

    if name == "hover":
        sel, role, text = inputs.get("selector"), inputs.get("role"), inputs.get("text")
        loc = page.locator(sel) if sel else page.get_by_role(role, name=text)
        try:
            loc.first.hover(timeout=5000)
            return f"Hovered"
        except PlaywrightTimeout:
            return f"TIMEOUT: element not found"

    if name == "assert_visible":
        sel, role, text = inputs.get("selector"), inputs.get("role"), inputs.get("text")
        loc = page.locator(sel) if sel else page.get_by_role(role, name=text)
        try:
            loc.first.wait_for(state="visible", timeout=5000)
            return f"VISIBLE"
        except PlaywrightTimeout:
            return f"FAIL: not visible"

    if name == "get_text":
        sel, role, text = inputs.get("selector"), inputs.get("role"), inputs.get("text")
        loc = page.locator(sel) if sel else page.get_by_role(role, name=text)
        try:
            return loc.first.inner_text(timeout=5000)
        except PlaywrightTimeout:
            return f"TIMEOUT: element not found"
```

All tool calls must return error strings (not raise exceptions) so the agent can recover.

---

## Rate limiting

All runners use flat 60s sleep on `RateLimitError` (org limit ~30k tokens/min):

```python
def _api_call_with_retry(client, **kwargs):
    for attempt in range(4):
        try:
            return client.messages.create(**kwargs)
        except anthropic.RateLimitError:
            if attempt == 3:
                raise
            time.sleep(60)
```

**Do not** run modules 05 and 06 simultaneously — combined parallel runners will hit the rate limit.

**Vibium parallel workers cap**: 2 workers max (`max_workers=min(len(scenarios), 2)`) — 5 concurrent API calls easily bursts past the 30K TPM org limit.

---

## Tool definitions schema

Tool sets differ by module group:

**M02–M04 (single-agent) — 11 tools:**
```python
TOOL_DEFINITIONS = [
  { "name": "navigate",           "input_schema": { "url": str } },
  { "name": "find_element",       "input_schema": { "role"?: str, "text"?: str } },
  { "name": "click",              "input_schema": { "selector"?: str, "role"?: str, "text"?: str } },
  { "name": "press",              "input_schema": { "key": str, "selector"?: str } },
  { "name": "fill",               "input_schema": { "value": str, "label"?: str, "placeholder"?: str, "selector"?: str } },
  { "name": "get_text",           "input_schema": { "selector": str } },
  { "name": "assert_visible",     "input_schema": { "selector"?: str, "role"?: str, "text"?: str } },
  { "name": "assert_not_visible", "input_schema": { "selector"?: str, "text"?: str } },
  { "name": "get_page_title",     "input_schema": {} },
  { "name": "get_current_url",    "input_schema": {} },
  { "name": "screenshot",         "input_schema": { "filename": str } },
]
```
M04 adds 3 BiDi extras: `get_browser_logs`, `execute_script`, `intercept_network`.

**M05–M06 Playwright (multi-agent / full framework) — 12 tools:**
```python
TOOL_DEFINITIONS = [
  { "name": "navigate",           "input_schema": { "url": str } },
  { "name": "click",              "input_schema": { "selector"?: str, "role"?: str, "text"?: str } },
  { "name": "hover",              "input_schema": { "selector"?: str, "role"?: str, "text"?: str } },
  { "name": "fill",               "input_schema": { "label": str, "value": str } },
  { "name": "press",              "input_schema": { "key": str, "selector"?: str } },
  { "name": "assert_visible",     "input_schema": { "selector"?: str, "role"?: str, "text"?: str } },
  { "name": "assert_not_visible", "input_schema": { "selector"?: str, "role"?: str, "text"?: str } },
  { "name": "get_text",           "input_schema": { "selector"?: str, "role"?: str, "text"?: str } },
  { "name": "get_title",          "input_schema": {} },
  { "name": "get_url",            "input_schema": {} },
  { "name": "screenshot",         "input_schema": { "path": str } },
  { "name": "count_elements",     "input_schema": { "selector": str } },
]
```

**M05–M06 Vibium — 13 tools:** same as above plus `type` (`{ "selector": str, "text": str }`).

---

## "Build next module" workflow

When asked to build the next module:

1. Read the existing stub README in `XX-module-name/README.md` (always exists from initial scaffold)
2. Create subdirs: `python/`, `typescript/src/`, and for M06 also `python/agents/`, `typescript/src/agents/`
3. Write all Python files first, then TypeScript equivalents
4. Replace the stub README with the full module README
5. Update root `README.md`: change that module's status from `🚧` to `✅`
6. Update the landing page: change module card class `soon` → `available`, badge text `Coming soon` → `Available`, add `module-link` with GitHub URL, add `Slides →` secondary link pointing to `./slides/NN-name.html`
7. Update banner count if it changed
8. Commit to GitHub, push
9. Deploy landing page and slides:
   ```bash
   aws s3 cp ~/Desktop/daisyladybug/courses/agent-test-automation/index.html \
     s3://www.daisyladybug.com/courses/agent-test-automation/index.html \
     --content-type text/html
   aws s3 sync ~/Desktop/daisyladybug/courses/agent-test-automation/slides/ \
     s3://www.daisyladybug.com/courses/agent-test-automation/slides/
   ```
10. Invalidate **both** CloudFront distributions:
    ```bash
    aws cloudfront create-invalidation --distribution-id E1TT5YX87OV074 --paths "/courses/agent-test-automation/*"
    aws cloudfront create-invalidation --distribution-id E18R3J3JT1XIUC --paths "/courses/agent-test-automation/*"
    ```

---

## Landing page structure

File: `~/Desktop/daisyladybug/courses/agent-test-automation/index.html`

Uses DLB design system tokens (coral/mint/steel accents, dark navy bg). Key components:
- Banner: `<div class="banner">` — update module count when adding modules
- Module cards grid: `.modules-grid` → `.module-card.available` or `.module-card.soon`
- Each card: `.module-num`, `.module-title`, `.module-subtitle`, `.badge.available`/`.badge.soon`, `.module-desc`, `.tags`, `.module-links`
- Module card CSS: `.available` has `border-left-color: var(--coral)` and hover slide; `.soon` has `opacity: 0.72`
- Asset paths (two levels deep from site root): `../../favicon.png`, `../../ldb-logo.webp`, `../../vibewire/floral-banner.jpeg`
- Tag variants: `.tag.coral` (Python/TypeScript/Vibium-as-tool), `.tag.mint` (Vibium/MCP/Playwright-as-driver), `.tag` (plain)

Module links pattern (`.module-links` wrapper):
```html
<div class="module-links">
  <a href="./slides/05-multi-agent.html" class="module-link secondary">Slides →</a>
  <a href="https://github.com/.../vibium" target="_blank" rel="noopener" class="module-link secondary">Vibium →</a>
  <a href="https://github.com/..." target="_blank" rel="noopener" class="module-link">View code →</a>
</div>
```

To flip a card from soon → available:
```html
<div class="module-card soon"> → <div class="module-card available">
<span class="badge soon">Coming soon</span> → <span class="badge available">Available</span>
```

---

## .gitignore rules

```
# secrets
.env
.env.*
*.env
**/.env
**/.env.*

# eval generated outputs
08-evaluations/python/current.json
08-evaluations/python/eval_report.md

# test artifacts
06-full-framework/python/report.json
06-full-framework/python/report.md
06-full-framework/vibium/report.json
06-full-framework/vibium/report.md

# local working notes
bugs/
transcripts/

# OS
.DS_Store
```

**Never commit `transcripts/`, `bugs/`, or any file containing API keys.**

---

## GitHub repo config

- Homepage: `https://www.daisyladybug.com/courses/agent-test-automation/`
- Default branch: `main`
- Remote: `https://github.com/lana-20/agent-test-automation.git`
- `.env.example` at repo root (referenced in each module's setup section)

---

## Model and API

- Agent loops: `claude-sonnet-4-6`
- LLM judge (Module 08): `claude-haiku-4-5-20251001`

Structured output uses:
```python
tool_choice={"type": "tool", "name": "tool_name"}
```
Forces a single tool call — always valid JSON matching the schema, no parsing needed.

---

## Key design decisions (do not change without good reason)

- **Self-contained modules**: each module has its own `tools.py` and `requirements.txt`/`package.json` — no cross-module imports
- **TodoMVC as universal task**: all modules test the same app (`https://demo.playwright.dev/todomvc`) so students can run them side by side and observe identical agent behavior with different drivers
- **TypeScript uses `AriaRole` type**: `type AriaRole = Parameters<Page["getByRole"]>[0]` — preserves type safety without importing from playwright internals
- **Python parallelism = ThreadPoolExecutor**: Playwright's sync API is thread-safe but not asyncio-safe; never use `asyncio.gather` with sync Playwright
- **Vibium parallel model = one browser, N contexts**: per Jason Huggins (vibium creator), the correct pattern is one browser + one `BrowserContext` per test + one page per context — same as Playwright's multi-tab model. Never call `vibium_browser.start()` concurrently from multiple threads; that crashes all connections.
- **CSS selector preferred over ARIA — TodoMVC-specific**: ARIA locators (`getByRole`, `getByLabel`) are the *generally recommended* approach (Playwright docs, Testing Library, a11y-first testing) because they test what the user actually experiences and surface accessibility bugs. However, TodoMVC `<li>` todo items have no accessible name — `getByRole("listitem", { name: "text" })` matches on accessible name, not text content, so it silently returns nothing. CSS (`page.locator(".todo-list li")`) is reliable because it matches DOM structure regardless of ARIA. Rule: prefer ARIA for interactive widgets (`button`, `textbox`, `checkbox`) that always have accessible names; prefer CSS for structural elements (`li`, `div`, `span`) with text but no ARIA name. All system prompts say: "Prefer locating elements by CSS selector. Use role+text as fallback when no stable selector exists."
- **`first_word != "FAIL"` pass detection**: check only the first word of the agent's final text block — robust across different report phrasings
- **All tool dispatch returns strings, never raises**: agent can recover from any error by retrying with a different locator
- **`if: always()` in CI**: artifact upload and step summary must run even on failure — that's when you need them most
- **Vibium Modules 05/06 share non-browser files**: only `tools.py` and `agents/runner.py` differ; `models.py`, `orchestrator.py`, `run.py`, `architect.py`, `asserter.py`, `reporter.py` are identical copies
- **Vibium screenshot = never call vibium**: `page.screenshot()` overflows asyncio's 64 KB readline buffer — keep `screenshot` in `TOOL_DEFINITIONS` for documentation but short-circuit in `dispatch()` to return a soft FAIL string. Root cause: duplicate of [VibiumDev/vibium#110](https://github.com/VibiumDev/vibium/issues/110); fix ships in v26.5.31. Filed as #168 (closed). Bug docs at `bugs/vibium-bug-screenshot-buffer-overflow.md`.
- **`type` tool over `fill` for placeholder-only inputs**: TodoMVC's `.new-todo` input has no `<label>`, only a `placeholder`. `el.fill()` fails with "editable check failed". The fix is a `type` tool that calls `el.type(text)` directly — sends the full string as simulated keystrokes without any label or editability check. System prompt must say: "Use type(selector, text) to type into any input field. Do NOT use fill()."
