,<template>
  <div class="surface">
    <div class="surface__content">
      <section class="surface__panel">
        <h3 class="surface__panel-title">Example Panel</h3>
        <p class="surface__panel-description">
          Replace this with your panel content.
        </p>
      </section>

      <div class="example-stats">
        <div class="example-stat">
          <span class="example-stat__value">0</span>
          <span class="example-stat__label">Items</span>
        </div>
      </div>

      <div class="example-section">
        <h4 class="example-section__title">Section</h4>
        <p>Content goes here.</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
// Your component logic
</script>

<style scoped>
.example-stats {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(10rem, 1fr));
  gap: var(--usx-spacing-md);
}
.example-stat {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--usx-spacing-xs);
  padding: var(--usx-spacing-lg);
  background: var(--usx-color-surface);
  border: var(--usx-border-width) solid var(--usx-color-border);
  border-radius: var(--usx-radius-lg);
}
.example-stat__value {
  font-size: var(--usx-font-size-2xl);
  font-weight: var(--usx-font-weight-bold);
}
.example-stat__label {
  font-size: var(--usx-font-size-base);
  color: var(--usx-color-on-surface-muted);
}
.example-section {
  display: flex;
  flex-direction: column;
  gap: var(--usx-spacing-sm);
  padding: var(--usx-spacing-md);
  background: var(--usx-color-surface);
  border: var(--usx-border-width) solid var(--usx-color-border);
  border-radius: var(--usx-radius-lg);
  box-shadow: 0 var(--usx-border-width-thick) 0
    color-mix(in srgb, var(--usx-color-border) 35%, transparent);
}
.example-section__title {
  margin: 0;
  font-size: var(--usx-font-size-base);
  font-weight: var(--usx-font-weight-semibold);
  color: var(--usx-color-on-surface-muted);
  text-transform: uppercase;
  letter-spacing: var(--usx-letter-spacing-wide);
}
</style>
/**
 * @component ExamplePanel
 * @description Example panel for {{cookiecutter.surface_id}} surface.
 * Generated from surface-basic plate template.
 * Uses USX surface panel classes from usx-standard.css.
 * @category panels
 */
</script>

<style scoped>
/* Panel-specific overrides only */
</style>
