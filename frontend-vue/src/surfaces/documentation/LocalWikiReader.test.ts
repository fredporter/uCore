// @vitest-environment jsdom
import { flushPromises, mount } from "@vue/test-utils";
import { createPinia } from "pinia";
import { afterEach, expect, it, vi } from "vitest";
import { useShellStore } from "../../stores/shell";
import { useWorkflowStore } from "../../stores/workflow";
import LocalWikiReader from "./LocalWikiReader.vue";

const { router, route } = await vi.hoisted(async () => {
  const { reactive } = await import("vue");
  const route = reactive<{ query: Record<string, string | undefined> }>({ query: {} });
  return { route, router: { push: vi.fn(async (target) => {
    if (!target.path) route.query = target.query;
  }) } };
});
vi.mock("vue-router", () => ({ useRouter: () => router, useRoute: () => route }));
vi.mock("../../utils/diagramHydrator", () => ({ hydrateDiagrams: vi.fn() }));

afterEach(() => {
  route.query = {};
  vi.unstubAllGlobals();
  Reflect.deleteProperty(Element.prototype, "scrollTo");
});

it("opens an offline Markdown link at its exact path in the current source", async () => {
  const folder = "global-knowledge/navigation";
  const map = folder + "/map_reading.md";
  const compass = folder + "/compass_use.md";
  const file = (source: string, path: string) => ({
    source, path, name: path.split("/").pop(), is_dir: false,
  });
  const fetchDocument = vi.fn(async (url: string) => {
    if (url === "/api/docs/wiki/tree") {
      return {
        ok: true,
        json: async () => ({
          vaults: [
            { id: "personal", source: "vault", items: [file("vault", "Memory/Daily_Activity.md")] },
            { id: "shared", source: "shared", items: [file("shared", compass)] },
            { id: "public", source: "public", items: [
              file("public", "elsewhere/compass_use.md"),
              {
                source: "public", path: "global-knowledge", name: "Global Knowledge", is_dir: true,
                children: [{
                  source: "public", path: folder, name: "Navigation", is_dir: true,
                  children: [file("public", map), file("public", compass)],
                }],
              },
            ] },
          ],
        }),
      };
    }
    const params = new URL(url, "https://test.invalid").searchParams;
    return {
      ok: true,
      json: async () => ({
        content: params.get("path") === map
          ? "# Map Reading\n\n[Compass Use](compass_use.html)\n\n[Source](https://example.org/guide)"
          : "# Compass Use\n\n[Map Reading](./map_reading.md)",
      }),
    };
  });
  Object.defineProperty(Element.prototype, "scrollTo", { configurable: true, value: vi.fn() });
  vi.stubGlobal("fetch", fetchDocument);
  const wrapper = mount(LocalWikiReader, { global: { plugins: [createPinia()], stubs: { RouterLink: true } } });
  try {
    await flushPromises();
    expect(wrapper.get("main h1").text()).toBe("Global Knowledge");
    expect(wrapper.get("main").text()).not.toContain("Daily_Activity");
    expect(fetchDocument).toHaveBeenCalledTimes(1);
    expect(wrapper.get("main ul").text()).toContain("Navigation");
    await wrapper.get(".wiki-index-browse").trigger("click");
    expect(useShellStore().sidebarOpen).toBe(true);
    expect(useShellStore().sidebarMode).toBe("vault");

    route.query = { tab: "wiki", article: map, source: "public" };
    await flushPromises();
    expect(wrapper.get(".offline-citation-chip").text()).toContain("example.org");
    await wrapper.get('a[href="compass_use.html"]').trigger("click");
    await flushPromises();
    expect(fetchDocument).toHaveBeenLastCalledWith(
      "/api/docs/content?source=public&path=" + encodeURIComponent(compass),
    );
    expect(wrapper.get("article h1").text()).toBe("Compass Use");

    await wrapper.get('a[href="./map_reading.md"]').trigger("click");
    await flushPromises();
    expect(wrapper.get("article h1").text()).toBe("Map Reading");

    await wrapper.get('[aria-label="Open in Editor"]').trigger("click");
    expect(router.push).toHaveBeenCalledWith({ path: "/workflow", query: { tab: "editor" } });
    expect(useWorkflowStore().selectedFile).toMatchObject({
      path: "virtual/copy/public/" + map, filename: "map_reading.md", readOnly: false,
      content: expect.stringContaining("# Map Reading"),
    });
    await wrapper.get('[aria-label="Global Knowledge library index"]').trigger("click");
    expect(wrapper.get("main h1").text()).toBe("Global Knowledge");
    expect(wrapper.get("main ul").text()).toContain("Navigation");
  } finally {
    wrapper.unmount();
  }
});

it("opens a typed library result through its reader locator and rejects unsupported locators", async () => {
  const article = "global-knowledge/navigation/map_reading.md";
  const fetchDocument = vi.fn(async (url: string) => {
    const path = new URL(url, "https://test.invalid").pathname;
    const result = {
      id: "map-reading", type: "file", title: "map reading", source: "public",
      reader_source: "public", relative_path: article, preview: "Map reading basics.",
    };
    switch (path) {
      case "/api/docs/wiki/tree":
        return { ok: true, json: async () => ({ vaults: [] }) };
      case "/api/library/stats":
        return { ok: true, json: async () => ({ status: "not-built" }) };
      case "/api/library/search":
        return { ok: true, json: async () => ({
          results: [
            result,
            { ...result, id: "task", type: "task", title: "map task" },
            { ...result, id: "traversal", relative_path: "navigation/../private.md", title: "invalid path" },
          ],
        }) };
      case "/api/docs/content":
        return { ok: true, json: async () => ({ content: "# Exact Library Article" }) };
      default:
        throw new Error(`Unexpected request: ${url}`);
    }
  });
  Object.defineProperty(Element.prototype, "scrollTo", { configurable: true, value: vi.fn() });
  vi.stubGlobal("fetch", fetchDocument);
  vi.useFakeTimers();
  const wrapper = mount(LocalWikiReader, { global: { plugins: [createPinia()], stubs: { RouterLink: true } } });

  try {
    await wrapper.get(".wiki-search-trigger").trigger("click");
    await wrapper.get(".wiki-search-modal__input").setValue("map");
    vi.advanceTimersByTime(150);
    await flushPromises();

    expect(wrapper.get(".footer-left").text()).toContain("Local index has not been built");
    const results = wrapper.findAll(".wiki-result-open");
    expect(results[0].text()).toContain("File · ~/Public");
    expect(results[1].attributes("disabled")).toBeDefined();
    expect(results[2].attributes("disabled")).toBeDefined();
    await results[0].trigger("click");
    await flushPromises();

    expect(fetchDocument).toHaveBeenLastCalledWith(
      "/api/docs/content?source=public&path=" + encodeURIComponent(article),
    );
    expect(wrapper.get("article h1").text()).toBe("Exact Library Article");
  } finally {
    wrapper.unmount();
    vi.useRealTimers();
  }
});
