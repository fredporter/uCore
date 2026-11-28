<template>
  <nav
    class="surface-tab-nav"
    :class="[
      `surface-tab-nav--${orientation}`,
      { 'surface-tab-nav--has-toggle': showToggle }
    ]"
    :data-overflow-start="overflowStart ? 'true' : undefined"
    :data-overflow-end="overflowEnd ? 'true' : undefined"
  >
    <!-- Orientation toggle icon -->
    <button
      v-if="showToggle"
      class="surface-tab-nav__toggle"
      :title="orientation === 'horizontal' ? 'Switch to vertical layout' : 'Switch to horizontal layout'"
      @click="toggleOrientation"
    >
      <UIcon :name="orientation === 'horizontal' ? 'swap_vert' : 'swap_horiz'" />
    </button>

    <!-- Tab links — the scroller, so the toggle and actions stay pinned -->
    <div
      ref="scroller"
      class="surface-tab-nav__scroll"
      @scroll="updateOverflow"
      @focusin="onFocusIn"
    >
      <a
        v-for="(tab, index) in tabs"
        :key="tab.id"
        class="surface-tab-nav__link"
        :class="{ 'surface-tab-nav__link--active': modelValue === tab.id }"
        :aria-current="modelValue === tab.id ? 'page' : undefined"
        href="#"
        @click.prevent="onTabClick(tab.id)"
        @keydown="onKeydown($event, index)"
      >
        <UIcon :name="tab.icon" class="surface-tab-nav__icon" />
        <span class="surface-tab-nav__label">{{ tab.label }}</span>
      </a>
    </div>

    <!-- Right-side actions slot -->
    <div class="surface-tab-nav__actions">
      <slot name="actions" />
    </div>
  </nav>
</template>

<script setup lang="ts">
/**
 * @component SurfaceTabNav
 * @description Reusable tab navigation bar for surfaces. Supports horizontal (default)
 * and vertical orientations. Links are styled as nav links (not buttons) with underline
 * active state matching the GlobalToolbar tab style. Position can be toggled via an
 * inline icon button.
 *
 * The strip is a single-row scroller: the active tab is revealed on mount, on selection
 * and on focus (WebKit does not scroll a script-focused tab into view), an edge fade
 * appears only while tabs continue past the edge, the active link carries
 * `aria-current="page"`, and arrow/Home/End keys move focus. The toggle and the
 * `actions` slot sit outside the scroller so they stay pinned.
 *
 * @category molecules
 * @props {TabDef[]} tabs - Array of tab definitions with id, label, icon
 * @props {string} modelValue - Currently active tab id (v-model)
 * @props {'horizontal' | 'vertical'} orientation - Layout orientation
 * @props {boolean} showToggle - Whether to show the orientation toggle icon
 * @emits {'update:modelValue'} - Emitted when a tab is clicked
 * @emits {'toggle-orientation'} - Emitted when the orientation toggle is clicked
 * @usage
 *   <SurfaceTabNav
 *     v-model="activeTab"
 *     :tabs="MY_TABS"
 *     :orientation="shell.tabOrientation"
 *     @toggle-orientation="shell.toggleTabOrientation()"
 *   />
 */
import UIcon from '../atoms/UIcon.vue'
import { nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'

export interface TabDef {
  id: string
  label: string
  icon: string
}

interface Props {
  tabs: TabDef[]
  modelValue: string
  orientation?: 'horizontal' | 'vertical'
  showToggle?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  orientation: 'horizontal',
  showToggle: false,
})

const emit = defineEmits<{
  'update:modelValue': [id: string]
  'toggle-orientation': []
}>()

// Keep a fully revealed tab clear of the edge fade.
const EDGE_INSET = 12

const scroller = ref<HTMLElement | null>(null)
const overflowStart = ref(false)
const overflowEnd = ref(false)
let resizeObserver: ResizeObserver | null = null

function links(): HTMLElement[] {
  const root = scroller.value
  if (!root) return []
  return Array.from(root.querySelectorAll<HTMLElement>('.surface-tab-nav__link'))
}

