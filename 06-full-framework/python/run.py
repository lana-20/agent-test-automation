import sys
from orchestrator import execute
from agents import reporter

SPEC = """
Test the TodoMVC application at https://demo.playwright.dev/todomvc

Feature: Todo list management
- Users can add new todo items
- Users can mark items as complete
- Users can delete items
- Users can filter by All / Active / Completed
- The item counter reflects the number of active (incomplete) todos
- Completing all todos shows a "Clear completed" button
"""


def main() -> None:
    headless = "--headless" in sys.argv
    report = execute(SPEC, headless=headless)

    reporter.console(report)
    reporter.write_markdown(report, "report.md")
    reporter.write_json(report, "report.json")

    if report.failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
