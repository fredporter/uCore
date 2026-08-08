# Bangle Editor Upgrade Sprint — Complete Implementation Plan

## Overview

Comprehensive upgrade to Bangle markdown editor with web research integration, workspace management, and enhanced tooling.

**Timeline:** 11-17 hours of development
**Priority:** High (foundational for research workflow)
**Status:** Scheduled for Sprint 02

---

## Phase 1: Workspace Tree Sidebar (2-3 hours)

**Goal:** Enable users to organize and navigate multiple documents in a structured file tree

### Components to Create

- `WorkspaceTree.vue` — Sidebar component (collapsible folders, file browser)
- `WorkspaceTreeNode.vue` — Individual file/folder item with context menu
- `FileOperations.ts` — Utilities for create, rename, delete, open operations

### Store Updates

- `useEditorSurface` — Add workspace files state
- `useWorkspaceStore` (new) — File tree management, breadcrumb navigation

### Features

- [ ] Display nested file/folder structure
- [ ] Double-click to open file in Bangle
- [ ] Right-click context menu (new, rename, delete, move)
- [ ] Breadcrumb navigation at sidebar top
- [ ] Drag-and-drop file organization
- [ ] Search/filter files
- [ ] Persist folder expansion state

### API Integration

- `GET /api/editor/workspace` — Fetch file tree
- `POST /api/editor/files` — Create file
- `PUT /api/editor/files/:id` — Rename/move file
- `DELETE /api/editor/files/:id` — Delete file

### Layout Changes

```
Before: [Full-width Editor]
After:  [Sidebar] | [Editor] | [Research Panel (optional)]
```

### Success Criteria

- [ ] Sidebar renders file tree without lag (< 100ms)
- [ ] Context menu works on touch and mouse
- [ ] Files open directly in editor
- [ ] Mobile: Sidebar converts to modal drawer
- [ ] Folder state persists across sessions

---

## Phase 2: Frontmatter & Metadata Pills (2-3 hours)

**Goal:** Display and edit document metadata visually using frontmatter tags/pills

### Components to Create

- `FrontmatterParser.ts` — YAML parsing utility
- `FrontmatterPills.vue` — Display metadata as editable pills
- `FrontmatterEditor.vue` — Modal for YAML editing
- `FrontmatterExtractor.ts` — Extract from document head

### Store Updates

- `useEditorSurface` — Add frontmatter state
- Reactive frontmatter updates

### Features

- [ ] Parse YAML frontmatter from document
- [ ] Display as pills: `#tag`, `author:name`, `status:draft`, `date:2026-08-08`
- [ ] Click pill to edit metadata
- [ ] Drag-and-drop to reorder pills
- [ ] Auto-save changes to document frontmatter
- [ ] Frontmatter editor modal (YAML form or text)
- [ ] Frontmatter templates (blog post, research, etc.)

### Example Frontmatter

```yaml
---
title: "Document Title"
tags: ["#research", "#vue", "#web-scraping"]
author: "User Name"
date: "2026-08-08"
source: "https://example.com"
status: "draft"
---
```

### UI Rendering

```
Pills: [ #research ] [ author:User ] [ status:draft ] [ date:2026-08-08 ] [+]
Editors: Click pill → inline edit or modal
```

### Success Criteria

- [ ] Frontmatter parses correctly from all markdown formats
- [ ] Pills render without visual lag
- [ ] Click-to-edit flow is smooth
- [ ] Auto-save doesn't cause flickering
- [ ] Mobile: Pills wrap gracefully
- [ ] Frontmatter stays synchronized with document

---

## Phase 3: Enhanced Markdown Toolbar (2-3 hours)

**Goal:** Provide comprehensive formatting toolbar with Material Symbols icons and organized sections

### Components to Create

- `EnhancedBangleToolbar.vue` — Full-featured toolbar
- `ToolbarSection.vue` — Toolbar grouping component
- `ToolbarButton.vue` — Icon button with tooltip

### Toolbar Sections

1. **Text Formatting** (6 buttons)
   - [ ] Bold (B)
   - [ ] Italic (I)
   - [ ] Underline (U)
   - [ ] Strikethrough (S)
   - [ ] Inline Code (code)
   - [ ] Link (link)