function prefersReducedMotion(): boolean {
  if (typeof window === 'undefined' || typeof window.matchMedia !== 'function') return false
  return window.matchMedia('(prefers-reduced-motion: reduce)').matches
}

/**
 * Bring one tab fully inside the strip without moving the page. WebKit does not
 * scroll a script-focused tab into view, so selection and focus both call this.
 */
function revealIndex(index: number, behavior: ScrollBehavior = 'auto') {
  const root = scroller.value
  const link = links()[index]
  if (!root || !link) return

  const rootBox = root.getBoundingClientRect()
  const linkBox = link.getBoundingClientRect()
  // jsdom and hidden surfaces report a zero box; nothing to reveal.
  if (!rootBox.width || !rootBox.height) return

  // The bar padding sits inside the scroller, so reveal against the content box
  // and leave a small breathing space clear of the edge fade.
  const style = getComputedStyle(root)
  const vertical = props.orientation === 'vertical'
  const lead = vertical ? parseFloat(style.paddingTop) || 0 : parseFloat(style.paddingLeft) || 0
  const trail = vertical ? parseFloat(style.paddingBottom) || 0 : parseFloat(style.paddingRight) || 0

  if (vertical) {
    const top = rootBox.top + lead
    const bottom = rootBox.bottom - trail
    let delta = 0
    if (linkBox.top < top + EDGE_INSET) delta = linkBox.top - top - EDGE_INSET
    else if (linkBox.bottom > bottom - EDGE_INSET) delta = linkBox.bottom - bottom + EDGE_INSET
    if (!delta) return
    const target = Math.max(0, root.scrollTop + delta)
    if (typeof root.scrollTo === 'function') root.scrollTo({ top: target, behavior })
    else root.scrollTop = target
    return
  }

  const left = rootBox.left + lead
  const right = rootBox.right - trail
  let delta = 0
  if (linkBox.left < left + EDGE_INSET) delta = linkBox.left - left - EDGE_INSET
  else if (linkBox.right > right - EDGE_INSET) delta = linkBox.right - right + EDGE_INSET
  if (!delta) return
  const target = Math.max(0, root.scrollLeft + delta)
  if (typeof root.scrollTo === 'function') root.scrollTo({ left: target, behavior })
  else root.scrollLeft = target
}

function revealActive(behavior: ScrollBehavior = 'auto') {
  const index = props.tabs.findIndex(tab => tab.id === props.modelValue)
  if (index >= 0) revealIndex(index, behavior)
}

function updateOverflow() {
  const root = scroller.value
  if (!root) {
    overflowStart.value = false
    overflowEnd.value = false
    return
  }
  const vertical = props.orientation === 'vertical'
  const offset = vertical ? root.scrollTop : root.scrollLeft
  const size = vertical ? root.scrollHeight : root.scrollWidth
  const viewport = vertical ? root.clientHeight : root.clientWidth
  const remaining = size - viewport
  overflowStart.value = remaining > 1 && offset > 1
  overflowEnd.value = remaining > 1 && offset < remaining - 1
}

function onFocusIn(event: FocusEvent) {
  const target = event.target as HTMLElement | null
  if (!target?.classList?.contains('surface-tab-nav__link')) return
  revealIndex(links().indexOf(target), 'auto')
}

function focusIndex(index: number) {
  const link = links()[index]
  if (!link) return
  link.focus({ preventScroll: true })
  revealIndex(index, 'auto')
}

function onKeydown(event: KeyboardEvent, index: number) {
  const last = props.tabs.length - 1
  const vertical = props.orientation === 'vertical'
  const nextKey = vertical ? 'ArrowDown' : 'ArrowRight'
  const previousKey = vertical ? 'ArrowUp' : 'ArrowLeft'
  let next: number

  if (event.key === nextKey) next = index === last ? 0 : index + 1
  else if (event.key === previousKey) next = index === 0 ? last : index - 1
  else if (event.key === 'Home') next = 0
  else if (event.key === 'End') next = last
  else return

  event.preventDefault()
  focusIndex(next)
}

