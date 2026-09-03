// @vitest-environment jsdom
import { createPinia, setActivePinia } from "pinia";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { useChatStore } from "./chat";

describe("chat history persistence", () => {
  beforeEach(() => {
    localStorage.clear();
    setActivePinia(createPinia());
  });

  it("restores the newest server conversation", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: true, json: async () => ({ conversations: [{ id: "one", title: "Saved", model: "auto", createdAt: "2026-01-01", updatedAt: "2026-01-02", messages: [{ id: "m", role: "user", content: "restored", timestamp: "2026-01-01" }] }] }) }));
    const store = useChatStore();
    await store.restoreHistory();
    expect(store.activeConversation).toBe("one");
    expect(store.messages[0].content).toBe("restored");
    expect(store.historySynced).toBe(true);
  });

  it("clears local and server history", async () => {
    const fetchMock = vi.fn().mockResolvedValue({ ok: true });
    vi.stubGlobal("fetch", fetchMock);
    const store = useChatStore();
    await store.clearHistory();
    expect(store.conversations).toEqual([]);
    expect(fetchMock).toHaveBeenCalledWith(expect.stringContaining("/api/chat/history"), expect.objectContaining({ method: "DELETE" }));
  });
});