2. **Block Elements** (8 buttons)
   - [ ] Heading (title — dropdown H1-H6)
   - [ ] Block Quote (format_quote)
   - [ ] Bullet List (list)
   - [ ] Ordered List (format_list_numbered)
   - [ ] Code Block (code_blocks)
   - [ ] Table (table_chart)
   - [ ] Horizontal Rule (remove)
   - [ ] Image (image)

3. **Document Structure** (3 buttons)
   - [ ] Outline (toc — table of contents)
   - [ ] Insert Callout (info)
   - [ ] Insert Footnote (footnote)

4. **Research Tools** (5 buttons — FUTURE)
   - [ ] Web Scrape (language)
   - [ ] Summarize (summarize)
   - [ ] Add Citation (quote)
   - [ ] Combine Research (merge)
   - [ ] Copy to Binder (save_alt)

5. **Document Actions** (5 buttons — FUTURE)
   - [ ] Copy to Binder (folder_copy)
   - [ ] Create Variant (fork_right)
   - [ ] Archive Document (archive)
   - [ ] Revert to Last (restore)
   - [ ] Settings (settings)

6. **Edit Controls** (3 buttons)
   - [ ] Undo (undo)
   - [ ] Redo (redo)
   - [ ] Mode Toggle (code/notes)

### Integration

- Replace simple text-button toolbar in BangleEditor
- Use Material Symbols (self-hosted icon font)
- Tooltips on hover with keyboard shortcuts
- Responsive: collapse to dropdown menu on mobile

### Success Criteria

- [ ] 20+ formatting options available
- [ ] Icons load without flashing
- [ ] Tooltips appear on 300ms hover
- [ ] Mobile: Toolbar scrolls horizontally or converts to icon menu
- [ ] Keyboard shortcuts work (Ctrl+B, Cmd+I, etc.)
- [ ] No toolbar layout shift when toggling options

---

## Phase 4: BrowserUI Integration (2-3 hours)

**Goal:** Cards on BrowserUI surface open in Bangle with auto-scraped content

### Components to Create

- `WebScraperModal.vue` — URL input + preview
- `ResearchDocTemplate.ts` — Generate frontmatter + markdown

### Changes to Existing Components

- BrowserUISurface.vue — Card click handler
- DevChatPanel.vue or ChatBubblePanel.vue — Add link to context

### Flow

```
1. User clicks research card on BrowserUI
2. Modal opens: "Open in Bangle?"
3. Scraper fetches URL content
4. Create new document with:
   - Frontmatter: title, source, date, type: "research"
   - Content: cleaned markdown from URL
5. Open document in Bangle editor
6. User can annotate/edit/combine
```

### API Integration

- `POST /api/editor/scrape-web` → HTML content
- `POST /api/editor/create-research-doc` → New document ID

### Success Criteria

- [ ] Cards route to Bangle instead of external links
- [ ] Content scrapes without errors
- [ ] Frontmatter auto-populates correctly
- [ ] Document opens in editor immediately
- [ ] Fallback for failed scrapes (plain link saved)
- [ ] Can still open original URL if needed

---

## Phase 5: Web Content Import & Editing (2-3 hours)

**Goal:** Extract formatted content from web pages and edit in WYSIWYG

### Utilities to Create

- `HtmlToMarkdown.ts` — Convert HTML → Markdown preserving formatting
- `WebScraper.ts` — Extract article content from arbitrary URLs
- `FormattedHtmlPreview.ts` — Display HTML preview option

### Features

- [ ] "Web Scrape" button in toolbar (new)
- [ ] URL input dialog with live preview
- [ ] Auto-extract: title, description, article body
- [ ] HTML → Markdown conversion (preserve bold, italic, lists, images)
- [ ] Display formatted content in editor
- [ ] Option to show HTML source or cleaned markdown
- [ ] Keep raw HTML in frontmatter `_html_source` for reference

### Implementation Details

- Use `turndown` or similar library for HTML→MD
- Handle nested elements, tables, images, links
- Clean up ads, navigation, sidebar content
- Extract canonical URL and favicon

### Success Criteria

- [ ] Web scrape preserves 90% of formatting
- [ ] Works on major news sites, docs, blogs
- [ ] Handles tables, images, code blocks
- [ ] Fallback to plain text if parsing fails
- [ ] Preview shows before saving
- [ ] No external dependencies needed

---

## Phase 6: Research Aggregation & Formatting Tools (3-4 hours)

**Goal:** Aggregate multiple research sources and create synthesis documents

