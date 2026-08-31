import { beforeEach, describe, expect, it, vi } from "vitest";
import { createPinia, setActivePinia } from "pinia";
import { getEditorSurface } from "../composables/useEditorSurface";
import { useWorkspaceStore } from "./workspace";

describe("workspace store", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    const values = new Map<string, string>();
    vi.stubGlobal("localStorage", {
      getItem: (key: string) => values.get(key) ?? null,
      setItem: (key: string, value: string) => values.set(key, value),
      removeItem: (key: string) => values.delete(key),
      clear: () => values.clear(),
    });
    setActivePinia(createPinia());
    getEditorSurface().closeEditor();
  });

  it("loads the persistent tree and opens file content", async () => {
    const node = { id: "Notes/Today.md", name: "Today.md", type: "file" as const, path: "/Notes/Today.md", extension: "md" };
    vi.stubGlobal("fetch", vi.fn()
      .mockResolvedValueOnce(new Response(JSON.stringify({ tree: [node] }), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify({ path: node.path, content: "# Today\n" }), { status: 200 })));
    const store = useWorkspaceStore();

    await store.loadTree();
    await store.selectFile(store.tree[0]);

    expect(store.selectedId).toBe(node.id);
    expect(getEditorSurface().content.value).toBe("# Today\n");
  });

  it("persists edited content and refreshes the tree", async () => {
    const fetchMock = vi.fn()
      .mockResolvedValueOnce(new Response(JSON.stringify({ ok: true, path: "/Today.md" }), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify({ tree: [] }), { status: 200 }));
    vi.stubGlobal("fetch", fetchMock);
    const store = useWorkspaceStore();

    await store.saveFile("/Today.md", "Updated");

    expect(fetchMock).toHaveBeenNthCalledWith(1, expect.stringContaining("/api/editor/files"), expect.objectContaining({ method: "PUT" }));
    expect(store.error).toBe("");
  });

  it("queues a save while offline", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new TypeError("offline")));
    const store = useWorkspaceStore();

    const saved = await store.saveFile("/Today.md", "Offline update");

    expect(saved).toBe(false);
    expect(store.error).toContain("queued");
    expect(localStorage.getItem("ucore-workspace-save-queue")).toContain("Offline update");
  });

  it("surfaces conflicts without queueing the stale write", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ error: "file changed", conflict: true }), { status: 409 }),
    ));
    const store = useWorkspaceStore();

    await expect(store.saveFile("/Today.md", "Stale update")).rejects.toThrow("file changed");
    expect(store.error).toContain("conflict");
    expect(localStorage.getItem("ucore-workspace-save-queue")).toBeNull();
  });

  it("replays an offline save with its original version", async () => {
    localStorage.setItem("ucore-workspace-save-queue", JSON.stringify([
      { path: "/Today.md", content: "Queued", version: "original-version" },
    ]));
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ ok: true, version: "saved-version" }), { status: 200 }),
    );
    vi.stubGlobal("fetch", fetchMock);
    const store = useWorkspaceStore();

    await store.flushSaveQueue();

    const request = JSON.parse(String((fetchMock.mock.calls[0][1] as RequestInit).body));
    expect(request.version).toBe("original-version");
    expect(localStorage.getItem("ucore-workspace-save-queue")).toBe("[]");
  });
});
