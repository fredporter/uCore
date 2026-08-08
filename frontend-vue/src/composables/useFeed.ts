/**
 * @module composables/useFeed
 * @description SSE composable for real-time skill/system events from /api/render/stream.
 * Gracefully degrades when the backend is offline.
 */
import { ref, onMounted, onBeforeUnmount } from "vue";
import { SNACKBAR_BASE } from "../api/base";

export interface FeedEvent {
  type: string;
  data: Record<string, unknown>;
  timestamp: string;
}

export function useFeed() {
  const events = ref<FeedEvent[]>([]);
  const isConnected = ref(false);
  const error = ref<string | null>(null);

  let source: EventSource | null = null;
  let reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  let destroyed = false;

  function connect() {
    if (source) return;
    try {
      source = new EventSource(`${SNACKBAR_BASE}/api/render/stream`);

      source.addEventListener("connected", () => {
        isConnected.value = true;
        error.value = null;
      });

      // Generic event listener for all typed events
      const KNOWN_EVENTS = [
        "skill_start",
        "skill_complete",
        "skill_error",
        "progress",
        "toast",
        "alert",
        "event",
      ];

      for (const type of KNOWN_EVENTS) {
        source.addEventListener(type, (e: MessageEvent) => {
          try {
            const data = JSON.parse(e.data);
            events.value.push({
              type,
              data,
              timestamp: new Date().toISOString(),
            });
            // Keep last 100 events
            if (events.value.length > 100) events.value.shift();
          } catch {
            // malformed event — skip
          }
        });
      }

      source.onerror = () => {
        isConnected.value = false;
        source?.close();
        source = null;
        // Reconnect after 5 s if not destroyed
        if (!destroyed) {
          reconnectTimer = setTimeout(connect, 5000);
        }
      };
    } catch {
      error.value = "SSE not supported or backend unavailable";
    }
  }

  function disconnect() {
    destroyed = true;
    if (reconnectTimer) clearTimeout(reconnectTimer);
    source?.close();
    source = null;
    isConnected.value = false;
  }

  function clearEvents() {
    events.value = [];
  }

  /** Get events filtered by type */
  function eventsOfType(type: string) {
    return events.value.filter((e) => e.type === type);
  }

  onMounted(connect);
  onBeforeUnmount(disconnect);

  return { events, isConnected, error, connect, disconnect, clearEvents, eventsOfType };
}
