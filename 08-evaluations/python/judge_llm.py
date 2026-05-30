"""LLM-as-judge: scores finding quality against a rubric via Claude."""
from __future__ import annotations
import json
import os
from dataclasses import dataclass

import anthropic

RUBRIC = """You are a QA evaluation judge. Score the following test finding on three criteria.

Finding:
{finding}

Task that produced it:
{task}

Score each criterion 0.0 – 1.0:
- accuracy: Is the finding factually correct for the task?
- specificity: Does it name the exact element, selector, or behavior (not vague)?
- actionability: Would a developer know exactly what to fix from this finding alone?

Return ONLY valid JSON:
{{"accuracy": float, "specificity": float, "actionability": float, "overall": float, "reasoning": "one sentence"}}

overall = (accuracy + specificity + actionability) / 3, rounded to 3 decimal places."""


@dataclass
class LLMJudgeResult:
    scenario_id: str
    accuracy: float
    specificity: float
    actionability: float
    overall: float
    reasoning: str
    passed: bool          # overall >= threshold


def judge(scenario_id: str, finding: str, task: str, threshold: float = 0.65) -> LLMJudgeResult:
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    prompt = RUBRIC.format(finding=finding, task=task)

    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=256,
        messages=[{"role": "user", "content": prompt}],
    )
    raw = response.content[0].text.strip()

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        start = raw.find("{")
        end = raw.rfind("}") + 1
        data = json.loads(raw[start:end])

    overall = round((data["accuracy"] + data["specificity"] + data["actionability"]) / 3, 3)
    return LLMJudgeResult(
        scenario_id=scenario_id,
        accuracy=data["accuracy"],
        specificity=data["specificity"],
        actionability=data["actionability"],
        overall=overall,
        reasoning=data.get("reasoning", ""),
        passed=overall >= threshold,
    )


def aggregate(results: list[LLMJudgeResult]) -> dict:
    total = len(results)
    if not total:
        return {}
    return {
        "total": total,
        "passed": sum(1 for r in results if r.passed),
        "avg_accuracy": round(sum(r.accuracy for r in results) / total, 3),
        "avg_specificity": round(sum(r.specificity for r in results) / total, 3),
        "avg_actionability": round(sum(r.actionability for r in results) / total, 3),
        "avg_overall": round(sum(r.overall for r in results) / total, 3),
    }
