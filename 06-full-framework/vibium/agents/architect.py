import anthropic
from models import TestScenario

_CLIENT = anthropic.Anthropic()

_PLAN_TOOL = {
    "name": "create_test_plan",
    "description": "Output a structured test plan as a list of prioritised, categorised scenarios.",
    "input_schema": {
        "type": "object",
        "properties": {
            "scenarios": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "id":               {"type": "string"},
                        "title":            {"type": "string"},
                        "url":              {"type": "string"},
                        "steps":            {"type": "array", "items": {"type": "string"}},
                        "priority":         {"type": "string", "enum": ["high", "medium", "low"]},
                        "category":         {"type": "string", "description": "e.g. smoke, regression, edge-case"},
                        "expected_outcome": {"type": "string"},
                    },
                    "required": ["id", "title", "url", "steps", "priority", "category", "expected_outcome"],
                },
            }
        },
        "required": ["scenarios"],
    },
}

_SYSTEM = """You are a senior QA architect. Given a feature description or spec, produce a structured test plan.

Rules:
- Break the scope into 4–6 independent scenarios, each runnable in a fresh browser.
- Assign a priority (high / medium / low) and a category (smoke, regression, edge-case, etc.).
- Write a one-sentence expected_outcome for each scenario.
- High-priority scenarios cover the core happy path; medium covers variations; low covers edge cases."""


def plan(spec: str) -> list[TestScenario]:
    response = _CLIENT.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2048,
        system=_SYSTEM,
        tools=[_PLAN_TOOL],
        tool_choice={"type": "tool", "name": "create_test_plan"},
        messages=[{"role": "user", "content": spec}],
    )

    tool_block = next(b for b in response.content if b.type == "tool_use")
    raw = tool_block.input["scenarios"]

    scenarios = [
        TestScenario(
            id=s["id"],
            title=s["title"],
            url=s["url"],
            steps=s["steps"],
            priority=s["priority"],
            category=s["category"],
            expected_outcome=s["expected_outcome"],
        )
        for s in raw
    ]

    print(f"\n[Architect] Generated {len(scenarios)} scenario(s):")
    for s in scenarios:
        print(f"  [{s.id}] [{s.priority.upper()}] {s.title}  ({s.category})")

    return scenarios
