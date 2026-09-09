// @vitest-environment jsdom
import { createPinia, setActivePinia } from "pinia";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { useIdentityStore } from "./identity";

describe("identity store", () => {
  beforeEach(() => setActivePinia(createPinia()));

  it("loads the current identity and derives toolbar labels", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({
          user_id: "user-1",
          codeword: "Fred",
          install_id: "i",
          session_id: "s",
          authenticated: true,
          active_profile_id: "default",
          active_profile: { id: "default", name: "Fred", role: "owner" },
          profiles: [{ id: "default", name: "Fred", role: "owner" }],
        }),
      }),
    );
    const store = useIdentityStore();
    await store.load();
    expect(store.authenticated).toBe(true);
    expect(store.displayName).toBe("Fred");
    expect(store.initials).toBe("FR");
    expect(store.activeProfileId).toBe("default");
    expect(store.profiles).toHaveLength(1);
  });

  it("exposes an unauthenticated state when identity is unavailable", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new Error("offline")));
    const store = useIdentityStore();
    await store.load();
    expect(store.authenticated).toBe(false);
    expect(store.error).toBe("offline");
  });

  it("supports switching profiles", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        success: true,
        identity: {
          user_id: "user-1",
          codeword: "Fred",
          install_id: "i",
          session_id: "s2",
          authenticated: true,
          active_profile_id: "developer",
          active_profile: { id: "developer", name: "Developer Mode", role: "developer" },
          profiles: [
            { id: "default", name: "Fred", role: "owner" },
            { id: "developer", name: "Developer Mode", role: "developer" },
          ],
        },
      }),
    });
    vi.stubGlobal("fetch", fetchMock);
    const store = useIdentityStore();
    await store.switchProfile("developer");

    expect(store.authenticated).toBe(true);
    expect(store.activeProfileId).toBe("developer");
    expect(store.displayName).toBe("Developer Mode");
  });

  it("supports logout to unauthenticated state and login back", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          success: true,
          identity: {
            user_id: "user-1",
            codeword: "Fred",
            install_id: "i",
            session_id: "s3",
            authenticated: false,
            active_profile_id: "",
            active_profile: null,
            profiles: [{ id: "default", name: "Fred", role: "owner" }],
          },
        }),
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          success: true,
          identity: {
            user_id: "user-1",
            codeword: "Fred",
            install_id: "i",
            session_id: "s4",
            authenticated: true,
            active_profile_id: "default",
            active_profile: { id: "default", name: "Fred", role: "owner" },
            profiles: [{ id: "default", name: "Fred", role: "owner" }],
          },
        }),
      });

    vi.stubGlobal("fetch", fetchMock);
    const store = useIdentityStore();

    await store.logout();
    expect(store.authenticated).toBe(false);
    expect(store.activeProfileId).toBe("");
    expect(store.activeProfile).toBeNull();

    await store.login("default");
    expect(store.authenticated).toBe(true);
    expect(store.activeProfileId).toBe("default");
    expect(store.displayName).toBe("Fred");
  });
});
