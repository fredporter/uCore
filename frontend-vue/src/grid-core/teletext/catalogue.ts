import {
  MAX_DOCS_PER_LIBRARY,
  type PublicLibraryDef,
  type VaultDoc,
  type VaultLibrary,
} from "@udos/gridcore/teletext";

export const PUBLIC_LIBRARY_DEFS: PublicLibraryDef[] = [
  { id: "documentation", label: "Documentation", source: "public", tag: "doc-sites", page: 200, colour: 2 },
  { id: "knowledge", label: "Global Knowledge", source: "global-knowledge", tag: null, page: 300, colour: 3 },
  { id: "learning", label: "Learning", source: "public", tag: "learning", page: 400, colour: 6 },
];

export interface LibrarySearchResponse {
  ok: boolean;
  status: number;
  json(): Promise<unknown>;
}

export class TeletextCatalogueError extends Error {}

export function normalizeLibrarySearchPayload(payload: unknown): VaultDoc[] {
  if (!payload || typeof payload !== "object" || !Array.isArray((payload as { results?: unknown }).results)) {
    throw new TeletextCatalogueError("Library search returned an invalid results payload");
  }
  return (payload as { results: unknown[] }).results.map((value, index) => {
    if (!value || typeof value !== "object") {
      throw new TeletextCatalogueError(`Library search result ${index} is invalid`);
    }
    const item = value as Record<string, unknown>;
    if (typeof item.path !== "string" || typeof item.filename !== "string" ||
        typeof item.extension !== "string" || (item.tags !== undefined &&
        (!Array.isArray(item.tags) || !item.tags.every(tag => typeof tag === "string")))) {
      throw new TeletextCatalogueError(`Library search result ${index} is invalid`);
    }
    return {
      path: item.path,
      filename: item.filename,
      binder: typeof item.binder === "string" ? item.binder : null,
      tags: item.tags ?? [],
      preview: typeof item.preview === "string" ? item.preview : "",
      extension: item.extension,
    };
  });
}

export async function readLibrarySearchResponse(
  response: LibrarySearchResponse,
  source: string,
): Promise<VaultDoc[]> {
  if (!response.ok) throw new TeletextCatalogueError(`HTTP ${response.status} (${source})`);
  return normalizeLibrarySearchPayload(await response.json());
}

export function buildTeletextLibraries(
  documentsBySource: ReadonlyMap<string, readonly VaultDoc[]>,
  definitions: readonly PublicLibraryDef[] = PUBLIC_LIBRARY_DEFS,
): VaultLibrary[] {
  return definitions.map((definition) => {
    const sourceDocuments = documentsBySource.get(definition.source) ?? [];
    const docs = (definition.tag
      ? sourceDocuments.filter(document => document.tags.includes(definition.tag!))
      : sourceDocuments
    ).filter(document => document.extension === "md" || document.extension === "markdown")
      .slice(0, MAX_DOCS_PER_LIBRARY);
    return { ...definition, docs };
  });
}