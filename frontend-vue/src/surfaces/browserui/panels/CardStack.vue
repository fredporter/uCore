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
        @click="$emit('select', card)">
        <div class="card-stack__card-top">
          <input type="checkbox" class="card-stack__check"
            :checked="selectedIds.includes(card.id)"
            @click.stop @change="toggleSelect(card.id, $event)"
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
