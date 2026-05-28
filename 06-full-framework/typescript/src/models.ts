export type Priority = "high" | "medium" | "low";
export type Classification = "bug" | "expected-failure" | "flaky" | "environment";
export type Severity = "critical" | "high" | "medium" | "low";

export interface TestScenario {
  id: string;
  title: string;
  url: string;
  steps: string[];
  priority: Priority;
  category: string;
  expected_outcome: string;
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

export interface Finding {
  scenarioId: string;
  title: string;
  classification: Classification;
  severity: Severity;
  description: string;
  suggestedAction: string;
}

export interface TestReport {
  spec: string;
  results: RunnerResult[];
  findings: Finding[];
  total: number;
  passed: number;
  failed: number;
  bugs: number;
}

export function buildReport(
  spec: string,
  results: RunnerResult[],
  findings: Finding[]
): TestReport {
  return {
    spec,
    results,
    findings,
    total: results.length,
    passed: results.filter((r) => r.passed).length,
    failed: results.filter((r) => !r.passed).length,
    bugs: findings.filter((f) => f.classification === "bug").length,
  };
}
