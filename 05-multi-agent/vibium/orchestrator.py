import json
import anthropic
from models import TestScenario

_CLIENT = anthropic.Anthropic()

_PLAN_TOOL = {
    "name": "create_test_plan",
    "description": "Output a structured test plan as a list of independent scenarios.",
    "input_schema": {
        "type": "object",
        "properties": {
            "scenarios": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "id":    {"type": "string", "description": "Short identifier, e.g. TC-01"},
                        "title": {"type": "string", "description": "One-line scenario title"},
                        "url":   {"type": "string", "description": "Starting URL for this scenario"},
                        "steps": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Ordered list of test steps",
                        },
                    },
                    "required": ["id", "title", "url", "steps"],
                },
            }
        },
        "required": ["scenarios"],
    },
}

_SYSTEM = (
    "You are a senior QA architect. Given a feature description, produce a "
    "concise test plan broken into independent scenarios. Each scenario must "
    "be runnable in isolation in a fresh browser. Aim for 3–5 scenarios."
)


def plan(feature: str) -> list[TestScenario]:
    response = _CLIENT.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2048,
        system=_SYSTEM,
        tools=[_PLAN_TOOL],
        tool_choice={"type": "tool", "name": "create_test_plan"},
        messages=[{"role": "user", "content": feature}],
    )

    tool_block = next(b for b in response.content if b.type == "tool_use")
    raw = tool_block.input["scenarios"]

    scenarios = [
        TestScenario(
            id=s["id"],
            title=s["title"],
            url=s["url"],
            steps=s["steps"],
        )
        for s in raw
    ]

    print(f"\nOrchestrator generated {len(scenarios)} scenario(s):")
    for s in scenarios:
        print(f"  [{s.id}] {s.title}  ({len(s.steps)} steps)")

    return scenarios
