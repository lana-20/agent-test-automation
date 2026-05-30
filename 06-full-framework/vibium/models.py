from dataclasses import dataclass, field
from typing import Literal


@dataclass
class TestScenario:
    id: str
    title: str
    url: str
    steps: list[str]
    priority: Literal["high", "medium", "low"]
    category: str
    expected_outcome: str


@dataclass
class RunnerResult:
    scenario_id: str
    title: str
    passed: bool
    summary: str
    step_log: list[dict] = field(default_factory=list)


@dataclass
class Finding:
    scenario_id: str
    title: str
    classification: Literal["bug", "expected-failure", "flaky", "environment"]
    severity: Literal["critical", "high", "medium", "low"]
    description: str
    suggested_action: str


@dataclass
class TestReport:
    spec: str
    results: list[RunnerResult]
    findings: list[Finding]

    @property
    def total(self) -> int:
        return len(self.results)

    @property
    def passed(self) -> int:
        return sum(1 for r in self.results if r.passed)

    @property
    def failed(self) -> int:
        return sum(1 for r in self.results if not r.passed)

    @property
    def bugs(self) -> int:
        return sum(1 for f in self.findings if f.classification == "bug")