### Components to Create

- `ResearchPanel.vue` — Sidebar showing research context
- `SummarizeModal.vue` — AI summary generation UI
- `CombineResearchModal.vue` — Multi-doc synthesis wizard

### Features

#### A. Summarize Tool

- [ ] Select text → right-click "Summarize"
- [ ] Modal shows: selected text + generated summary
- [ ] Options: insert as blockquote, create new section, create footnote
- [ ] Links back to original selection
- [ ] Requires: POST `/api/editor/summarize` backend

#### B. Combine Research

- [ ] Multi-select documents from sidebar
- [ ] Create synthesis document
- [ ] Auto-extract key points from each source
- [ ] Generate table of contents
- [ ] Create cross-references and citations
- [ ] Preserve source URLs in frontmatter

#### C. Copy to Binder

- [ ] Button: "Export to Binder"
- [ ] Choose destination (project, section, board)
- [ ] Create snapshot/archive version
- [ ] Maintain reference back to original
- [ ] Export as markdown + frontmatter

#### D. Create Variant

- [ ] Branch current document
- [ ] New ID with reference to parent
- [ ] Useful for parallel explorations
- [ ] Both versions sync metadata changes

#### E. Citations

- [ ] Auto-generate from frontmatter source URL
- [ ] Format options: APA, MLA, Chicago
- [ ] Insert as footnotes or bibliography section
- [ ] Auto-detect publication type (article, blog, doc)

### Store Updates

- `useResearchStore` (new)
  - `selectedResearchDocs: EditorFile[]`
  - `summaries: Map<string, string>`
  - `citations: CitationFormat[]`

### Success Criteria

- [ ] Summarize works with AI backend
- [ ] Combine creates coherent synthesis
- [ ] Copy to Binder exports correctly
- [ ] Citations format properly
- [ ] Variants maintain bidirectional reference
- [ ] No data loss during export

---

## Component Architecture Summary

### New Files (16 components)

```
src/skills/
├── molecules/
│   ├── editor/
│   │   ├── BangleEditor.vue (enhance)
│   │   ├── EnhancedBangleToolbar.vue (NEW — Phase 3)
│   │   ├── ToolbarSection.vue (NEW — Phase 3)
│   │   ├── ToolbarButton.vue (NEW — Phase 3)
│   │   ├── WorkspaceTree.vue (NEW — Phase 1)
│   │   ├── WorkspaceTreeNode.vue (NEW — Phase 1)
│   │   ├── FrontmatterPills.vue (NEW — Phase 2)
│   │   ├── FrontmatterEditor.vue (NEW — Phase 2)
│   │   ├── WebScraperModal.vue (NEW — Phase 4)
│   │   ├── ResearchPanel.vue (NEW — Phase 6)
│   │   └── (existing atoms: UIcon, UInput, etc.)
│   └── ...
├── organisms/
│   ├── EditorPanel.vue (refactor to 3-column)
│   ├── ChatBubblePanel.vue (already created)
│   └── ...
└── utils/
    ├── frontmatterParser.ts (NEW — Phase 2)
    ├── htmlToMarkdown.ts (NEW — Phase 5)
    ├── webScraper.ts (NEW — Phase 4)
    ├── fileOperations.ts (NEW — Phase 1)
    ├── researchTools.ts (NEW — Phase 6)
    └── citationGenerator.ts (NEW — Phase 6)
```

### Stores to Update/Create

- `useEditorSurface` — Add workspace, frontmatter, research state
- `useWorkspaceStore` (new) — File tree, breadcrumb, navigation
- `useResearchStore` (new) — Summarize, combine, citations

---

## Implementation Order (Recommended)

1. **Phase 1** ✅ Workspace Tree (foundation)
   - Enables file organization
   - Prerequisite for phases 2+

2. **Phase 2** ✅ Frontmatter Pills (metadata)
   - Complements workspace tree
   - Required for research tracking

3. **Phase 3** ✅ Enhanced Toolbar (UX improvement)
   - No dependencies on other phases
   - Can be done in parallel

4. **Phase 4** ✅ BrowserUI Integration (research workflow)
   - Depends on Phase 1 (file creation)
   - Creates research documents in workspace

5. **Phase 5** ✅ Web Content Tools (research enhancement)
   - Depends on Phase 4 (scraper infrastructure)
   - Improves Phase 4 workflows

