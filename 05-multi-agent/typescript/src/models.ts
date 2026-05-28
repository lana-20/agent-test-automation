export interface TestScenario {
  id: string;
  title: string;
  url: string;
  steps: string[];
}

export interface StepLog {
  tool: string;
  input: Record<string, unknown>;
  result: string;
}

export interface RunnerResult {
  scenarioId: string;
  title: string;
  passed: boolean;
  summary: string;
  stepLog: StepLog[];
}

export interface TestReport {
  scenarios: RunnerResult[];
  passed: number;
  failed: number;
  total: number;
}

export function buildReport(scenarios: RunnerResult[]): TestReport {
  return {
    scenarios,
    passed: scenarios.filter((s) => s.passed).length,
    failed: scenarios.filter((s) => !s.passed).length,
    total: scenarios.length,
  };
}
