<template>
  <div class="sonic-surface-wrapper">
    <header class="sonic-header">
      <div class="sonic-header__title-group">
        <h1 class="sonic-header__title">SonicScrewdriver</h1>
        <UBadge type="info" size="sm">USB Bootloader & Device Toolkit</UBadge>
      </div>
      <div class="sonic-header__actions">
        <a
          class="usx-btn usx-btn--sm usx-btn--secondary"
          href="https://github.com/uDosGo/SonicScrewdriver"
          target="_blank"
          title="Open SonicScrewdriver on GitHub"
        >
          <UIcon name="open_in_new" />
          <span>GitHub</span>
        </a>
      </div>
    </header>

    <div class="sonic-surface-body">
      <!-- Stats Summary -->
      <div class="sonic-summary-grid">
        <div class="sonic-stat-card">
          <div class="sonic-stat-value sonic-stat-value--info">12</div>
          <div class="sonic-stat-label">Total Events</div>
        </div>
        <div class="sonic-stat-card">
          <div class="sonic-stat-value sonic-stat-value--ok">9</div>
          <div class="sonic-stat-label">Healthy</div>
        </div>
        <div class="sonic-stat-card">
          <div class="sonic-stat-value sonic-stat-value--warn">1</div>
          <div class="sonic-stat-label">Warnings</div>
        </div>
        <div class="sonic-stat-card">
          <div class="sonic-stat-value sonic-stat-value--err">2</div>
          <div class="sonic-stat-label">Errors</div>
        </div>
      </div>

      <!-- Events Card -->
      <div class="sonic-card">
        <div class="sonic-card-header">
          <h2>Recent Spool Events</h2>
          <button class="usx-btn usx-btn--sm usx-btn--secondary" @click="refresh">
            <UIcon name="refresh" />
            <span>Refresh</span>
          </button>
        </div>
        <div class="sonic-event-list">
          <div v-for="(event, i) in events" :key="i" class="sonic-event-row">
            <span class="sonic-event-time font-mono">{{ event.timestamp.slice(0, 19) }}</span>
            <span :class="['sonic-badge', eventBadgeClass(event.level)]">{{ event.level }}</span>
            <span class="sonic-event-msg">{{ event.message }}</span>
            <span class="sonic-event-tags">
              <span v-for="tag in event.tags" :key="tag" class="sonic-tag">{{ tag }}</span>
            </span>
          </div>
        </div>
      </div>

      <!-- Module Breakdown -->
      <div class="sonic-card">
        <div class="sonic-card-header">
          <h2>Top Modules by Volume</h2>
        </div>
        <table class="sonic-table">
          <thead>
            <tr><th>Module</th><th>Events</th></tr>
          </thead>
          <tbody>
            <tr v-for="(mod, i) in moduleBreakdown" :key="i">
              <td class="sonic-module-name">{{ mod[0] }}</td>
              <td class="sonic-module-count">{{ mod[1] }}</td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Quick Links -->
      <div class="sonic-card">
        <div class="sonic-card-header">
          <h2>Quick Actions</h2>
        </div>
        <div class="sonic-actions">
          <a href="https://github.com/uDosGo/SonicScrewdriver" target="_blank" class="usx-btn usx-btn--primary">
            <UIcon name="open_in_new" />
            <span>GitHub Repository</span>
          </a>
          <span class="sonic-actions-hint">
            Full CLI tools available at <code>~/Code/SonicScrewdriver/cli/</code>
          </span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * @component SonicScrewdriverSurface
 * @description uCore surface for SonicScrewdriver — USB bootloader & device toolkit.
 * @category surfaces
 * @usage Routed at '/sonic'
 */
import { ref, computed } from 'vue'
import UIcon from '../../skills/atoms/UIcon.vue'
import UBadge from '../../skills/atoms/UBadge.vue'

interface SpoolEvent {
  timestamp: string
  module: string
  level: string
  message: string
  tags: string[]
}

