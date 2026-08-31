// ── uCore Frontend: Teletext Module ──────────────────────────────
// E1: extracted from UCodeSurface.vue
// Re-exports stateless types/helpers/builders from @udos/gridcore's reader-model,
// plus adds Vue-specific/reactive config and functions (loaders, renderers that
// use local grid-core buffer functions).
// ────────────────────────────────────────────────────────────────────

// ── Re-exports from @udos/gridcore (stateless) ───────────────────
export {
  ceefaxClock,
  DOC_PAGE_OFFSET,
  DOC_SCREEN_LINES,
  docContentPage,
  docListPage,
  DOCS_PER_LIST_PAGE,
  docScreens,
  // Helpers (pure)
  docTitle,
  helpPage,
  libraryForPage,
  // Page builders (pure, take BuilderContext)
  mainIndexPage,
  MAX_DOCS_PER_LIBRARY,
  newsPage,
  subIndexPage,
  // Constants
  TELETEXT_FASTEXT,
  teletextContent,
  wrapText,
  writeBoxedDoubleHeightTitle,
  // Layout renderers (pure, target ReaderBuffer)
  writeDoubleHeight,
  writeMosaicRule,
  writeSeparatedBar,
  type BuilderContext,
  type PublicLibraryDef,
  type ReaderBuffer,
  type ReaderBufferCell,
  // Types
  type ReaderTeletextPage,
  type VaultDoc,
  type VaultLibrary,
} from "@udos/gridcore/teletext";

// ── Local config: uCore vault public library definitions ──────────
// This maps uCore's vault sources (public / global-knowledge) to Ceefax page ranges.
export {
  buildTeletextLibraries,
  normalizeLibrarySearchPayload,
  PUBLIC_LIBRARY_DEFS,
  readLibrarySearchResponse,
  TeletextCatalogueError,
  type LibrarySearchResponse,
} from "./catalogue";
