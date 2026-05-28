from dotenv import load_dotenv
from agent import run

load_dotenv()

TASK = """
Go to https://demo.playwright.dev/todomvc and test the core todo workflow:

1. Add three todos: "Buy groceries", "Walk the dog", "Read a book"
2. Verify all three appear in the list
3. Mark "Walk the dog" as complete
4. Switch to the "Completed" filter and verify only "Walk the dog" is shown
5. Switch to the "Active" filter and verify "Walk the dog" is NOT shown
6. Delete "Buy groceries"
7. Switch to "All" and verify the list has exactly two items

Take a screenshot after steps 2, 4, and 7.
"""

if __name__ == "__main__":
    run(task=TASK, headless=False)
