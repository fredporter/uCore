<template>
  <div class="sonic-surface-wrapper">
    <header class="sonic-header">
      <div class="sonic-header__title-group">
        <h1 class="sonic-header__title">SonicScrewdriver</h1>
        <p>USB bootloader and device toolkit</p>
      </div>
      <div class="sonic-header__actions">
        <a
          class="usx-btn usx-btn--sm usx-btn--secondary"
          href="https://github.com/uDosGo/SonicScrewdriver"
          target="_blank"
          rel="noopener noreferrer"
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
          <h2>Sample Spool events</h2>
        </div>
        <div class="sonic-event-list">
          <div v-for="(event, i) in events" :key="i" class="sonic-event-row">
            <time class="sonic-event-time" :datetime="event.timestamp">{{ event.timestamp.slice(0, 19).replace("T", " ") }}</time>
            <UBadge :type="eventBadgeType(event.level)" size="sm">{{ event.level }}</UBadge>
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

      <p class="sonic-cli-hint">CLI tools are available in <code>~/Code/SonicScrewdriver/cli/</code>.</p>
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
import UIcon from '../../skills/atoms/UIcon.vue'
import UBadge from '../../skills/atoms/UBadge.vue'

interface SpoolEvent {
  timestamp: string
  module: string
  level: string
  message: string
  tags: string[]
}

const events: SpoolEvent[] = [
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
]

const moduleBreakdown = (() => {
  const map: Record<string, number> = {}
  events.forEach(e => {
    map[e.module] = (map[e.module] || 0) + 1
  })
  return Object.entries(map).sort((a, b) => b[1] - a[1])
})()

function eventBadgeType(level: string) {
  switch (level) {
    case 'ERROR': case 'CRITICAL': return 'error'
    case 'WARNING': return 'warning'
    default: return 'info'
  }
}
</script>

<style scoped>
.sonic-surface-wrapper {
  display: flex;
  flex-direction: column;
  height: 100%;
  min-width: 0;
  overflow: auto;
  background: var(--usx-color-background);
  color: var(--usx-color-on-surface);
  font-family: var(--usx-font-family-sans);
}

.sonic-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: var(--usx-spacing-sm);
  padding: var(--usx-spacing-md);
  border-block-end: var(--usx-border-width) solid var(--usx-color-border);
}

.sonic-header__title-group {
  display: grid;
  gap: var(--usx-spacing-xs);
  min-width: 0;
  overflow-wrap: anywhere;
}

.sonic-header__title {
  font-size: var(--usx-font-size-xl);
  font-weight: var(--usx-font-weight-semibold);
}

.sonic-header__title,
.sonic-header p,
.sonic-card-header h2,
.sonic-cli-hint {
  margin: 0;
}

.sonic-header .usx-btn {
  display: inline-flex;
  align-items: center;
  gap: var(--usx-icon-gap);
  min-block-size: var(--usx-touch-min);
  padding: var(--usx-spacing-xs) var(--usx-spacing-sm);
  border: var(--usx-border-width) solid var(--usx-color-border);
  border-radius: var(--usx-radius-sm);
  background: var(--usx-color-surface);
  color: var(--usx-color-on-surface);
  font-size: var(--usx-font-size-sm);
  text-decoration: none;
  box-sizing: border-box;
}

.sonic-header .usx-btn:hover {
  border-color: var(--usx-color-primary);
}

.sonic-header .usx-btn:focus-visible {
  outline: 2px solid var(--usx-color-primary);
  outline-offset: 2px;
}

.sonic-surface-body,
.sonic-summary-grid,
.sonic-card {
  display: grid;
  gap: var(--usx-spacing-md);
  min-width: 0;
}

.sonic-surface-body { padding: var(--usx-spacing-md); }

.sonic-summary-grid {
  grid-template-columns: repeat(auto-fit, minmax(min(100%, 7rem), 1fr));
}

.sonic-stat-card,
.sonic-card {
  padding: var(--usx-spacing-md);
  border: var(--usx-border-width) solid var(--usx-color-border);
  border-radius: var(--usx-radius-sm);
  background: var(--usx-color-surface);
}

.sonic-stat-card { display: grid; gap: var(--usx-spacing-xs); }

.sonic-stat-value {
  font-size: var(--usx-font-size-xl);
  font-weight: var(--usx-font-weight-bold);
  font-variant-numeric: tabular-nums;
}

.sonic-header p,
.sonic-stat-label,
.sonic-event-time,
.sonic-cli-hint {
  color: var(--usx-color-on-surface-muted);
  font-size: var(--usx-font-size-sm);
}

.sonic-stat-value--info { color: var(--usx-color-info); }
.sonic-stat-value--ok { color: var(--usx-color-success); }
.sonic-stat-value--warn { color: var(--usx-color-warning); }
.sonic-stat-value--err { color: var(--usx-color-danger); }

.sonic-card-header h2 {
  font-size: var(--usx-font-size-base);
  font-weight: var(--usx-font-weight-semibold);
}

.sonic-event-row {
  display: grid;
  grid-template-columns: max-content max-content minmax(0, 1fr) minmax(0, 9rem);
  align-items: start;
  gap: var(--usx-spacing-sm);
  padding-block: var(--usx-spacing-sm);
  border-block-start: var(--usx-border-width) solid var(--usx-color-border);
  font-size: var(--usx-font-size-sm);
  overflow-wrap: anywhere;
}

.sonic-event-time { font-variant-numeric: tabular-nums; }

.sonic-event-tags {
  display: flex;
  flex-wrap: wrap;
  gap: var(--usx-spacing-xs);
}

.sonic-tag {
  padding: var(--usx-spacing-1) var(--usx-spacing-xs);
  border-radius: var(--usx-radius-sm);
  background: var(--usx-color-surface-variant);
  color: var(--usx-color-on-surface-muted);
  font-size: var(--usx-font-size-xs);
}

.sonic-table {
  width: 100%;
  border-collapse: collapse;
  font-size: var(--usx-font-size-sm);
  overflow-wrap: anywhere;
}

.sonic-table :is(th, td) {
  padding: var(--usx-spacing-sm);
  border-block-start: var(--usx-border-width) solid var(--usx-color-border);
  text-align: start;
}

.sonic-table :is(th, td):last-child {
  text-align: end;
  font-variant-numeric: tabular-nums;
}

.sonic-cli-hint { overflow-wrap: anywhere; }

@media (max-width: 720px) {
  .sonic-event-row {
    grid-template-columns: minmax(0, 1fr) auto;
    align-items: center;
  }

  .sonic-event-msg,
  .sonic-event-tags {
    grid-column: 1 / -1;
  }
}
</style>
