import { beforeEach, describe, expect, it, vi } from "vitest";
import { createPinia, setActivePinia } from "pinia";
import { getEditorSurface } from "../composables/useEditorSurface";
import { useWorkspaceStore } from "./workspace";

describe("workspace store", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    getEditorSurface().closeEditor();
    vi.restoreAllMocks();
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
});