const events = ref<SpoolEvent[]>([
  { timestamp: "2026-07-12T19:20:00+08:00", module: "sonic.usb", level: "INFO",  message: "USB create completed successfully for /dev/sdb", tags: ["usb", "create", "success"] },
  { timestamp: "2026-07-12T19:19:55+08:00", module: "sonic.usb", level: "INFO",  message: "Installing SonicScrewloader to ESP", tags: ["usb", "bootloader", "install"] },
  { timestamp: "2026-07-12T19:19:50+08:00", module: "sonic.usb", level: "INFO",  message: "Formatting partitions", tags: ["usb", "format", "lifecycle"] },
  { timestamp: "2026-07-12T19:19:45+08:00", module: "sonic.usb", level: "INFO",  message: "Partitioning drive (ESP + ext4 + exFAT)", tags: ["usb", "partition", "lifecycle"] },
  { timestamp: "2026-07-12T19:19:40+08:00", module: "sonic.usb", level: "INFO",  message: "USB create requested for /dev/sdb", tags: ["usb", "create", "lifecycle"] },
  { timestamp: "2026-07-12T18:45:10+08:00", module: "sonic.bootloader", level: "INFO", message: "Bootloader installed to /dev/sdc:\\EFI\\sonic", tags: ["bootloader", "install", "success"] },
  { timestamp: "2026-07-12T18:44:55+08:00", module: "sonic.bootloader", level: "INFO", message: "Bootloader install requested: device=/dev/sdc", tags: ["bootloader", "install", "lifecycle"] },
  { timestamp: "2026-07-12T17:30:00+08:00", module: "sonic.security", level: "INFO", message: "Device enrolled: type=fido2", tags: ["security", "enroll", "success"] },
  { timestamp: "2026-07-12T16:15:00+08:00", module: "sonic.diagnostics", level: "INFO", message: "Health check complete (healthy=true)", tags: ["diagnostics", "health", "completed"] },
  { timestamp: "2026-07-12T16:14:00+08:00", module: "sonic.mint", level: "INFO", message: "Mint ISO build completed: sonic-mint.iso", tags: ["mint", "build", "success"] },
  { timestamp: "2026-07-12T15:00:00+08:00", module: "sonic.device", level: "WARNING", message: "Device repurpose: router-001 -> openwrt", tags: ["device", "repurpose", "lifecycle"] },
  { timestamp: "2026-07-12T14:30:00+08:00", module: "skills-mcp", level: "ERROR", message: "MCP tool failed: sonic.device.flash (120ms)", tags: ["mcp", "skill", "execution", "failed"] },
])

const moduleBreakdown = computed(() => {
  const map: Record<string, number> = {}
  events.value.forEach(e => {
    map[e.module] = (map[e.module] || 0) + 1
  })
  return Object.entries(map).sort((a, b) => b[1] - a[1])
})

function eventBadgeClass(level: string) {
  switch (level) {
    case 'ERROR': case 'CRITICAL': return 'sonic-badge--error'
    case 'WARNING': return 'sonic-badge--warning'
    default: return 'sonic-badge--info'
  }
}

function refresh() {
  events.value = [...events.value]
}
</script>

<style scoped>
.sonic-surface-wrapper {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: var(--usx-color-background);
  color: var(--usx-color-on-surface);
  overflow: hidden;
}

.sonic-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--usx-spacing-sm) var(--usx-spacing-md);
  background: var(--usx-color-surface);
  border-bottom: var(--usx-border-width) solid var(--usx-color-border);
  flex-shrink: 0;
}

.sonic-header__title-group {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-sm);
}

.sonic-header__title {
  font-size: var(--usx-font-size-xl);
  font-weight: 600;
  margin: 0;
  color: var(--usx-color-on-surface);
}

.sonic-header__actions {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-xs);
}

.sonic-surface-body {
  flex: 1;
  overflow-y: auto;
  padding: var(--usx-spacing-xl);
  display: flex;
  flex-direction: column;
  gap: var(--usx-spacing-md);
}

/* Stats Grid */
.sonic-summary-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: var(--usx-spacing-md);
}

.sonic-stat-card {
  background: var(--usx-color-surface);
  border: var(--usx-border-width) solid var(--usx-color-border);
  border-radius: var(--usx-radius-md);
  padding: var(--usx-spacing-lg);
  text-align: center;
}

.sonic-stat-value {
  font-size: 32px;
  font-weight: var(--usx-font-weight-bold);
  margin-bottom: var(--usx-spacing-xs);
}