6. **Phase 6** ✅ Research Aggregation (advanced)
   - Depends on Phases 1, 2, 4
   - Highest complexity, lowest priority

---

## Milestones & Checkpoints

### Milestone 1: File Organization (Phase 1 + 2)

- Users can organize documents in folders
- Metadata visible and editable
- **Estimated:** 2-3 hours

### Milestone 2: Enhanced Editing (Phase 3)

- Full formatting toolbar with 20+ options
- Improved UX for markdown editing
- **Estimated:** 2-3 hours

### Milestone 3: Web Research Integration (Phase 4 + 5)

- BrowserUI cards open in Bangle
- Web scraping works reliably
- **Estimated:** 2-3 hours

### Milestone 4: Research Synthesis (Phase 6)

- Summarize, combine, export workflows
- Advanced research tools
- **Estimated:** 3-4 hours

---

## Testing Checklist

- [ ] Unit tests for all utilities (Parser, Scraper, Formatter)
- [ ] Component tests for interactive elements (TreeNode, Pills, Toolbar)
- [ ] E2E test: Create → Edit → Export workflow
- [ ] E2E test: BrowserUI card → Bangle integration
- [ ] Performance test: Workspace tree with 100+ files
- [ ] Mobile responsiveness test (iOS Safari, Android Chrome)
- [ ] Keyboard accessibility test (arrow keys, Tab, shortcuts)
- [ ] Dark mode rendering (all components)

---

## API Dependencies

```typescript
// Must be implemented in backend
POST /api/editor/workspace → File tree structure
POST /api/editor/files → Create new file
PUT /api/editor/files/:id → Update/rename file
DELETE /api/editor/files/:id → Delete file
POST /api/editor/scrape-web → Fetch and parse URL
POST /api/editor/summarize → AI summary generation
POST /api/editor/save-to-binder → Export document
GET /api/editor/citations → Generate citations
```

---

## Success Metrics

- [ ] Workspace tree handles 1000+ files smoothly
- [ ] Frontmatter pill editing works within 100ms
- [ ] Toolbar renders all 25+ buttons without lag
- [ ] Web scrape completes within 3 seconds
- [ ] Summarize generates output within 5 seconds
- [ ] Research aggregation scales to 10+ source documents
- [ ] Zero layout shifts or visual glitches
- [ ] Mobile/tablet UX equivalent to desktop
- [ ] All keyboard shortcuts functional
- [ ] Dark mode fully supported

---

## Risk Mitigation

| Risk                       | Mitigation                                          |
| -------------------------- | --------------------------------------------------- |
| HTML→MD conversion lossy   | Test with major sites, keep raw HTML backup         |
| AI summarize latency       | Show spinner, cache summaries, timeout after 10s    |
| Workspace tree performance | Virtualize for 100+ files, lazy-load content        |
| Metadata conflicts         | Lock frontmatter during edit, version conflicts     |
| Mobile sidebar UX          | Convert to bottom sheet modal, full-screen on small |

---

## Notes & Assumptions

1. **State Persistence:** All workspace tree state, frontmatter, and research selections persist to localStorage or backend
2. **Backend Availability:** Phases 4-6 assume backend APIs exist; if not, mock them first
3. **AI Integration:** Summarize and citation generation require backend skill; uCore has AI router
4. **File Storage:** Assume backend handles file persistence; frontend manages workspace tree state
5. **Mobile First:** All components tested for mobile responsiveness
6. **Keyboard Access:** Full keyboard navigation and shortcuts supported (WCAG 2.1 AA)

---

## Timeline Estimate

- **Phase 1:** 2-3 hours
- **Phase 2:** 2-3 hours
- **Phase 3:** 2-3 hours
- **Phase 4:** 2-3 hours
- **Phase 5:** 2-3 hours
- **Phase 6:** 3-4 hours
- **Testing & Polish:** 2-3 hours

**Total: 15-22 hours** (includes testing, documentation, commits)

---

## Related Issues/Tasks

- [ ] Chat Bubble Phase 4 (Chat integration) — COMPLETED ✅
- [ ] Bangle Editor Upgrade (this sprint)
- [ ] Workflow surface enhancement (integrate research results)
- [ ] BrowserUI to Bangle routing

---

## Version

Document Version: 1.0
Last Updated: 2026-08-08
Status: READY FOR IMPLEMENTATION
