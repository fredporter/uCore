/**
 * @module utils/htmlToMarkdown
 * @description Converts HTML strings to Markdown preserving structure.
 * No external dependencies — stdlib DOM parsing only.
 */

/** Convert an HTML string to Markdown text */
export function htmlToMarkdown(html: string): string {
  if (typeof window === "undefined") return html;
  const doc = new DOMParser().parseFromString(html, "text/html");
  return nodeToMarkdown(doc.body, 0).trim();
}

function nodeToMarkdown(node: Node, depth: number): string {
  if (node.nodeType === Node.TEXT_NODE) {
    return (node.textContent ?? "").replace(/\s+/g, " ");
  }

  if (node.nodeType !== Node.ELEMENT_NODE) return "";

  const el = node as Element;
  const tag = el.tagName.toLowerCase();
  const children = () =>
    Array.from(el.childNodes)
      .map((c) => nodeToMarkdown(c, depth))
      .join("");

  switch (tag) {
    case "h1":
      return `\n\n# ${children().trim()}\n\n`;
    case "h2":
      return `\n\n## ${children().trim()}\n\n`;
    case "h3":
      return `\n\n### ${children().trim()}\n\n`;
    case "h4":
      return `\n\n#### ${children().trim()}\n\n`;
    case "h5":
      return `\n\n##### ${children().trim()}\n\n`;
    case "h6":
      return `\n\n###### ${children().trim()}\n\n`;
    case "p":
      return `\n\n${children().trim()}\n\n`;
    case "br":
      return "\n";
    case "hr":
      return "\n\n---\n\n";
    case "strong":
    case "b":
      return `**${children()}**`;
    case "em":
    case "i":
      return `_${children()}_`;
    case "s":
    case "del":
      return `~~${children()}~~`;
    case "code": {
      const text = el.textContent ?? "";
      if (el.parentElement?.tagName.toLowerCase() === "pre") return text;
      return `\`${text}\``;
    }
    case "pre": {
      const codeEl = el.querySelector("code");
      const lang = codeEl?.className.replace(/^language-/, "") ?? "";
      const content = codeEl?.textContent ?? el.textContent ?? "";
      return `\n\n\`\`\`${lang}\n${content.trim()}\n\`\`\`\n\n`;
    }
    case "blockquote":
      return `\n\n${children()
        .trim()
        .split("\n")
        .map((l) => `> ${l}`)
        .join("\n")}\n\n`;
    case "a": {
      const href = el.getAttribute("href") ?? "";
      const text = children().trim();
      return href ? `[${text}](${href})` : text;
    }
    case "img": {
      const src = el.getAttribute("src") ?? "";
      const alt = el.getAttribute("alt") ?? "";
      return `![${alt}](${src})`;
    }
    case "ul":
      return `\n\n${listItems(el, "- ")}\n\n`;
    case "ol":
      return `\n\n${listItems(el, "1. ")}\n\n`;
    case "li":
      return children().trim();
    case "table":
      return tableToMarkdown(el);
    case "thead":
    case "tbody":
    case "tr":
    case "td":
    case "th":
      return children(); // handled by tableToMarkdown
    // Skip nav, header, footer, aside, script, style
    case "nav":
    case "header":
    case "footer":
    case "aside":
    case "script":
    case "style":
    case "noscript":
      return "";
    default:
      return children();
  }
}

function listItems(el: Element, prefix: string): string {
  return Array.from(el.querySelectorAll(":scope > li"))
    .map((li) => `${prefix}${nodeToMarkdown(li, 0).trim()}`)
    .join("\n");
}

function tableToMarkdown(table: Element): string {
  const rows = Array.from(table.querySelectorAll("tr"));
  if (!rows.length) return "";

  const toRow = (tr: Element) =>
    Array.from(tr.querySelectorAll("th, td"))
      .map((cell) => cell.textContent?.trim().replace(/\|/g, "\\|") ?? "")
      .join(" | ");

  const header = toRow(rows[0]);
  const sep = rows[0].querySelectorAll("th, td").length;
  const divider = Array(sep).fill("---").join(" | ");
  const body = rows.slice(1).map(toRow).join("\n");

  return `\n\n| ${header} |\n| ${divider} |\n${body ? `| ${body.split("\n").join(" |\n| ")} |` : ""}\n\n`;
}