.sonic-stat-label {
  font-size: var(--usx-font-size-caption);
  color: var(--usx-color-on-surface-muted);
  text-transform: uppercase;
}

.sonic-stat-value--info { color: var(--usx-color-info); }
.sonic-stat-value--ok   { color: var(--usx-color-success); }
.sonic-stat-value--warn { color: var(--usx-color-warning); }
.sonic-stat-value--err  { color: var(--usx-color-danger); }

/* Cards */
.sonic-card {
  background: var(--usx-color-surface);
  border: var(--usx-border-width) solid var(--usx-color-border);
  border-radius: var(--usx-radius-md);
  padding: var(--usx-spacing-lg);
}

.sonic-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--usx-spacing-md);
  padding-bottom: var(--usx-spacing-md);
  border-bottom: var(--usx-border-width) solid var(--usx-color-border);
}

.sonic-card-header h2 {
  font-size: var(--usx-font-size-base);
  font-weight: var(--usx-font-weight-bold);
  margin: 0;
}

.sonic-btn {
  background: var(--usx-color-primary);
  color: var(--usx-color-on-primary);
  border: none;
  border-radius: var(--usx-radius-sm);
  padding: var(--usx-spacing-xs) var(--usx-spacing-md);
  font-size: var(--usx-font-size-sm);
  font-family: inherit;
  cursor: pointer;
  text-decoration: none;
  display: inline-flex;
  align-items: center;
  gap: var(--usx-spacing-xs);
}

.sonic-btn:hover { opacity: 0.85; }

/* Events */
.sonic-event-row {
  display: grid;
  grid-template-columns: 140px 70px 1fr 120px;
  gap: var(--usx-spacing-md);
  align-items: center;
  padding: var(--usx-spacing-xs) 0;
  border-bottom: 1px solid var(--usx-color-border);
  font-size: var(--usx-font-size-sm);
}

.sonic-event-time { color: var(--usx-color-on-surface-muted); }
.sonic-event-msg  { color: var(--usx-color-on-surface); }

.sonic-event-tags {
  display: flex;
  gap: var(--usx-spacing-xs);
  flex-wrap: wrap;
}

.sonic-tag {
  background: var(--usx-color-surface-variant);
  color: var(--usx-color-on-surface-muted);
  padding: 1px var(--usx-spacing-sm);
  border-radius: var(--usx-radius-sm);
  font-size: 10px;
  text-transform: uppercase;
}

.sonic-badge {
  padding: 2px var(--usx-spacing-sm);
  border-radius: var(--usx-radius-sm);
  font-size: 10px;
  font-weight: var(--usx-font-weight-bold);
  text-transform: uppercase;
  text-align: center;
}

.sonic-badge--info    { background: var(--usx-color-info); color: var(--usx-color-on-info); }
.sonic-badge--warning { background: var(--usx-color-warning); color: #000; }
.sonic-badge--error   { background: var(--usx-color-danger); color: var(--usx-color-on-danger); }

/* Table */
.sonic-table {
  width: 100%;
  border-collapse: collapse;
  font-size: var(--usx-font-size-sm);
}

.sonic-table th {
  text-align: left;
  padding: var(--usx-spacing-xs) var(--usx-spacing-md);
  border-bottom: var(--usx-border-width) solid var(--usx-color-border);
  color: var(--usx-color-on-surface-muted);
  font-weight: var(--usx-font-weight-bold);
  font-size: var(--usx-font-size-caption);
  text-transform: uppercase;
}

.sonic-table td {
  padding: var(--usx-spacing-xs) var(--usx-spacing-md);
  border-bottom: var(--usx-border-width) solid var(--usx-color-border);
}

.sonic-module-name  { color: var(--usx-color-primary); font-weight: var(--usx-font-weight-bold); }
.sonic-module-count { color: var(--usx-color-on-surface); font-weight: var(--usx-font-weight-bold); }

.sonic-actions {
  display: flex;
  align-items: center;
  gap: var(--usx-spacing-md);
}

.sonic-actions-hint {
  font-size: var(--usx-font-size-sm);
  color: var(--usx-color-on-surface-muted);
}

.sonic-actions-hint code {
  background: var(--usx-color-surface-variant);
  padding: 2px var(--usx-spacing-sm);
  border-radius: var(--usx-radius-sm);
}
</style>