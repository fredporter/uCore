# Bangle + Tasker Integration Plan (uCore + uDev)

Date: 2026-08-04
Status: Proposed implementation plan
Owner: uCore/uDev platform

## 1) Current Editor Reality (what is running now)

### uCore frontend-vue

- Primary in-browser document editor is md-editor-v3, wrapped as:
  - skills/molecules/editor/MarkdownEditor.vue
  - skills/molecules/editor/MarkdownPreview.vue
  - skills/organisms/EditorPanel.vue
- md-editor-v3 itself is vendored and currently CodeMirror-based.
- Workflow surface uses EditorPanel in:
  - surfaces/workflow/WorkflowSurface.vue

### uCore Developer surface

- Repo browser (Code/Repository/Editor) uses CodeMirror-based editors:
  - surfaces/developer/DeveloperSurface.vue (UCodeEditor, ProseCodeReader)
- Chat input lives in the Intelligence surface, not the Developer surface.

### Vault coupling still visible

- Workflow binder panel still names the vault layers in labels/actions:
  - surfaces/workflow/panels/BinderPanel.vue
- Workflow store still reads task status through workflow/user APIs and has vault status model fields:
  - stores/workflow.ts

## 2) Product Decision

- Keep Tasker as canonical task model and task API source.
- Use Bangle as the primary long-form document editor.
- Do not use Jotion for this lane.
- Avoid non-Python/non-JavaScript runtime dependencies for integration work.

## 3) Target Architecture

- Tasks:
  - Source of truth: Tasker markdown tasks via backend APIs.
  - Surface: Task list/board UI in workflow tasks panel.
- Documents:
  - Source of truth: markdown files in vault/workspace paths.
  - Editor engine: Bangle in browser.
  - Save path: existing file-save APIs (or new dedicated document save endpoint).

## 4) Integration Steps

### Phase A: Decouple editor surface from md-editor-v3

1. Introduce editor engine abstraction in frontend-vue:
   - Add editor engine selector in a store (markdown/editor settings).
   - Keep md-editor-v3 adapter as Engine A.
   - Add Bangle adapter as Engine B.
2. Update EditorPanel to render active engine adapter instead of directly using MarkdownEditor.
3. Keep preview pane behavior and keyboard save behavior unchanged.

### Phase B: Add Bangle adapter

1. Vendor intake is complete at Vendor/01-RAW/bangle-io.
2. Implement BangleAdapter component under frontend-vue skills/molecules/editor/.
3. Map existing editor callbacks:
   - content change
   - save
   - readonly
   - open document content
4. Ensure style tokens remain USX-compliant in host shell/container.

### Phase C: Tasker-first workflow cleanup

1. Replace workflow task fetches with Tasker endpoints everywhere in workflow store/UI.
2. Remove AppFlowy naming from BinderPanel labels/actions and replace with vault/workspace-neutral language.
3. Keep mission/task/binder projections but make backing source Tasker + markdown metadata pipeline.

### Phase D: Harden and ship

1. Add migration toggle (feature flag): editor.engine = md-editor-v3 | bangle.
2. Run dual-path dogfooding for one sprint.
3. Remove md-editor-v3 hard dependency only after Bangle parity is confirmed.

## 5) Risks and Mitigations

- AGPL license boundary for bangle-io:
  - Keep clear attribution and distribution posture review before broad bundling.
- Existing workflows tied to AppFlowy labels:
  - Rename UI first, then move API dependencies.
- Regression risk in save/load pipeline:
  - Keep the current editor adapter as fallback until parity is proven.

## 6) Immediate Next Tasks

1. Build editor engine abstraction and wire EditorPanel to it.
2. Implement initial Bangle adapter with read/write markdown support.
3. Update workflow store and binder panel to Tasker/vault-first naming and endpoints.
