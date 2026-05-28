# Module 07 — CI/CD Integration

## What's new in this module

The framework runs locally. Now it runs in GitHub Actions — headless, on every push and pull request, with reports uploaded as artifacts and results rendered in the Actions UI.

Two things make CI different from local:
1. **No display** — the browser must run headless
2. **No `.env` file** — the API key must come from a GitHub secret

Both are already solved: every entry point accepts `--headless`, and the workflow passes `ANTHROPIC_API_KEY` from `secrets`.

## GitHub Actions workflows

```
.github/workflows/
├── agents.yml         ← runs on push + PR (Python + TypeScript jobs in parallel)
└── agents-smoke.yml   ← manual dispatch; matrix across all single-agent modules
```

### `agents.yml` — main workflow

Triggers on every push to `main` and every PR targeting `main`. Runs the Module 06 full framework in two parallel jobs.

```
push / pull_request
        │
        ├── python job
        │     install → playwright install → run.py --headless → step summary → upload
        │
        └── typescript job
              install → playwright install → npm run start:headless → step summary → upload
```

Each job:
- Caches pip / npm for faster runs
- Uploads `report.md` + `report.json` as artifacts with `if: always()` — artifacts are preserved even when the job fails, so you can inspect the failure report
- Writes a step summary (see below)

### `agents-smoke.yml` — matrix smoke run

A `workflow_dispatch`-only workflow (manual trigger). Uses a matrix strategy to run the three single-agent implementations from Modules 02–04 in parallel:

```yaml
strategy:
  fail-fast: false
  matrix:
    include:
      - name: Playwright (Python)   dir: 02-...
      - name: Playwright (TypeScript) dir: 02-...
      - name: Vibium (Python)       dir: 03-...
      - name: Selenium BiDi Chrome  dir: 04-...
```

`fail-fast: false` keeps all jobs running even if one fails — you get a full picture of what broke, not just the first failure.

## Step summary

GitHub Actions renders a job summary in the Actions UI. The step-summary scripts read `report.json` and write Markdown tables directly to `$GITHUB_STEP_SUMMARY`:

```yaml
- name: Write step summary
  if: always()
  run: python ../../07-ci-cd/scripts/step-summary.py report.json >> $GITHUB_STEP_SUMMARY
```

What it looks like in the Actions UI:

```
## ✅ Test Results

| Total | Passed | Failed | Bugs |
|-------|--------|--------|------|
| 5     | 5      | 0      | 0    |

### Scenarios

| ID    | Title                              | Result  |
|-------|------------------------------------|---------|
| TC-01 | Add and verify multiple todos      | ✅ PASS |
| TC-02 | Mark todo complete, check filter   | ✅ PASS |
| TC-03 | Delete a todo, verify count        | ✅ PASS |
| TC-04 | Active filter shows incomplete     | ✅ PASS |
| TC-05 | Clear all completed todos          | ✅ PASS |
```

If failures exist, a Findings table appears below, sorted by severity.

## Setup

### 1. Add the API key secret

In your GitHub repo: **Settings → Secrets and variables → Actions → New repository secret**

- Name: `ANTHROPIC_API_KEY`
- Value: your Anthropic API key

### 2. Protect the main branch (optional but recommended)

**Settings → Branches → Add branch ruleset**
- Apply to: `main`
- Required status checks: `python (Module 06)`, `typescript (Module 06)`

PRs can no longer merge if the agent tests fail.

### 3. Commit a lock file

The TypeScript job uses `npm install` but benefits from a lock file for reproducible builds:

```bash
cd 06-full-framework/typescript
npm install          # generates package-lock.json
git add package-lock.json
git commit -m "add lock file for CI"
```

## Files

```
.github/
└── workflows/
    ├── agents.yml          ← main CI (push + PR)
    └── agents-smoke.yml    ← manual matrix smoke run

07-ci-cd/
└── scripts/
    ├── step-summary.py     ← reads report.json → $GITHUB_STEP_SUMMARY (Python)
    ├── step-summary.js     ← same, plain Node (used by workflow)
    └── step-summary.ts     ← same, TypeScript source
```

## Anatomy of the main workflow

```yaml
on:
  push:    { branches: [main] }
  pull_request: { branches: [main] }

jobs:
  python:
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: 06-full-framework/python
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.11", cache: pip }
      - run: pip install -r requirements.txt
      - run: playwright install chromium --with-deps
      - run: python run.py --headless              # ← headless flag
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
      - run: python ../../07-ci-cd/scripts/step-summary.py report.json >> $GITHUB_STEP_SUMMARY
        if: always()                               # ← runs even on failure
      - uses: actions/upload-artifact@v4
        if: always()                               # ← artifact even on failure
        with:
          name: report-python
          path: |
            06-full-framework/python/report.md
            06-full-framework/python/report.json
```

### Why `if: always()`

By default, a step is skipped when a previous step fails. `if: always()` overrides this so the summary and artifact upload run regardless of the test outcome — the failure report is exactly when you need the artifact most.

### `--with-deps`

`playwright install chromium --with-deps` installs Chromium plus its OS-level dependencies (fonts, libs) on the Ubuntu runner. Without `--with-deps` the browser launches but crashes on missing system libraries.

## Cost awareness

Each run calls Claude multiple times (one architect call + N runner calls + M asserter calls). A typical Module 06 run uses roughly 50–150K tokens depending on the number of scenarios.

To keep costs predictable:
- Only run the full suite on PRs to `main`, not on every feature branch push
- Use the `smoke` workflow (`workflow_dispatch`) for full cross-module testing
- Add a `paths` filter to skip runs when only docs change:

```yaml
on:
  push:
    branches: [main]
    paths:
      - "0[2-6]-**"        # only re-run when module code changes
      - ".github/**"
```
