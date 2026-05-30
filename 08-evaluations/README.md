# Module 08 — Evaluating Your Agent

Systematic evals to measure how well your AI test agent performs.

## Three judges

| Judge | Measures | Pass threshold |
|---|---|---|
| Deterministic | Keyword coverage in findings | ≥ 60% keywords matched |
| LLM (Claude Haiku) | Accuracy, specificity, actionability | ≥ 0.65 overall score |
| Trajectory | Tool sequence validity, hallucinations | 0 hallucinated tools |

## Python

```bash
cd python
pip install -r requirements.txt
export ANTHROPIC_API_KEY=sk-...

# Run all 10 scenarios
python eval_runner.py

# Run one module's scenarios only
python eval_runner.py 02-playwright

# Compare against baseline
python regression.py

# Save current run as new baseline
python regression.py --save-baseline
```

## TypeScript

```bash
cd typescript
npm install
export ANTHROPIC_API_KEY=sk-...

npm run eval
npm run eval:module 02-playwright
```

## Golden dataset

`python/golden.json` — 10 scenarios across 5 practice sites covering Modules 02–06.
Add new scenarios following the same schema to extend coverage.

## Regression workflow

1. Run `eval_runner.py` → produces `eval_report.md`
2. Export aggregates to `current.json`
3. Run `regression.py` → compares against `baseline.json`
4. If all thresholds pass, promote current to baseline with `--save-baseline`
