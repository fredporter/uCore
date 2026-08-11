/**
 * @component ResizableSplitter
 * @description Draggable divider between two panels.
 * Supports horizontal (left-right) and vertical (top-bottom) splits.
 */
<template>
  <div
    class="resize-split"
    :class="[`resize-split--${direction}`, { 'resize-split--dragging': isDragging }]"
    @pointerdown.prevent="startDrag"
  >
    <div class="resize-split__handle" />
  </div>
</template>

<script setup lang="ts">
import { ref } from "vue";

const props = withDefaults(
  defineProps<{
    direction?: "horizontal" | "vertical";
  }>(),
  { direction: "horizontal" },
);

const emit = defineEmits<{
  resize: [delta: number];
  "resize-end": [final: number];
}>();

const isDragging = ref(false);

function startDrag(e: PointerEvent) {
  isDragging.value = true;
  const startPos = props.direction === "horizontal" ? e.clientX : e.clientY;
  const el = (e.target as HTMLElement).closest(".resize-split")!;
  el.setPointerCapture(e.pointerId);

  function onMove(ev: PointerEvent) {
    const currentPos =
      props.direction === "horizontal" ? ev.clientX : ev.clientY;
    const delta = currentPos - startPos;
    emit("resize", delta);
  }

  function onUp(ev: PointerEvent) {
    isDragging.value = false;
    el.releasePointerCapture(ev.pointerId);
    const finalPos =
      props.direction === "horizontal" ? ev.clientX : ev.clientY;
    emit("resize-end", finalPos - startPos);
    document.removeEventListener("pointermove", onMove as EventListener);
    document.removeEventListener("pointerup", onUp as EventListener);
  }

  document.addEventListener("pointermove", onMove as EventListener);
  document.addEventListener("pointerup", onUp as EventListener);
}
</script>

<style scoped>
.resize-split {
  position: relative;
  flex-shrink: 0;
  z-index: 2;
  background: var(--usx-color-border, #30363d);
}

.resize-split--horizontal {
  width: 4px;
  cursor: col-resize;
  min-height: 0;
  height: 100%;
}

.resize-split--vertical {
  height: 4px;
  cursor: row-resize;
  min-width: 0;
  width: 100%;
}

.resize-split__handle {
  position: absolute;
  inset: -4px;
}

.resize-split--dragging {
  background: var(--usx-color-primary, #58a6ff);
}

.resize-split:hover {
  background: var(--usx-color-primary, #58a6ff);
}
</style>
