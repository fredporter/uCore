/**
 * @module stores/workspace
 * @description Workspace file tree state — folders, files, selection, expansion.
 */
import { ref, computed } from "vue";
import { defineStore } from "pinia";
import { getEditorSurface } from "../composables/useEditorSurface";
import { UCORE_BASE } from "../api/base";

export interface FileNode {
  id: string;
  name: string;
  type: "file" | "folder";
  path: string;
  extension?: string;
  children?: FileNode[];
  content?: string;
}

const EXPANSION_KEY = "ucore-workspace-expanded";

function loadExpanded(): Set<string> {
  try {
    const raw = localStorage.getItem(EXPANSION_KEY);
    return raw ? new Set(JSON.parse(raw)) : new Set(["root", "notes"]);
  } catch {
    return new Set(["root", "notes"]);
  }
}

function saveExpanded(expanded: Set<string>) {
  try {
    localStorage.setItem(EXPANSION_KEY, JSON.stringify([...expanded]));
  } catch {}
}

// Seed tree for offline/demo use — replaced by API fetch in production
const DEFAULT_TREE: FileNode[] = [
  {
    id: "notes",
    name: "Notes",
    type: "folder",
    path: "/notes",
    children: [
      {
        id: "notes-welcome",
        name: "Welcome.md",
        type: "file",
        path: "/notes/Welcome.md",
        extension: "md",
        content:
          "---\ntitle: Welcome\nstatus: published\ntags: [#intro]\n---\n\n# Welcome\n\nThis is your workspace.\n",
      },
      {
        id: "notes-scratch",
        name: "Scratch.md",
        type: "file",
        path: "/notes/Scratch.md",
        extension: "md",
        content: "# Scratch\n\nQuick notes here.\n",
      },
    ],
  },
  {
    id: "research",
    name: "Research",
    type: "folder",
    path: "/research",
    children: [
      {
        id: "research-example",
        name: "Example Research.md",
        type: "file",
        path: "/research/Example Research.md",
        extension: "md",
        content:
          "---\ntitle: Example Research\ntype: research\nsource: https://example.com\ndate: 2026-08-08\nstatus: draft\ntags: [#research]\n---\n\n# Example Research\n\nResearch content goes here.\n",
      },
    ],
  },
  {
    id: "binder",
    name: "Binder",
    type: "folder",
    path: "/binder",
    children: [],
  },
];

export const useWorkspaceStore = defineStore("workspace", () => {
  const tree = ref<FileNode[]>(DEFAULT_TREE);
  const expandedIds = ref<Set<string>>(loadExpanded());
  const selectedId = ref<string | null>(null);
  const loading = ref(false);
  const error = ref("");

  async function request(path: string, init?: RequestInit) {
    const response = await fetch(`${UCORE_BASE}${path}`, init);
    const result = await response.json();
    if (!response.ok) throw new Error(result.error || "Workspace request failed");
    return result;
  }

  async function loadTree() {
    loading.value = true;
    error.value = "";
    try {
      const result = await request("/api/editor/workspace?source=user");
      tree.value = Array.isArray(result.tree) ? result.tree : [];
    } catch (exc) {
      error.value = exc instanceof Error ? exc.message : "Workspace is unavailable";
    } finally {
      loading.value = false;
    }
  }

  const selectedFile = computed(() =>
    selectedId.value ? findNode(tree.value, selectedId.value) : null,
  );

  const breadcrumb = computed(() => {
    if (!selectedId.value) return [];
    return buildBreadcrumb(tree.value, selectedId.value, []);
  });

  function isExpanded(id: string) {
    return expandedIds.value.has(id);
  }

  function toggleFolder(id: string) {
    if (expandedIds.value.has(id)) {
      expandedIds.value.delete(id);
    } else {
      expandedIds.value.add(id);
    }
    saveExpanded(expandedIds.value);
  }

  async function selectFile(node: FileNode) {
    if (node.type !== "file") return;
    try {
      const result = await request(`/api/editor/files?source=user&path=${encodeURIComponent(node.path)}`);
      node.content = String(result.content || "");
      selectedId.value = node.id;
      getEditorSurface().openFile({
        path: node.path,
        filename: node.name,
        content: node.content,
        extension: node.extension ?? "md",
      });
    } catch (exc) {
      error.value = exc instanceof Error ? exc.message : "File could not be opened";
    }
  }

  async function createFile(parentPath: string, name: string) {
    const newNode = await mutate("POST", { parent: parentPath, name, type: "file" });
    await selectFile(newNode);
    return newNode;
  }

  async function createFolder(parentPath: string, name: string) {
    const newNode = await mutate("POST", { parent: parentPath, name, type: "folder" });
    expandedIds.value.add(newNode.id);
    saveExpanded(expandedIds.value);
    return newNode;
  }

  async function deleteNode(id: string) {
    const node = findNode(tree.value, id);
    if (!node) return;
    await mutate("DELETE", { path: node.path });
    if (selectedId.value === id) selectedId.value = null;
  }

  async function renameNode(id: string, newName: string) {
    const node = findNode(tree.value, id);
    if (node) await mutate("PUT", { path: node.path, name: newName });
  }

  async function moveNode(id: string, parent: string) {
    const node = findNode(tree.value, id);
    if (node) await mutate("PUT", { path: node.path, parent });
  }

  async function mutate(method: string, body: Record<string, unknown>): Promise<FileNode> {
    error.value = "";
    try {
      const result = await request("/api/editor/files", {
        method,
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ source: "user", ...body }),
      });
      await loadTree();
      return result as FileNode;
    } catch (exc) {
      error.value = exc instanceof Error ? exc.message : "Workspace change failed";
      throw exc;
    }
  }

  async function saveFile(path: string, content: string) {
    await mutate("PUT", { path, content });
  }

  function updateFileContent(id: string, content: string) {
    const node = findNode(tree.value, id);
    if (node && node.type === "file") node.content = content;
  }

  // ─── Helpers ────────────────────────────────────────────────────────
  function findNode(nodes: FileNode[], id: string): FileNode | null {
    for (const n of nodes) {
      if (n.id === id) return n;
      if (n.children) {
        const found = findNode(n.children, id);
        if (found) return found;
      }
    }
    return null;
  }

  function findNodeByPath(nodes: FileNode[], path: string): FileNode | null {
    for (const n of nodes) {
      if (n.path === path) return n;
      if (n.children) {
        const found = findNodeByPath(n.children, path);
        if (found) return found;
      }
    }
    return null;
  }

  function removeNode(nodes: FileNode[], id: string): FileNode[] {
    return nodes
      .filter((n) => n.id !== id)
      .map((n) =>
        n.children ? { ...n, children: removeNode(n.children, id) } : n,
      );
  }

  function buildBreadcrumb(
    nodes: FileNode[],
    id: string,
    path: string[],
  ): string[] {
    for (const n of nodes) {
      if (n.id === id) return [...path, n.name];
      if (n.children) {
        const found = buildBreadcrumb(n.children, id, [...path, n.name]);
        if (found.length > 0) return found;
      }
    }
    return [];
  }

  return {
    tree,
    expandedIds,
    selectedId,
    loading,
    error,
    selectedFile,
    breadcrumb,
    isExpanded,
    loadTree,
    toggleFolder,
    selectFile,
    createFile,
    createFolder,
    deleteNode,
    renameNode,
    moveNode,
    updateFileContent,
    saveFile,
  };
});
