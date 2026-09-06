import { parseDocument, serializeDocument } from "./frontmatterParser";

export type SynthesisFormat = "report" | "list" | "venn";
export interface ResearchSource { path: string; name: string; content: string }

function keyPoints(content: string): string[] {
  const { body } = parseDocument(content);
  return body.replace(/^#+\s+.*$/gm, "").split(/(?<=[.!?])\s+|\n+/).map((line) => line.replace(/^[-*>\s]+/, "").trim()).filter((line) => line.length > 24).slice(0, 3);
}

export function buildResearchSynthesis(sources: ResearchSource[], format: SynthesisFormat) {
  const created = new Date().toISOString();
  const title = `Research synthesis — ${created.slice(0, 10)}`;
  const sections = sources.map((source, index) => {
    const parsed = parseDocument(source.content);
    const sourceTitle = String(parsed.frontmatter.title || source.name.replace(/\.md$/, ""));
    const url = String(parsed.frontmatter.source || "");
    const points = keyPoints(source.content);
    const citation = url ? `[${sourceTitle}](${url})` : `[[${source.path}]]`;
    return { index: index + 1, title: sourceTitle, citation, points };
  });
  let body = `# ${title}\n\n`;
  if (format === "report") body += sections.map((section) => `## ${section.title}\n\n${section.points.map((point) => `- ${point}`).join("\n")}\n\nSource: ${section.citation}`).join("\n\n");
  if (format === "list") body += sections.flatMap((section) => section.points.map((point) => `- ${point} — ${section.citation}`)).join("\n");
  if (format === "venn") body += `## Shared themes\n\nCompare recurring terms and claims across the selected sources.\n\n${sections.map((section) => `## Source ${section.index}: ${section.title}\n\n${section.points.map((point) => `- ${point}`).join("\n")}\n\n${section.citation}`).join("\n\n")}`;
  const content = serializeDocument(body, { title, type: "research-synthesis", status: "draft", format, created, sources: sources.map((source) => source.path) });
  return { filename: `research-synthesis-${created.slice(0, 10)}.md`, content };
}
