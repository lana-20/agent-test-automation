import * as dotenv from "dotenv";
import { execute } from "./orchestrator";
import { console_, writeMarkdown, writeJson } from "./agents/reporter";

dotenv.config();

const SPEC = `
Test the TodoMVC application at https://demo.playwright.dev/todomvc

Feature: Todo list management
- Users can add new todo items
- Users can mark items as complete
- Users can delete items
- Users can filter by All / Active / Completed
- The item counter reflects the number of active (incomplete) todos
- Completing all todos shows a "Clear completed" button
`;

const headless = process.argv.includes("--headless");

execute(SPEC, headless)
  .then((report) => {
    console_(report);
    writeMarkdown(report, "report.md");
    writeJson(report, "report.json");
    if (report.failed > 0) process.exit(1);
  })
  .catch(console.error);
