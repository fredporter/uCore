// @vitest-environment jsdom
import { createPinia, setActivePinia } from "pinia";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { useSettingsStore } from "./settings";

describe("settings sync", () => {
  beforeEach(() => setActivePinia(createPinia()));

  it("loads server preferences on initialization", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: true, json: async () => ({ preferences: { themeMode: "light", fontStyle: "mono", fontSize: 18, palette: "forest", defaultModel: "mistral" } }) }));
    const store = useSettingsStore();
    await store.initialize();
    expect(store.themeMode).toBe("light");
    expect(store.fontStyle).toBe("mono");
    expect(store.defaultModel).toBe("mistral");
  });

  it("migrates hydrated local preferences when the server is empty", async () => {
    const fetchMock = vi.fn()
      .mockResolvedValueOnce({ ok: true, json: async () => ({ preferences: {} }) })
      .mockResolvedValueOnce({ ok: true, json: async () => ({ status: "ok" }) });
    vi.stubGlobal("fetch", fetchMock);
    const store = useSettingsStore();
    store.setPalette("ocean");
    await store.initialize();
    expect(fetchMock).toHaveBeenCalledTimes(2);
    expect(String(fetchMock.mock.calls[1][1]?.body)).toContain('"palette":"ocean"');
  });
});
