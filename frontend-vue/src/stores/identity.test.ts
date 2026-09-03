// @vitest-environment jsdom
import { createPinia, setActivePinia } from "pinia";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { useIdentityStore } from "./identity";

describe("identity store", () => {
  beforeEach(() => setActivePinia(createPinia()));

  it("loads the current identity and derives toolbar labels", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: true, json: async () => ({ user_id: "user-1", codeword: "Fred", install_id: "i", session_id: "s" }) }));
    const store = useIdentityStore();
    await store.load();
    expect(store.authenticated).toBe(true);
    expect(store.displayName).toBe("Fred");
    expect(store.initials).toBe("FR");
  });

  it("exposes an unauthenticated state when identity is unavailable", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new Error("offline")));
    const store = useIdentityStore();
    await store.load();
    expect(store.authenticated).toBe(false);
    expect(store.error).toBe("offline");
  });
});
