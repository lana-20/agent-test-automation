"""Deterministic judge: keyword matching against expected findings."""
from __future__ import annotations
from dataclasses import dataclass


@dataclass
class DeterministicResult:
    scenario_id: str
    score: float          # 0.0 – 1.0
    matched: list[str]
    missed: list[str]
    passed: bool          # score >= threshold


def judge(scenario_id: str, finding: str, expected_keywords: list[str], threshold: float = 0.6) -> DeterministicResult:
    finding_lower = finding.lower()
    matched = [kw for kw in expected_keywords if kw.lower() in finding_lower]
    missed = [kw for kw in expected_keywords if kw.lower() not in finding_lower]
    score = len(matched) / len(expected_keywords) if expected_keywords else 0.0
    return DeterministicResult(
        scenario_id=scenario_id,
        score=round(score, 3),
        matched=matched,
        missed=missed,
        passed=score >= threshold,
    )


def precision_recall(results: list[DeterministicResult]) -> dict:
    total = len(results)
    passed = sum(1 for r in results if r.passed)
    avg_score = sum(r.score for r in results) / total if total else 0.0
    return {
        "total": total,
        "passed": passed,
        "failed": total - passed,
        "pass_rate": round(passed / total, 3) if total else 0.0,
        "avg_keyword_coverage": round(avg_score, 3),
    }
