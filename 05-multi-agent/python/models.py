from dataclasses import dataclass, field


@dataclass
class TestScenario:
    id: str
    title: str
    steps: list[str]
    url: str


@dataclass
class RunnerResult:
    scenario_id: str
    title: str
    passed: bool
    summary: str
    step_log: list[dict] = field(default_factory=list)


@dataclass
class TestReport:
    scenarios: list[RunnerResult]

    @property
    def passed(self) -> int:
        return sum(1 for r in self.scenarios if r.passed)

    @property
    def failed(self) -> int:
        return sum(1 for r in self.scenarios if not r.passed)

    @property
    def total(self) -> int:
        return len(self.scenarios)
