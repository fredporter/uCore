/**
 * @module utils/frontmatterParser
 * @description Extract, parse, serialize YAML frontmatter from markdown strings.
 */

export interface Frontmatter {
  [key: string]: unknown;
}

export interface ParsedDocument {
  frontmatter: Frontmatter;
  body: string;
  hasFrontmatter: boolean;
}

const FRONTMATTER_REGEX = /^---\r?\n([\s\S]*?)\r?\n---\r?\n?/;

/** Split markdown into frontmatter object + body content */
export function parseDocument(markdown: string): ParsedDocument {
  const match = FRONTMATTER_REGEX.exec(markdown);
  if (!match) {
    return { frontmatter: {}, body: markdown, hasFrontmatter: false };
  }
  return {
    frontmatter: parseYaml(match[1]),
    body: markdown.slice(match[0].length),
    hasFrontmatter: true,
  };
}

/** Reconstruct markdown with updated frontmatter */
export function serializeDocument(
  body: string,
  frontmatter: Frontmatter,
): string {
  if (Object.keys(frontmatter).length === 0) return body;
  return `---\n${stringifyYaml(frontmatter)}---\n\n${body}`;
}

/** Parse a minimal YAML string into a plain object (no external deps) */
export function parseYaml(yaml: string): Frontmatter {
  const result: Frontmatter = {};
  for (const line of yaml.split("\n")) {
    const colonIdx = line.indexOf(":");
    if (colonIdx === -1) continue;
    const key = line.slice(0, colonIdx).trim();
    if (!key || key.startsWith("#")) continue;
    const rawValue = line.slice(colonIdx + 1).trim();
    result[key] = parseYamlValue(rawValue);
  }
  return result;
}

/** Serialize a plain object to YAML lines */
export function stringifyYaml(obj: Frontmatter): string {
  return (
    Object.entries(obj)
      .map(([k, v]) => `${k}: ${formatYamlValue(v)}`)
      .join("\n") + "\n"
  );
}

function parseYamlValue(raw: string): unknown {
  if (!raw) return "";
  // Array: [item1, item2]
  if (raw.startsWith("[") && raw.endsWith("]")) {
    return raw
      .slice(1, -1)
      .split(",")
      .map((s) => s.trim().replace(/^["']|["']$/g, ""))
      .filter(Boolean);
  }
  // Quoted string
  if (
    (raw.startsWith('"') && raw.endsWith('"')) ||
    (raw.startsWith("'") && raw.endsWith("'"))
  ) {
    return raw.slice(1, -1);
  }
  // Boolean
  if (raw === "true") return true;
  if (raw === "false") return false;
  // Number
  if (!isNaN(Number(raw)) && raw !== "") return Number(raw);
  return raw;
}

function formatYamlValue(value: unknown): string {
  if (Array.isArray(value)) {
    return `[${value.map((v) => String(v)).join(", ")}]`;
  }
  if (typeof value === "string") {
    // Quote if contains colon or special chars
    if (/[:#\[\]{},|>]/.test(value)) return `"${value.replace(/"/g, '\\"')}"`;
    return value;
  }
  return String(value);
}
