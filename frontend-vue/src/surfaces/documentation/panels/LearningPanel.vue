<template>
  <div class="wf-panel">
    <div class="wf-toolbar">
      <span class="wf-toolbar__count">
        <UIcon name="school" />
        Learning
      </span>
      <span class="wf-toolbar__count">{{ courses.length }} courses</span>
    </div>

    <div v-if="loading" class="wf-loading">
      <UIcon name="sync" /> Loading courses...
    </div>

    <div v-else-if="courses.length === 0" class="wf-empty">
      No courses indexed. Run a documentation scan to populate.
    </div>

    <div v-else class="learning-grid">
      <div v-for="course in courses" :key="course.path" class="learning-card">
        <div class="learning-card__icon">
          <UIcon :name="levelIcon(course.level)" />
        </div>
        <div class="learning-card__body">
          <span class="learning-card__title">{{
            course.title || course.name
          }}</span>
          <span class="learning-card__path">{{ course.path }}</span>
          <div class="learning-card__pills">
            <span
              class="task-pill"
              :class="`task-pill--${relevanceClass(course.relevance)}`"
            >
              {{ course.relevance }}%
            </span>
            <span class="task-pill task-pill--board">{{
              course.level || "all"
            }}</span>
            <span v-if="course.category" class="task-pill task-pill--tag">{{
              course.category
            }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from "vue";
import UIcon from "../../../skills/atoms/UIcon.vue";
import { SNACKBAR_BASE } from "../../../api/base";

interface Course {
  title?: string;
  name: string;
  path: string;
  level: string;
  relevance: number;
  category?: string;
}

const courses = ref<Course[]>([]);
const loading = ref(true);

function levelIcon(level: string): string {
  if (level === "advanced") return "stars";
  if (level === "average") return "trending_up";
  return "school";
}

function relevanceClass(relevance: number): string {
  if (relevance >= 90) return "completed";
  if (relevance >= 60) return "review";
  return "blocked";
}

async function loadCourses() {
  loading.value = true;
  try {
    const res = await fetch(`${SNACKBAR_BASE}/api/docs/courses`);
    if (res.ok) {
      const data = await res.json();
      courses.value = data.courses || data || [];
    }
  } catch {
    courses.value = [];
  } finally {
    loading.value = false;
  }
}

onMounted(loadCourses);
</script>

<style scoped>
.wf-panel {
  display: flex;
  flex-direction: column;
  gap: var(--usx-spacing-md);
}

.wf-loading,
.wf-empty {
  padding: var(--usx-spacing-md);
  color: var(--usx-color-on-surface-muted);
  font-size: var(--usx-font-size-sm);
  text-align: center;
}

.learning-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(28ch, 1fr));
  gap: var(--usx-spacing-sm);
}

.learning-card {
  display: flex;
  gap: var(--usx-spacing-sm);
  padding: var(--usx-spacing-md);
  background: var(--usx-color-surface);
  border-radius: var(--usx-radius-md);
  border: var(--usx-border-width) solid var(--usx-color-border);
}

.learning-card__icon {
  flex-shrink: 0;
  color: var(--usx-color-primary);
}

.learning-card__body {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: var(--usx-spacing-xs);
}

.learning-card__title {
  font-weight: var(--usx-font-weight-semibold);
  font-size: var(--usx-font-size-sm);
}

.learning-card__path {
  font-family: var(--usx-font-family-mono);
  font-size: var(--usx-font-size-xs);
  color: var(--usx-color-on-surface-muted);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.learning-card__pills {
  display: flex;
  gap: var(--usx-spacing-xs);
  flex-wrap: wrap;
}

.task-pill {
  display: inline-flex;
  align-items: center;
  padding: 1px var(--usx-spacing-xs);
  border-radius: var(--usx-radius-sm);
  font-size: var(--usx-font-size-xs);
  font-weight: var(--usx-font-weight-medium);
  line-height: 1.4;
  white-space: nowrap;
  border: var(--usx-border-width) solid transparent;
}

.task-pill--completed {
  color: var(--usx-color-success);
  background: color-mix(in srgb, var(--usx-color-success) 10%, transparent);
}
.task-pill--review {
  color: var(--usx-color-warning);
  background: color-mix(in srgb, var(--usx-color-warning) 10%, transparent);
}
.task-pill--blocked {
  color: var(--usx-color-danger);
  background: color-mix(in srgb, var(--usx-color-danger) 8%, transparent);
}
.task-pill--board {
  color: var(--usx-color-on-surface-muted);
  background: var(--usx-color-surface-variant);
}
.task-pill--tag {
  color: var(--usx-color-info);
  background: color-mix(in srgb, var(--usx-color-info) 8%, transparent);
}
</style>
