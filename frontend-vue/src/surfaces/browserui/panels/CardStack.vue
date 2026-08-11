/**
 * @component CardStack — Sortable card grid with quality scores and tag filters.
 */
<template>
  <div class="card-stack">
    <div class="card-stack__header">
      <h3>{{ title }}</h3>
      <span v-if="selectedIds.length > 0" class="card-stack__selected-count">{{ selectedIds.length }} selected</span>
      <div v-if="tagFilter" class="card-stack__filters">
        <button v-for="tag in availableTags" :key="tag"
          class="card-stack__filter-chip"
          :class="{ 'card-stack__filter-chip--active': localActiveTag === tag }"
          @click="localActiveTag = localActiveTag === tag ? '' : tag">{{ tag }}</button>
        <select v-model="localSortBy" class="card-stack__sort">
          <option value="default">Sort: Default</option>
          <option value="score-desc">Highest Score</option>
          <option value="score-asc">Lowest Score</option>
          <option value="name">Name</option>
        </select>
      </div>
    </div>
    <div v-if="sortedCards.length === 0" class="card-stack__empty">
      <UIcon name="inbox" /><span>No cards</span>
    </div>
    <div class="card-stack__grid">
      <div v-for="card in sortedCards" :key="card.id"
        class="card-stack__card"
        :class="{ 'card-stack__card--active': activeId === card.id }"
        @click.self="$emit('select', card)">
        <div class="card-stack__card-top">
          <input type="checkbox" class="card-stack__check"
            :checked="selectedIds.includes(card.id)"
            @change="toggleSelect(card.id, $event)"
          />
          <span class="card-stack__score" :class="scoreClass(card.score)">{{ card.score ?? '-' }}</span>
          <span class="card-stack__title">{{ card.title }}</span>
        </div>
        <div class="card-stack__desc">{{ card.description }}</div>
        <div class="card-stack__tags">
          <span v-for="t in card.tags" :key="t" class="card-stack__tag">{{ t }}</span>
        </div>
        <div class="card-stack__actions">
          <button class="uxs-btn uxs-btn--sm" @click.stop="$emit('research', card)">Research</button>
          <button class="uxs-btn uxs-btn--sm" @click.stop="$emit('enhance', card)">Enhance</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from "vue"
import UIcon from "../../../skills/atoms/UIcon.vue"

export interface StackCard {
  id: string; title: string; description: string;
  url?: string; tags: string[]; score?: number; binder?: string;
}

const props = defineProps<{
  title: string; cards: StackCard[]; activeId?: string;
  tagFilter?: boolean;
}>()

const emit = defineEmits<{
  select: [card: StackCard]
  research: [card: StackCard]
  enhance: [card: StackCard]
}>()

const localActiveTag = ref("")
const localSortBy = ref("default")
const selectedIds = ref<string[]>([])

function toggleSelect(id: string, event: Event) {
  const checked = (event.target as HTMLInputElement).checked
  if (checked) selectedIds.value = [...selectedIds.value, id]
  else selectedIds.value = selectedIds.value.filter(i => i !== id)
}

const availableTags = computed(() => {
  const t = new Set<string>()
  for (const c of props.cards) for (const tag of c.tags) t.add(tag)
  return [...t].sort()
})

const sortedCards = computed(() => {
  let c = [...props.cards]
  if (localActiveTag.value) c = c.filter(x => x.tags.includes(localActiveTag.value))
  const s = localSortBy.value || "default"
  if (s === "score-desc") c.sort((a, b) => (b.score || 0) - (a.score || 0))
  else if (s === "score-asc") c.sort((a, b) => (a.score || 0) - (b.score || 0))
  else if (s === "name") c.sort((a, b) => a.title.localeCompare(b.title))
  return c
})

function scoreClass(s: number | undefined): string {
  if (s === undefined) return "card-stack__score--none"
  if (s >= 4) return "card-stack__score--high"
  if (s >= 2) return "card-stack__score--mid"
  return "card-stack__score--low"
}
</script>

