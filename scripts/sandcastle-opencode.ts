import { run, opencode } from "@ai-hero/sandcastle";
import { noSandbox } from "@ai-hero/sandcastle/sandboxes/no-sandbox";

const task = process.env.SANDCASTLE_TASK!;
const issueNumber = process.env.SANDCASTLE_ISSUE_NUMBER;
const apiKey = process.env.OPENCODE_API_KEY!;
const baseUrl = process.env.OPENCODE_BASE_URL;
const model =
  process.env.OPENCODE_MODEL || "opencode-go/deepseek-v4-flash";

function normalizeIssueNumber(input: string | undefined): string {
  if (!input) {
    return "";
  }

  const trimmed = input.trim();
  if (!trimmed) {
    return "";
  }

  const urlMatch = trimmed.match(/github\.com\/[^/]+\/[^/]+\/issues\/(\d+)/i);
  if (urlMatch) {
    return urlMatch[1];
  }

  const hashMatch = trimmed.match(/^#(\d+)$/);
  if (hashMatch) {
    return hashMatch[1];
  }

  const numericMatch = trimmed.match(/^(\d+)$/);
  if (numericMatch) {
    return numericMatch[1];
  }

  return "";
}

if (!task) {
  console.error("FATAL: SANDCASTLE_TASK environment variable is required.");
  process.exit(1);
}

if (!apiKey) {
  console.error("FATAL: OPENCODE_API_KEY environment variable is required.");
  process.exit(1);
}

const timestamp = Date.now();
const branchName = `sandcastle/opencode-${timestamp}`;

async function main() {
  const resolvedIssueNumber = normalizeIssueNumber(issueNumber);

  console.log("=== Sandcastle OpenCode Agent ===");
  console.log("");
  console.log(`Task:   ${task}`);
  console.log(`Model:  ${model}`);
  console.log(`Branch: ${branchName}`);
  console.log(`Base URL: ${baseUrl || "(default)"}`);
  console.log("");

  const result = await run({
    agent: opencode(model, {
      variant: "high",
    }),
    sandbox: noSandbox(),
    promptFile: ".sandcastle/prompt.md",
    promptArgs: {
      TASK: task,
      ISSUE_NUMBER: resolvedIssueNumber,
    },
    maxIterations: 3,
    completionSignal: "<promise>COMPLETE</promise>",
    logging: { type: "stdout" },
    idleTimeoutSeconds: 600,
  });

  console.log("");
  console.log("=== Results ===");
  console.log(`Branch:     ${result.branch}`);
  console.log(`Commits:    ${result.commits.length}`);
  console.log(`Iterations: ${result.iterations.length}`);

  if (result.commits.length > 0) {
    console.log("");
    console.log("Commits:");
    for (const commit of result.commits) {
      console.log(`  ${commit.sha}`);
    }
  } else {
    console.log("");
    console.log("No commits created. Check agent output above.");
  }
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
