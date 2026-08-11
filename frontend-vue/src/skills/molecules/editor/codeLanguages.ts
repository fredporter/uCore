/**
 * @module utils/codeLanguages
 * @description Maps file extensions to CodeMirror language extensions.
 * Supports lazy-loading to keep initial bundle small.
 */
import { type Extension } from "@codemirror/state";
import { markdown } from "@codemirror/lang-markdown";

// ── Language loader registry ──────────────────────────────────────────

type LanguageLoader = () => Promise<Extension | Extension[]>;

const languageLoaders: Record<string, LanguageLoader> = {
  // JavaScript / TypeScript family
  javascript: async () => {
    const { javascript } = await import("@codemirror/lang-javascript");
    return javascript();
  },
  js: async () => {
    const { javascript } = await import("@codemirror/lang-javascript");
    return javascript();
  },
  jsx: async () => {
    const { javascript } = await import("@codemirror/lang-javascript");
    return javascript({ jsx: true });
  },
  typescript: async () => {
    const { javascript } = await import("@codemirror/lang-javascript");
    return javascript({ typescript: true });
  },
  ts: async () => {
    const { javascript } = await import("@codemirror/lang-javascript");
    return javascript({ typescript: true });
  },
  tsx: async () => {
    const { javascript } = await import("@codemirror/lang-javascript");
    return javascript({ jsx: true, typescript: true });
  },

  // Python
  python: async () => {
    const { python } = await import("@codemirror/lang-python");
    return python();
  },
  py: async () => {
    const { python } = await import("@codemirror/lang-python");
    return python();
  },

  // HTML
  html: async () => {
    const { html } = await import("@codemirror/lang-html");
    return html();
  },

  // CSS family
  css: async () => {
    const { css } = await import("@codemirror/lang-css");
    return css();
  },
  scss: async () => {
    const { css } = await import("@codemirror/lang-css");
    return css();
  },
  less: async () => {
    const { css } = await import("@codemirror/lang-css");
    return css();
  },

  // JSON
  json: async () => {
    const { json } = await import("@codemirror/lang-json");
    return json();
  },

  // YAML
  yaml: async () => {
    const { yaml } = await import("@codemirror/lang-yaml");
    return yaml();
  },
  yml: async () => {
    const { yaml } = await import("@codemirror/lang-yaml");
    return yaml();
  },

  // Markdown
  markdown: async () => markdown(),
  md: async () => markdown(),
  mdx: async () => {
    const { markdown } = await import("@codemirror/lang-markdown");
    return markdown();
  },
};

// ── Extension → language name map ─────────────────────────────────────

const EXT_TO_LANG: Record<string, string> = {
  js: "javascript",
  mjs: "javascript",
  cjs: "javascript",
  jsx: "jsx",
  ts: "typescript",
  mts: "typescript",
  tsx: "tsx",
  py: "python",
  pyw: "python",
  html: "html",
  htm: "html",
  css: "css",
  scss: "scss",
  less: "less",
  json: "json",
  jsonc: "json",
  yaml: "yaml",
  yml: "yml",
  md: "markdown",
  mdx: "mdx",
  markdown: "markdown",
};

// ── Cached loaded extensions ──────────────────────────────────────────

const extensionCache = new Map<string, Extension>();

// ── Public API ─────────────────────────────────────────────────────────

/** Resolve a language ID (or filename) to a language name key */
export function languageFor(filename: string): string {
  const ext = filename.split(".").pop()?.toLowerCase() ?? "";
  return EXT_TO_LANG[ext] || "markdown"; // fallback to markdown
}

/** Human-readable language label (e.g., for status bar) */
export function languageLabel(lang: string): string {
  const labels: Record<string, string> = {
    javascript: "JavaScript",
    jsx: "JSX",
    typescript: "TypeScript",
    tsx: "TSX",
    python: "Python",
    html: "HTML",
    css: "CSS",
    scss: "SCSS",
    less: "Less",
    json: "JSON",
    yaml: "YAML",
    markdown: "Markdown",
    mdx: "MDX",
  };
  return labels[lang] || lang.charAt(0).toUpperCase() + lang.slice(1);
}

/** Load (or retrieve cached) a CodeMirror language extension */
export async function loadLanguage(
  lang: string,
): Promise<Extension | null> {
  if (extensionCache.has(lang)) {
    return extensionCache.get(lang)!;
  }
  const loader = languageLoaders[lang];
  if (!loader) {
    // Fall back to markdown for unknown languages
    return loadLanguage("markdown");
  }
  try {
    const ext = await loader();
    const normalized = Array.isArray(ext) ? ext : [ext];
    const combined = normalized.length === 1 ? normalized[0] : normalized;
    extensionCache.set(lang, combined);
    return combined;
  } catch {
    console.warn(`[codeLanguages] Failed to load language: ${lang}`);
    return null;
  }
}

/** Check if a language has a registered loader */
export function hasLanguage(lang: string): boolean {
  return lang in languageLoaders || lang in EXT_TO_LANG;
}

/** All supported language keys */
export function supportedLanguages(): string[] {
  return Object.keys(languageLoaders);
}
