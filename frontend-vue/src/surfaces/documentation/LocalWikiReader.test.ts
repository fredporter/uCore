// @vitest-environment jsdom
import { flushPromises, mount } from "@vue/test-utils";
import { createPinia } from "pinia";
import { afterEach, expect, it, vi } from "vitest";
import LocalWikiReader from "./LocalWikiReader.vue";

vi.mock("../../utils/diagramHydrator", () => ({ hydrateDiagrams: vi.fn() }));

afterEach(() => {
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
            { id: "public", source: "public", items: [
              file("public", map),
              file("public", "elsewhere/compass_use.md"),
            ] },
            { id: "shared", source: "shared", items: [file("shared", compass)] },
            { id: "public-other", source: "public", items: [{
              source: "public", path: folder, name: "navigation", is_dir: true,
              children: [file("public", compass)],
            }] },
          ],
        }),
      };
    }
    const params = new URL(url, "https://test.invalid").searchParams;
    return {
      ok: true,
      json: async () => ({
        content: params.get("path") === map
          ? "# Map Reading\n\n[Compass Use](compass_use.md)\n\n[Source](https://example.org/guide)"
          : "# Compass Use\n\n[Map Reading](./map_reading.md)",
      }),
    };
  });
  Object.defineProperty(Element.prototype, "scrollTo", { configurable: true, value: vi.fn() });
  vi.stubGlobal("fetch", fetchDocument);
  const wrapper = mount(LocalWikiReader, { global: { plugins: [createPinia()] } });
  try {
    await flushPromises();
    expect(wrapper.get(".offline-citation-chip").text()).toContain("example.org");
    await wrapper.get('a[href="compass_use.md"]').trigger("click");
    await flushPromises();
    expect(fetchDocument).toHaveBeenLastCalledWith(
      "/api/docs/content?source=public&path=" + encodeURIComponent(compass),
    );
    expect(wrapper.get("article h1").text()).toBe("Compass Use");

    await wrapper.get('a[href="./map_reading.md"]').trigger("click");
    await flushPromises();
    expect(wrapper.get("article h1").text()).toBe("Map Reading");
  } finally {
    wrapper.unmount();
  }
});