function onTabClick(id: string) {
  emit('update:modelValue', id)
}

function toggleOrientation() {
  emit('toggle-orientation')
}

onMounted(() => {
  void nextTick(() => {
    revealActive('auto')
    updateOverflow()
  })
  // Fonts change tab widths after first paint, which moves the selected tab.
  if (typeof document !== 'undefined' && document.fonts?.ready) {
    void document.fonts.ready.then(() => revealActive('auto'))
  }
  if (typeof ResizeObserver !== 'undefined' && scroller.value) {
    resizeObserver = new ResizeObserver(() => {
      updateOverflow()
      // Re-reveal on resize, orientation change and the first non-zero layout.
      revealActive('auto')
    })
    resizeObserver.observe(scroller.value)
  }
})

onBeforeUnmount(() => {
  resizeObserver?.disconnect()
  resizeObserver = null
})

watch(
  () => props.modelValue,
  () => {
    void nextTick(() => {
      revealActive(prefersReducedMotion() ? 'auto' : 'smooth')
      updateOverflow()
    })
  },
)

watch(
  () => props.tabs,
  () => {
    void nextTick(() => updateOverflow())
  },
)
</script>

<style scoped>
/* ─── Base ─────────────────────────────────────────────────────────── */
.surface-tab-nav {
  display: flex;
  align-items: center;
  gap: 0;
  flex-shrink: 0;
  position: relative;
  background: var(--usx-color-surface);
  overflow: hidden;
  box-sizing: border-box;
}

/* ─── Scroller — links scroll; toggle and actions stay pinned ────────── */
.surface-tab-nav__scroll {
  display: flex;
  align-items: center;
  flex: 1 1 auto;
  min-width: 0;
  min-height: 0;
  overflow-x: auto;
  overflow-y: hidden;
  scroll-padding-inline: var(--usx-spacing-sm);
  overscroll-behavior-x: contain;
}

.surface-tab-nav--vertical .surface-tab-nav__scroll {
  flex-direction: column;
  align-items: stretch;
  overflow-x: hidden;
  overflow-y: auto;
  scroll-padding-block: var(--usx-spacing-sm);
  overscroll-behavior-y: contain;
}

/* ─── Edge fades — shown only while tabs continue beyond the edge ───── */
.surface-tab-nav::before,
.surface-tab-nav::after {
  content: '';
  position: absolute;
  top: 0;
  bottom: 0;
  width: 16px;
  z-index: 1;
  opacity: 0;
  pointer-events: none;
  transition: opacity var(--usx-transition-fast);
}

.surface-tab-nav::before {
  left: 0;
  background: linear-gradient(to right, var(--usx-color-surface), transparent);
}

.surface-tab-nav::after {
  right: 0;
  background: linear-gradient(to left, var(--usx-color-surface), transparent);
}

.surface-tab-nav[data-overflow-start='true']::before,
.surface-tab-nav[data-overflow-end='true']::after {
  opacity: 1;
}

.surface-tab-nav--vertical::before,
.surface-tab-nav--vertical::after {
  content: none;
}

/* ─── Horizontal (default) ─────────────────────────────────────────── */
.surface-tab-nav--horizontal {
  flex-direction: row;
  justify-content: flex-start;
  padding: 0;
  border-bottom: var(--usx-border-width) solid var(--usx-color-border);
}

/* Bar padding lives inside the scroller so a clipped tab runs under the fade
   instead of stopping short of it. */
.surface-tab-nav--horizontal .surface-tab-nav__scroll {
  padding: var(--usx-surface-tab-bar-padding);
}

.surface-tab-nav--horizontal::before,
.surface-tab-nav--horizontal::after {
  bottom: var(--usx-border-width);
}

/* ─── Vertical ──────────────────────────────────────────────────────── */
.surface-tab-nav--vertical {
  flex-direction: column;
  justify-content: flex-start;
  padding: var(--usx-spacing-xs) 0;
  border-right: var(--usx-border-width) solid var(--usx-color-border);
  min-width: var(--usx-sidebar-compact-width);
  align-items: stretch;
}

