// @vitest-environment jsdom

import { mount, flushPromises } from "@vue/test-utils";
import { describe, expect, it, vi, beforeEach } from "vitest";
import BitChatSurface from "./BitChatSurface.vue";

// Mock vue-router
vi.mock("vue-router", () => ({
  useRouter: () => ({
    push: vi.fn(),
  }),
}));

describe("BitChatSurface", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("renders discovered mesh peers and messages", async () => {
    const fakePeers = {
      status: "ok",
      local_peer_id: "node_host_01",
      local_node_name: "uDos Studio Host",
      peers: [
        {
          peer_id: "node_host_01",
          node_name: "uDos Studio Host",
          ip: "127.0.0.1",
          port: 3000,
          status: "online",
          is_local: true,
          services: ["_bitchat._tcp.local."],
        },
        {
          peer_id: "node_kiosk_99",
          node_name: "Workshop Kiosk",
          ip: "192.168.1.150",
          port: 3000,
          status: "online",
          is_local: false,
          services: ["_bitchat._tcp.local."],
        },
      ],
    };

    const fakeMessages = {
      status: "ok",
      channel: "#general",
      messages: [
        {
          id: 1,
          msg_id: "msg_001",
          channel: "#general",
          sender_name: "Workshop Kiosk",
          content: "Mesh beacon received! Ready for sync.",
          timestamp: "2026-09-14T12:00:00Z",
          saved_to_binder: false,
          task_id: null,
        },
      ],
    };

    global.fetch = vi.fn().mockImplementation((url: string) => {
      if (url.includes("/api/network/mesh/peers")) {
        return Promise.resolve({
          ok: true,
          json: async () => fakePeers,
        });
      }
      if (url.includes("/api/network/bitchat/messages")) {
        return Promise.resolve({
          ok: true,
          json: async () => fakeMessages,
        });
      }
      return Promise.resolve({
        ok: true,
        json: async () => ({ status: "ok" }),
      });
    });

    const wrapper = mount(BitChatSurface);
    await flushPromises();

    // Verify UI header
    expect(wrapper.text()).toContain("BitChat");
    expect(wrapper.text()).toContain("Decentralized LAN Mesh");

    // Verify discovered peers
    expect(wrapper.text()).toContain("uDos Studio Host");
    expect(wrapper.text()).toContain("Workshop Kiosk");

    // Verify message stream
    expect(wrapper.text()).toContain("Mesh beacon received! Ready for sync.");

    // Verify channel tabs
    expect(wrapper.text()).toContain("general");
    expect(wrapper.text()).toContain("briefing");
    expect(wrapper.text()).toContain("engineering");
  });

  it("supports selecting messages for Save to Binder modal", async () => {
    const fakePeers = {
      status: "ok",
      local_peer_id: "node_host_01",
      local_node_name: "uDos Studio Host",
      peers: [],
    };

    const fakeMessages = {
      status: "ok",
      channel: "#general",
      messages: [
        {
          id: 1,
          msg_id: "msg_select_test",
          channel: "#general",
          sender_name: "Alice",
          content: "Important discussion point for binder",
          timestamp: "2026-09-14T12:00:00Z",
          saved_to_binder: false,
          task_id: null,
        },
      ],
    };

    global.fetch = vi.fn().mockImplementation((url: string) => {
      if (url.includes("/api/network/mesh/peers")) {
        return Promise.resolve({ ok: true, json: async () => fakePeers });
      }
      if (url.includes("/api/network/bitchat/messages")) {
        return Promise.resolve({ ok: true, json: async () => fakeMessages });
      }
      return Promise.resolve({ ok: true, json: async () => ({ status: "ok" }) });
    });

    const wrapper = mount(BitChatSurface);
    await flushPromises();

    // Select the message checkbox
    const checkbox = wrapper.find(".bitchat-msg-select input");
    expect(checkbox.exists()).toBe(true);
    await checkbox.setValue(true);

    // Save to Binder button should now be visible in header
    expect(wrapper.text()).toContain("1 selected");
    expect(wrapper.text()).toContain("Save to Binder");

    // Click Save to Binder
    const saveBtn = wrapper.findAll(".bitchat-btn").find((b) => b.text().includes("Save to Binder"));
    expect(saveBtn).toBeDefined();
    await saveBtn!.trigger("click");

    // Modal should be open
    expect(wrapper.find(".bitchat-modal").exists()).toBe(true);
    expect(wrapper.text()).toContain("Save Discussion Evidence to Binder");
  });
});
