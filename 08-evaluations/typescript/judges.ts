import Anthropic from "@anthropic-ai/sdk";

export interface DeterministicResult {
  scenarioId: string;
  score: number;
  matched: string[];
  missed: string[];
  passed: boolean;
}

export interface LLMJudgeResult {
  scenarioId: string;
  accuracy: number;
  specificity: number;
  actionability: number;
  overall: number;
  reasoning: string;
  passed: boolean;
}

export interface TrajectoryResult {
  scenarioId: string;
  toolSequence: string[];
  expectedTools: string[];
  coverage: number;
  hallucinated: string[];
  redundantCalls: number;
  passed: boolean;
}

const VALID_TOOLS = new Set([
  "navigate", "click", "fill", "find", "find_all", "get_text", "get_attribute",
  "get_value", "is_visible", "is_enabled", "is_checked", "check", "uncheck",
  "select", "hover", "scroll", "wait", "wait_for_text", "screenshot",
  "evaluate", "count", "get_url", "get_title", "dialog_accept", "dialog_dismiss",
  "keys", "press", "type",
]);

export function judgeDeterministic(
  scenarioId: string,
  finding: string,
  expectedKeywords: string[],
  threshold = 0.6
): DeterministicResult {
  const lower = finding.toLowerCase();
  const matched = expectedKeywords.filter((kw) => lower.includes(kw.toLowerCase()));
  const missed = expectedKeywords.filter((kw) => !lower.includes(kw.toLowerCase()));
  const score = expectedKeywords.length ? matched.length / expectedKeywords.length : 0;
  return { scenarioId, score: +score.toFixed(3), matched, missed, passed: score >= threshold };
}

const RUBRIC = `You are a QA evaluation judge. Score the following test finding on three criteria.

Finding:
{finding}

Task that produced it:
{task}

Score each criterion 0.0 – 1.0:
- accuracy: Is the finding factually correct for the task?
- specificity: Does it name the exact element, selector, or behavior (not vague)?
- actionability: Would a developer know exactly what to fix from this finding alone?

Return ONLY valid JSON:
{"accuracy": float, "specificity": float, "actionability": float, "overall": float, "reasoning": "one sentence"}

overall = (accuracy + specificity + actionability) / 3, rounded to 3 decimal places.`;

export async function judgeLLM(
  client: Anthropic,
  scenarioId: string,
  finding: string,
  task: string,
  threshold = 0.65
): Promise<LLMJudgeResult> {
  const prompt = RUBRIC.replace("{finding}", finding).replace("{task}", task);
  const response = await client.messages.create({
    model: "claude-haiku-4-5-20251001",
    max_tokens: 256,
    messages: [{ role: "user", content: prompt }],
  });

  const raw = (response.content[0] as { text: string }).text.trim();
  const start = raw.indexOf("{");
  const end = raw.lastIndexOf("}") + 1;
  const data = JSON.parse(raw.slice(start, end));
  const overall = +((data.accuracy + data.specificity + data.actionability) / 3).toFixed(3);

  return {
    scenarioId,
    accuracy: data.accuracy,
    specificity: data.specificity,
    actionability: data.actionability,
    overall,
    reasoning: data.reasoning ?? "",
    passed: overall >= threshold,
  };
}

export function judgeTrajectory(
  scenarioId: string,
  toolCalls: Array<{ name?: string; tool?: string }>,
  expectedTools: string[]
): TrajectoryResult {
  const sequence = toolCalls.map((tc) => tc.name ?? tc.tool ?? "");
  const calledSet = new Set(sequence);
  const expectedSet = new Set(expectedTools);
  const coverage = expectedSet.size ? [...expectedSet].filter((t) => calledSet.has(t)).length / expectedSet.size : 0;
  const hallucinated = sequence.filter((t) => !VALID_TOOLS.has(t));

  let redundant = 0;
  for (let i = 2; i < sequence.length; i++) {
    if (sequence[i] === sequence[i - 1] && sequence[i] === sequence[i - 2]) redundant++;
  }

  return {
    scenarioId,
    toolSequence: sequence,
    expectedTools,
    coverage: +coverage.toFixed(3),
    hallucinated,
    redundantCalls: redundant,
    passed: coverage >= 0.6 && hallucinated.length === 0 && redundant === 0,
  };
}
