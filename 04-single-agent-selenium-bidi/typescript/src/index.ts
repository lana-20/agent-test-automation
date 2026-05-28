import * as dotenv from "dotenv";
import { run } from "./agent";

dotenv.config();

const TASK = `
Go to https://demo.playwright.dev/todomvc and test the core todo workflow:

1. Add three todos: "Buy groceries", "Walk the dog", "Read a book"
2. Verify all three appear in the list
3. Mark "Walk the dog" as complete
4. Switch to the "Completed" filter and verify only "Walk the dog" is shown
5. Switch to the "Active" filter and verify "Walk the dog" is NOT shown
6. Delete "Buy groceries"
7. Switch to "All" and verify the list has exactly two items

After each navigation, call get_browser_logs to check for JavaScript errors.
Take a screenshot after steps 2, 4, and 7.
`;

// Set BROWSER=firefox before running to test on Firefox:  npm run start:firefox
const browser = process.env.BROWSER ?? "chrome";

run(TASK, browser, false).catch(console.error);
