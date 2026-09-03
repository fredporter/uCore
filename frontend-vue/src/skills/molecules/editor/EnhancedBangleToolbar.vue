<template>
  <div class="enhanced-toolbar" role="toolbar" aria-label="Document formatting">
    <ToolbarSection label="Text formatting" :class="{ 'enhanced-toolbar__desktop-extra': mobile }">
      <ToolbarButton v-for="item in textCommands" :key="item.id" v-bind="item" @activate="command(item.id)" />
    </ToolbarSection>
    <ToolbarSection v-if="mobile" label="Primary formatting">
      <ToolbarButton v-for="item in mobilePrimaryCommands" :key="item.id" v-bind="item" @activate="command(item.id)" />
    </ToolbarSection>
    <ToolbarSection label="Block formatting">
      <label class="enhanced-toolbar__heading">
        <span class="sr-only">Heading level</span>
        <select aria-label="Heading level" @change="heading($event)">
          <option value="">Text</option>
          <option v-for="level in 6" :key="level" :value="`heading-${level}`">H{{ level }}</option>
        </select>
      </label>
      <ToolbarButton v-for="item in blockCommands" :key="item.id" v-bind="item" @activate="command(item.id)" />
    </ToolbarSection>
    <ToolbarSection label="Structure">
      <ToolbarButton v-for="item in structureCommands" :key="item.id" v-bind="item" @activate="command(item.id)" />
    </ToolbarSection>
    <details class="enhanced-toolbar__more">
      <summary aria-label="More editor actions"><UIcon name="more_horiz" /></summary>
      <div class="enhanced-toolbar__menu">
        <ToolbarSection v-if="mobile" label="More formatting">
          <ToolbarButton v-for="item in mobileOverflowCommands" :key="item.id" v-bind="item" @activate="command(item.id)" />
        </ToolbarSection>
        <ToolbarSection label="Research">
          <ToolbarButton v-for="item in researchCommands" :key="item.id" v-bind="item" @activate="command(item.id)" />
        </ToolbarSection>
        <ToolbarSection label="Document">
          <ToolbarButton v-for="item in documentCommands" :key="item.id" v-bind="item" @activate="command(item.id)" />
        </ToolbarSection>
      </div>
    </details>
    <ToolbarSection label="History">
      <ToolbarButton v-for="item in editCommands" :key="item.id" v-bind="item" @activate="command(item.id)" />
    </ToolbarSection>
    <slot name="actions" />
  </div>
</template>

<script setup lang="ts">
import UIcon from "../../atoms/UIcon.vue";
import ToolbarButton from "./ToolbarButton.vue";
import ToolbarSection from "./ToolbarSection.vue";
import { useBreakpoint } from "../../../composables/useBreakpoint";

export type EditorCommand =
  | "bold" | "italic" | "underline" | "strike" | "code" | "link"
  | `heading-${1 | 2 | 3 | 4 | 5 | 6}`
  | "blockquote" | "bullet-list" | "ordered-list" | "code-block" | "horizontal-rule"
  | "table" | "callout" | "footnote" | "outline"
  | "scrape" | "summarize" | "citation"
  | "copy-binder" | "variant" | "archive"
  | "undo" | "redo";

interface Item { id: EditorCommand; label: string; icon: string; shortcut?: string }
const emit = defineEmits<{ command: [command: EditorCommand] }>();
const mobile = useBreakpoint();
const item = (id: EditorCommand, label: string, icon: string, shortcut = ""): Item => ({ id, label, icon, shortcut });
const textCommands = [
  item("bold", "Bold", "format_bold", "⌘B"), item("italic", "Italic", "format_italic", "⌘I"),
  item("underline", "Underline", "format_underlined", "⌘U"), item("strike", "Strikethrough", "strikethrough_s"),
  item("code", "Inline code", "code"), item("link", "Link", "link", "⌘K"),
];
const blockCommands = [
  item("blockquote", "Block quote", "format_quote"), item("bullet-list", "Bullet list", "format_list_bulleted"),
  item("ordered-list", "Ordered list", "format_list_numbered"), item("code-block", "Code block", "data_object"),
  item("horizontal-rule", "Divider", "horizontal_rule"),
];
const structureCommands = [item("table", "Table", "table"), item("callout", "Callout", "campaign"), item("footnote", "Footnote", "footnote"), item("outline", "Outline", "toc")];
const researchCommands = [item("scrape", "Capture research", "travel_explore"), item("summarize", "Summarize", "summarize"), item("citation", "Insert citation", "format_quote")];
const documentCommands = [item("copy-binder", "Copy to Binder", "content_copy"), item("variant", "Create variant", "fork_right"), item("archive", "Archive", "archive")];
const editCommands = [item("undo", "Undo", "undo", "⌘Z"), item("redo", "Redo", "redo", "⇧⌘Z")];
const mobilePrimaryCommands = textCommands.slice(0, 4);
const mobileOverflowCommands = [...textCommands.slice(4), ...blockCommands, ...structureCommands];
function command(value: EditorCommand) { emit("command", value); }
function heading(event: Event) {
  const value = (event.target as HTMLSelectElement).value as EditorCommand;
  if (value) command(value);
  (event.target as HTMLSelectElement).value = "";
}
</script>

<style scoped>
.enhanced-toolbar { display: flex; align-items: center; gap: var(--usx-spacing-xs); width: 100%; overflow-x: auto; white-space: nowrap; }
.enhanced-toolbar__heading select { min-height: var(--usx-control-size-sm); width: 4.5rem; margin: 0; padding: 0 var(--usx-spacing-xs); }
.enhanced-toolbar__more { position: relative; }
.enhanced-toolbar__more summary { display: inline-flex; align-items: center; justify-content: center; width: var(--usx-control-size-sm); height: var(--usx-control-size-sm); cursor: pointer; list-style: none; }
.enhanced-toolbar__menu { position: absolute; z-index: var(--usx-z-index-dropdown); top: 100%; right: 0; display: flex; gap: var(--usx-spacing-sm); padding: var(--usx-spacing-sm); border: var(--usx-border-width) solid var(--usx-color-border); border-radius: var(--usx-radius-md); background: var(--usx-color-surface); box-shadow: var(--usx-shadow-md); }
.sr-only { position: absolute; width: 1px; height: 1px; overflow: hidden; clip: rect(0, 0, 0, 0); }
@media (max-width: 40rem) { .enhanced-toolbar__desktop-extra, .enhanced-toolbar > :deep(.toolbar-section:nth-of-type(n + 3)) { display: none; } .enhanced-toolbar :deep(.toolbar-button) { width: var(--usx-touch-min); height: var(--usx-touch-min); min-width: var(--usx-touch-min); } .enhanced-toolbar__menu { position: fixed; inset-inline: var(--usx-spacing-sm); top: auto; bottom: var(--usx-spacing-sm); flex-wrap: wrap; } }
</style>
