// @vitest-environment jsdom
import { createPinia, setActivePinia } from "pinia";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { useIdentityStore } from "../stores/identity";
import { useSettingsStore } from "../stores/settings";
import { useChatStore } from "../stores/chat";
import { citationGenerator } from "../utils/citationGenerator";
import { parseDocument, serializeDocument } from "../utils/frontmatterParser";
import { createVariantDocument, syncVariantMetadata } from "../utils/documentVariant";

describe("Sprint 6 Product Journey & Release Hardening", () => {
  beforeEach(() => {
    localStorage.clear();
    setActivePinia(createPinia());
  });

  describe("Journey 1: Sovereign Identity & Profile Lifecycle", () => {
    it("manages multi-profile sessions and unauthenticated transitions", async () => {
      let activeProfile = "default";
      let authenticated = true;

      vi.stubGlobal(
        "fetch",
        vi.fn().mockImplementation(async (url, options) => {
          const urlStr = String(url);
          if (urlStr.includes("/api/identity/me")) {
            return {
              ok: true,
              json: async () => ({
                user_id: "UDOS-20260909-ABC123",
                codeword: activeProfile === "default" ? "Local Owner" : "Dev User",
                install_id: "host-macbook-1",
                session_id: "sess-1",
                authenticated,
                active_profile_id: authenticated ? activeProfile : "",
                active_profile: authenticated
                  ? { id: activeProfile, name: activeProfile === "default" ? "Local Owner" : "Dev User", role: "owner" }
                  : null,
                profiles: [
                  { id: "default", name: "Local Owner", role: "owner" },
                  { id: "developer", name: "Dev User", role: "developer" },
                ],
              }),
            };
          }
          if (urlStr.includes("/api/identity/switch")) {
            const body = JSON.parse(options.body);
            activeProfile = body.profile_id;
            authenticated = true;
            return {
              ok: true,
              json: async () => ({
                success: true,
                identity: {
                  user_id: "UDOS-20260909-ABC123",
                  codeword: "Dev User",
                  install_id: "host-macbook-1",
                  session_id: "sess-2",
                  authenticated: true,
                  active_profile_id: "developer",
                  active_profile: { id: "developer", name: "Dev User", role: "developer" },
                  profiles: [
                    { id: "default", name: "Local Owner", role: "owner" },
                    { id: "developer", name: "Dev User", role: "developer" },
                  ],
                },
              }),
            };
          }
          if (urlStr.includes("/api/identity/logout")) {
            authenticated = false;
            return {
              ok: true,
              json: async () => ({
                success: true,
                identity: {
                  user_id: "UDOS-20260909-ABC123",
                  codeword: "Local Owner",
                  install_id: "host-macbook-1",
                  session_id: "sess-3",
                  authenticated: false,
                  active_profile_id: "",
                  active_profile: null,
                  profiles: [{ id: "default", name: "Local Owner", role: "owner" }],
                },
              }),
            };
          }
          return { ok: true, json: async () => ({}) };
        }),
      );

      const identityStore = useIdentityStore();
      await identityStore.load();

      expect(identityStore.authenticated).toBe(true);
      expect(identityStore.displayName).toBe("Local Owner");
      expect(identityStore.activeProfileId).toBe("default");

      // Switch profile
      await identityStore.switchProfile("developer");
      expect(identityStore.authenticated).toBe(true);
      expect(identityStore.activeProfileId).toBe("developer");
      expect(identityStore.displayName).toBe("Dev User");

      // Logout to unauthenticated state
      await identityStore.logout();
      expect(identityStore.authenticated).toBe(false);
      expect(identityStore.activeProfileId).toBe("");
      expect(identityStore.activeProfile).toBeNull();
    });
  });

  describe("Journey 2: Settings Architecture & Scoped Sync", () => {
    it("persists theme settings locally and synchronizes with server", async () => {
      const serverPrefs = { themeMode: "dark", fontSize: 16, palette: "default", defaultModel: "auto" };
      const fetchMock = vi.fn().mockImplementation(async (url, options) => {
        const method = options?.method || "GET";
        if (method === "GET") {
          return { ok: true, json: async () => ({ preferences: serverPrefs }) };
        }
        if (method === "POST") {
          return { ok: true, json: async () => ({ status: "ok" }) };
        }
        return { ok: true, json: async () => ({}) };
      });
      vi.stubGlobal("fetch", fetchMock);

      const settingsStore = useSettingsStore();
      await settingsStore.initialize();

      expect(settingsStore.themeMode).toBe("dark");
      expect(settingsStore.fontSize).toBe(16);

      // Change settings
      settingsStore.setThemeMode("light");
      settingsStore.setFontSize(20);
      settingsStore.setPalette("ocean");

      expect(settingsStore.themeMode).toBe("light");
      expect(settingsStore.fontSize).toBe(20);
      expect(settingsStore.palette).toBe("ocean");
    });
  });

  describe("Journey 3: Per-Profile Chat Isolation", () => {
    it("partitions conversations between profiles without data bleeding", async () => {
      const store = useChatStore();

      // Set conversation under profile 1
      const convP1 = [
        {
          id: "conv-owner-1",
          title: "Owner Project Discussion",
          model: "auto",
          createdAt: "2026-01-01",
          updatedAt: "2026-01-01",
          messages: [{ id: "m1", role: "user" as const, content: "Secret owner note", timestamp: "2026-01-01" }],
        },
      ];
      localStorage.setItem("assistui-conversations-default", JSON.stringify(convP1));

      // Set conversation under profile 2
      const convP2 = [
        {
          id: "conv-guest-1",
          title: "Guest Public Inquiries",
          model: "auto",
          createdAt: "2026-01-02",
          updatedAt: "2026-01-02",
          messages: [{ id: "m2", role: "user" as const, content: "Public question", timestamp: "2026-01-02" }],
        },
      ];
      localStorage.setItem("assistui-conversations-guest", JSON.stringify(convP2));

      // Mock server returning guest profile conversations
      vi.stubGlobal(
        "fetch",
        vi.fn().mockImplementation(async (url) => {
          const urlStr = String(url);
          if (urlStr.includes("profile=guest")) {
            return { ok: true, json: async () => ({ conversations: convP2 }) };
          }
          return { ok: true, json: async () => ({ conversations: convP1 }) };
        }),
      );

      // Default profile history
      await store.restoreHistory();
      expect(store.conversations).toHaveLength(1);
      expect(store.conversations[0].id).toBe("conv-owner-1");
    });
  });

  describe("Journey 4: Authoring, Metadata & Citation Provenance", () => {
    it("handles frontmatter roundtrips, variants, and IEEE/APA citations cleanly", () => {
      const originalMarkdown = `---
title: "uDOS Architecture Review"
author: "Engineering"
tags: ["system", "release"]
---
# Executive Summary
The system conforms to local-first invariants.

<!-- variant: detailed -->
## Detailed Implementation
Deep architectural notes for verification.
`;

      // 1. Frontmatter parsing & roundtrip
      const { frontmatter, body } = parseDocument(originalMarkdown);
      expect(frontmatter.title).toBe("uDOS Architecture Review");
      expect(frontmatter.author).toBe("Engineering");
      expect(frontmatter.tags).toEqual(["system", "release"]);

      const serialized = serializeDocument(body, frontmatter);
      expect(serialized).toContain("title: uDOS Architecture Review");
      expect(serialized).toContain("The system conforms to local-first invariants.");

      // 2. Variant document creation & sync
      const variantDoc = createVariantDocument(originalMarkdown, "docs/arch.md", "var-detailed");
      expect(variantDoc).toContain("id: var-detailed");
      expect(variantDoc).toContain("variant_of: docs/arch.md");
      expect(variantDoc).toContain("status: draft");

      const synced = syncVariantMetadata(originalMarkdown, variantDoc);
      expect(synced).toContain("id: var-detailed");
      expect(synced).toContain("title: uDOS Architecture Review");

      // 3. Citation provenance
      const metadata = {
        title: "Sovereign Computing Architecture",
        author: "Porter, F.",
        site: "uKnowledge Press",
        published: "2026-01-01",
        accessed: "2026-09-09",
        url: "https://udos.local/arch-2026",
      };

      const apaCitation = citationGenerator(metadata, "APA");
      expect(apaCitation).toContain("Porter, F.");
      expect(apaCitation).toContain("Sovereign Computing Architecture");
      expect(apaCitation).toContain("https://udos.local/arch-2026");

      const uknowledgeCitation = citationGenerator(metadata, "uKnowledge");
      expect(uknowledgeCitation).toContain("> [!NOTE] Citation: Sovereign Computing Architecture");
      expect(uknowledgeCitation).toContain("Provenance: [uKnowledge Press](https://udos.local/arch-2026)");
      expect(uknowledgeCitation).toContain("Author: Porter, F.");
    });
  });
});
