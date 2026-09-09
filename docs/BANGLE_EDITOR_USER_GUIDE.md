# Bangle Editor User Guide

The Bangle Editor is uCore's sovereign, local-first markdown authoring environment. It provides structured metadata editing, rich formatting, web research integration, citation generation, and Binder publishing while preserving markdown portability.

---

## 1. Workspace Tree & Navigation

The workspace tree sidebar provides direct access to your local notes, documents, and research folders.

- **Browsing & Expansion**: Click any folder chevron to expand or collapse subdirectories.
- **File Selection**: Click a document to load it into the editor. Active files are highlighted with a distinct indicator.
- **Context Menus**: Right-click on files or folders to create new documents, rename, or delete items safely.
- **Search & Filtering**: Use the top filter input to filter files by filename or tag matching in real time.

---

## 2. Frontmatter Metadata Editor

Bangle stores structured metadata in YAML frontmatter at the top of your markdown files. The interactive Frontmatter Editor allows you to inspect and modify metadata without typing raw YAML syntax.

```markdown
---
title: "Sovereign Computing Architecture"
author: "Engineering"
tags: ["system", "release", "architecture"]
status: "published"
date: "2026-09-09"
---
```

- **Pill Display**: Metadata fields appear as interactive pills above the editor content.
- **Field Editing**: Click any property to edit its key or value inline.
- **Tag Management**: Add, remove, or reorder tags. Tags are synchronized across the workspace filter.
- **Validation**: Schema validation guarantees that frontmatter roundtrips safely through `parseDocument` and `serializeDocument` without stripping markdown content or comments.

---

## 3. Enhanced Formatting Toolbar

The authoring toolbar floats or docks above the editor pane, adapting responsively across desktop, tablet, and mobile displays.

### Formatting Controls
- **Headers**: Toggle H1, H2, and H3 headers (`Ctrl+Alt+1..3` or `Cmd+Opt+1..3`).
- **Inline Styling**: Bold (`Cmd+B` / `Ctrl+B`), Italic (`Cmd+I` / `Ctrl+I`), Code (`Cmd+\`` / `Ctrl+\``), Strikethrough.
- **Lists**: Bullet lists, numbered lists, and task checklists with interactive checkboxes.
- **Blocks**: Blockquotes, code blocks with syntax highlighting, horizontal rules, and table insertion.
- **Responsive Collapse**: On compact viewports, auxiliary tools tuck into an overflow menu (`...`) to preserve vertical screen real estate.

---

## 4. Web Research & Scraper Integration

Bangle connects directly to uCore's governed scraper service to ingest research notes directly from web sources.

1. **Trigger Scraping**: Click the **Scrape / Research** button in the toolbar or open the scraper drawer.
2. **Enter URL**: Provide any target article, blog post, or documentation URL.
3. **Structured Ingestion**: The system fetches the source and extracts:
   - Clean markdown conversion (via `htmlToMarkdown`).
   - Publication type detection (`article`, `blog`, `documentation`, `video`, `webpage`).
   - Page title, author, domain host, and publication timestamp.
4. **Draft Insertion**: Content is inserted directly into the current document or saved as a new research note in your workspace.

---

## 5. Research Combining & Document Variants

When working across multiple research sources or drafting multi-audience versions, use Bangle's synthesis tools.

### Combining Research Notes
- Open the **Combine Research Modal** from the toolbar or workspace context menu.
- Select two or more source notes.
- Choose a synthesis mode: **Append**, **Thematic Merge**, or **Executive Summary**.
- The synthesized result retains backlinks and citations to the original source notes.

### Managing Document Variants
Create specialized versions (e.g. executive summary, technical specification, slide deck) without duplicating core content:
- Use `<!-- variant: <variant-id> -->` delimiters to scope sections.
- Use `createVariantDocument()` to spin off an isolated variant file.
- Use `syncVariantMetadata()` to propagate shared title, author, and tag updates across all related document variants.

---

## 6. Citation Generation & Provenance

Bangle provides citation formatting conforming to academic and sovereign documentation standards.

### Supported Citation Formats
- **APA**: `Author. (Year). Title. Site. URL`
- **MLA**: `Author. "Title." Site, Year, URL. Accessed Date.`
- **Chicago**: `Author. "Title." Site. Year. URL.`
- **Markdown Footnote**: `[^1]: [Title](URL) by Author — Site, accessed Date.`
- **uKnowledge Callout**:
  ```markdown
  > [!NOTE] Citation: Title
  > Provenance: [Site](URL)
  > Author: Name | Published: Date
  ```

### Adding a Citation
1. Click **Insert Citation** (`Cmd+Shift+C` / `Ctrl+Shift+C`) or select **Citation Modal**.
2. Enter the source URL or fill in author, title, and date fields.
3. Select your desired citation format from the dropdown.
4. Click **Insert** to paste the formatted citation footnote or callout at your cursor position.

---

## 7. Exporting to Binder & Presentations

- **Binder Export**: Export the active document and its content directly into the user's Binder workspace as a Markdown file under `~/Vault/<binder>` via the backend Binder API (`POST /api/editor/save-to-binder`).
- **Slide Presentation (Marp)**: Delimit slides with `---` dividers. Bangle renders slides in real time using the Marp renderer for instant full-screen presentations.

---

## 8. Keyboard Shortcuts Reference

| Command | macOS Shortcut | Windows / Linux Shortcut |
| :--- | :--- | :--- |
| **Save Document** | `Cmd + S` | `Ctrl + S` |
| **Toggle Global Chat** | `Cmd + J` | `Ctrl + J` |
| **Bold Text** | `Cmd + B` | `Ctrl + B` |
| **Italic Text** | `Cmd + I` | `Ctrl + I` |
| **Inline Code** | `Cmd + \`` | `Ctrl + \`` |
| **Heading 1** | `Cmd + Opt + 1` | `Ctrl + Alt + 1` |
| **Heading 2** | `Cmd + Opt + 2` | `Ctrl + Alt + 2` |
| **Heading 3** | `Cmd + Opt + 3` | `Ctrl + Alt + 3` |
| **Insert Citation** | `Cmd + Shift + C` | `Ctrl + Shift + C` |
| **Combine Research** | `Cmd + Shift + M` | `Ctrl + Shift + M` |
| **Close Modal / Drawer** | `Escape` | `Escape` |
