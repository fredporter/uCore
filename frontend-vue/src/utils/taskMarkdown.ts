export interface TaskMarkdownShape {
  title: string;
  status: string;
  priority: string;
  board?: string;
  tags?: string[];
}

const STATUS_DONE = new Set(["completed", "done", "closed"]);

function norm(text: string): string {
  return String(text || "")
    .trim()
    .toLowerCase();
}

export function isTaskDone(status: string): boolean {
  return STATUS_DONE.has(norm(status));
}

export function toTaskMarkdownLine(task: TaskMarkdownShape): string {
  const checked = isTaskDone(task.status) ? "x" : " ";
  const tags = (task.tags || [])
    .map((tag) => `#${String(tag).trim()}`)
    .join(" ");
  const board = task.board ? `@${String(task.board).trim()}` : "";
  const priority = `p:${String(task.priority || "medium")
    .trim()
    .toLowerCase()}`;
  return `- [${checked}] ${task.title} ${tags} ${board} ${priority}`
    .replace(/\s+/g, " ")
    .trim();
}

export function parseTaskMarkdownLine(
  line: string,
): Partial<TaskMarkdownShape> {
  const input = String(line || "").trim();
  if (!input.startsWith("- [")) {
    return {};
  }

  const done = /^-\s*\[[xX]\]/.test(input);
  const withoutPrefix = input.replace(/^-\s*\[[ xX]\]\s*/, "").trim();
  const tokens = withoutPrefix.split(/\s+/);

  const tags: string[] = [];
  let board = "";
  let priority = "";
  const titleParts: string[] = [];

  for (const token of tokens) {
    if (token.startsWith("#") && token.length > 1) {
      tags.push(token.slice(1));
      continue;
    }
    if (token.startsWith("@") && token.length > 1) {
      board = token.slice(1);
      continue;
    }
    if (token.startsWith("p:") && token.length > 2) {
      priority = token.slice(2).toLowerCase();
      continue;
    }
    titleParts.push(token);
  }

  return {
    title: titleParts.join(" ").trim(),
    status: done ? "completed" : "todo",
    priority: priority || "medium",
    board,
    tags,
  };
}