/* ─── Links — styled as nav (not buttons) ──────────────────────────── */
.surface-tab-nav__link {
  display: inline-flex;
  align-items: center;
  gap: var(--usx-spacing-xs);
  padding: var(--usx-tab-padding);
  border: none;
  background: transparent;
  color: var(--usx-color-on-surface-muted);
  cursor: pointer;
  font-size: var(--usx-font-size-base);
  font-weight: var(--usx-font-weight-medium);
  line-height: var(--usx-line-height-tight);
  white-space: nowrap;
  transition: color var(--usx-transition-base);
  text-decoration: none;
  font-family: var(--usx-font-family-sans);
}

/* No button-style effects */
.surface-tab-nav__link:hover {
  color: var(--usx-color-primary);
  background: transparent;
  box-shadow: none;
  outline: none;
}

.surface-tab-nav__link:active {
  background: transparent;
  box-shadow: none;
  outline: none;
}

/* Keyboard focus must stay visible: it is the only cue inside the strip. */
.surface-tab-nav__link:focus-visible {
  outline: 2px solid var(--usx-color-primary);
  outline-offset: -2px;
  border-radius: var(--usx-radius-sm);
}

.surface-tab-nav__link--active {
  color: var(--usx-color-primary);
}

/* ─── Vertical link variant ───────────────────────────────────────── */
.surface-tab-nav--vertical .surface-tab-nav__link {
  border: none;
  padding: var(--usx-spacing-sm) calc(var(--usx-spacing-md) + 1.35em + var(--usx-spacing-sm)) var(--usx-spacing-sm) var(--usx-spacing-md);
  justify-content: flex-start;
}

.surface-tab-nav--vertical .surface-tab-nav__link:hover {
  color: var(--usx-color-primary);
}

.surface-tab-nav--vertical .surface-tab-nav__link--active {
  color: var(--usx-color-primary);
}

/* ─── Right-side actions ──────────────────────────────────────────── */
.surface-tab-nav__actions {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-xs);
  margin-left: auto;
  flex-shrink: 0;
}

.surface-tab-nav--vertical .surface-tab-nav__actions {
  margin-left: 0;
  margin-top: auto;
  flex-direction: column;
}

/* ─── Toggle orientation button ────────────────────────────────────── */
.surface-tab-nav__toggle {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--usx-spacing-xs);
  border: none;
  background: transparent;
  color: var(--usx-color-on-surface-muted);
  cursor: pointer;
  font-size: var(--usx-icon-size-sm);
  line-height: var(--usx-line-height-none);
  width: var(--usx-touch-min);
  height: var(--usx-touch-min);
  flex-shrink: 0;
  transition: color var(--usx-transition-fast);
  -webkit-appearance: none;
  appearance: none;
}

.surface-tab-nav__toggle:hover {
  color: var(--usx-color-on-surface);
  background: transparent;
  box-shadow: none;
  outline: none;
}

.surface-tab-nav--horizontal .surface-tab-nav__toggle {
  margin-right: var(--usx-spacing-sm);
}

.surface-tab-nav--vertical .surface-tab-nav__toggle {
  align-self: center;
  margin-bottom: var(--usx-spacing-xs);
}

/* ─── Icon sizing — relative to tab label font ── */
.surface-tab-nav__icon {
  flex-shrink: 0;
  width: 1.1em;
  height: 1.1em;
  font-size: 1.1em;
  display: flex;
  align-items: center;
  justify-content: center;
  line-height: var(--usx-line-height-none);
  vertical-align: middle;
}

.surface-tab-nav__icon :deep(.material-symbols-outlined) {
  font-size: 1.1em;
}

.surface-tab-nav__icon :deep(iconify-icon) {
  width: 1.1em;
  height: 1.1em;
}

.surface-tab-nav__label {
  line-height: var(--usx-line-height-tight);
}

/* Touch pointers need a full target; desktop keeps the calm 39px row. */
@media (pointer: coarse) {
  .surface-tab-nav--horizontal .surface-tab-nav__link {
    min-height: var(--usx-touch-min);
  }
}


</style>