<style scoped>
.card-stack { margin-bottom: var(--usx-spacing-lg); }
.card-stack__header {
  display: flex; align-items: center; gap: var(--usx-spacing-md);
  margin-bottom: var(--usx-spacing-sm); flex-wrap: wrap;
}
.card-stack__header h3 { margin: 0; font-size: var(--usx-font-size-lg); }
.card-stack__selected-count {
  font-size: var(--usx-font-size-xs); color: var(--usx-color-primary);
  background: color-mix(in srgb, var(--usx-color-primary) 15%, transparent);
  padding: 2px var(--usx-spacing-sm); border-radius: var(--usx-radius-sm);
  font-weight: 600;
}
.card-stack__filters { display: flex; gap: var(--usx-spacing-xs); align-items: center; flex-wrap: wrap; }
.card-stack__filter-chip {
  font-size: var(--usx-font-size-xs); padding: 2px var(--usx-spacing-sm);
  border-radius: var(--usx-radius-sm); border: 1px solid var(--usx-color-border);
  background: var(--usx-color-surface); cursor: pointer;
}
.card-stack__filter-chip--active { background: var(--usx-color-primary); color: var(--usx-color-on-primary); }
.card-stack__sort { font-size: var(--usx-font-size-xs); padding: 2px var(--usx-spacing-sm); border-radius: var(--usx-radius-sm); border: 1px solid var(--usx-color-border); }
.card-stack__empty { display: flex; align-items: center; gap: var(--usx-spacing-sm); padding: var(--usx-spacing-lg); color: var(--usx-color-on-surface-muted); }
.card-stack__grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: var(--usx-spacing-md); }
.card-stack__card {
  padding: var(--usx-spacing-md); border: 1px solid var(--usx-color-border);
  border-radius: var(--usx-radius-md); cursor: pointer;
  background: var(--usx-color-surface);
  transition: border-color var(--usx-transition-fast), box-shadow var(--usx-transition-fast);
}
.card-stack__card:hover {
  border-color: var(--usx-color-primary);
  box-shadow: 0 2px 8px color-mix(in srgb, var(--usx-color-primary) 15%, transparent);
}
.card-stack__card--active { border-color: var(--usx-color-primary); background: color-mix(in srgb, var(--usx-color-primary) 6%, transparent); }
.card-stack__card-top { display: flex; align-items: center; gap: var(--usx-spacing-sm); margin-bottom: var(--usx-spacing-xs); }
.card-stack__check { width: 16px; height: 16px; accent-color: var(--usx-color-primary); cursor: pointer; flex-shrink: 0; }
.card-stack__score {
  font-size: var(--usx-font-size-xs); font-weight: 700; min-width: 28px;
  text-align: center; padding: 2px 6px; border-radius: var(--usx-radius-sm);
}
.card-stack__score--high { background: var(--usx-color-success); color: var(--usx-color-on-success); }
.card-stack__score--mid { background: var(--usx-color-warning); color: var(--usx-color-on-warning); }
.card-stack__score--low { background: var(--usx-color-danger); color: var(--usx-color-on-danger); }
.card-stack__score--none { background: var(--usx-color-surface-variant); color: var(--usx-color-on-surface-muted); }
.card-stack__title { font-weight: 600; font-size: var(--usx-font-size-base); overflow: hidden; text-overflow: ellipsis; }
.card-stack__desc {
  font-size: var(--usx-font-size-sm); color: var(--usx-color-on-surface-muted);
  margin-bottom: var(--usx-spacing-sm); display: -webkit-box; -webkit-line-clamp: 2;
  -webkit-box-orient: vertical; overflow: hidden;
}
.card-stack__tags { display: flex; gap: var(--usx-spacing-xs); flex-wrap: wrap; margin-bottom: var(--usx-spacing-sm); }
.card-stack__tag {
  font-size: var(--usx-font-size-xs); padding: 1px var(--usx-spacing-xs);
  border-radius: var(--usx-radius-sm); background: var(--usx-color-surface-variant);
  color: var(--usx-color-on-surface-muted);
}
.card-stack__actions { display: flex; gap: var(--usx-spacing-xs); }
.uxs-btn {
  display: inline-flex; align-items: center; gap: var(--usx-spacing-xs);
  border: 1px solid var(--usx-color-border); border-radius: var(--usx-radius-sm);
  padding: 4px var(--usx-spacing-sm); cursor: pointer;
  background: var(--usx-color-surface); font-size: var(--usx-font-size-xs);
  color: var(--usx-color-on-surface); white-space: nowrap;
}
.uxs-btn:hover { background: var(--usx-color-surface-hover); }
.uxs-btn--sm { font-size: var(--usx-font-size-xs); padding: 3px var(--usx-spacing-sm); }
</style>
