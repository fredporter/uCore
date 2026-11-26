// @vitest-environment jsdom
import { describe, it, expect, vi, beforeEach } from "vitest";
import { mount, flushPromises } from "@vue/test-utils";
import { createPinia, setActivePinia } from "pinia";
import ChatBubblePanel from "./ChatBubblePanel.vue";
import { useChatStore } from "../../stores/chat";

describe("ChatBubblePanel - Format Smith", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
  });

  it("exposes Format Smith specialist selection in OK Assistant mode", async () => {
    const wrapper = mount(ChatBubblePanel, {
      props: {
        chatMessages: [],
        devMessages: [],
        loading: false,
        localAssistant: true,
        contextLabel: "Dashboard",
        currentTask: "",
        activeLane: "chat",
      },
      global: {
        stubs: {
          RouterLink: { template: "<a><slot /></a>" },
          UIcon: { template: "<span class='u-icon' />" },
        },
      },
    });

    // Check specialist toggle buttons exist in footer
    const buttons = wrapper.findAll(".chat-panel__mode-btn");
    expect(buttons.length).toBeGreaterThanOrEqual(2);
    expect(buttons[0].text()).toContain("General");
    expect(buttons[1].text()).toContain("Format Smith");

    // Click Format Smith
    await buttons[1].trigger("click");
    await flushPromises();

    // Placeholder updates
    const textarea = wrapper.get("textarea");
    expect(textarea.attributes("placeholder")).toBe("Paste notes to format as Markdown…");

    wrapper.unmount();
  });

  it("emits send-chat with format-smith specialist when sending notes", async () => {
    const chatStore = useChatStore();
    const wrapper = mount(ChatBubblePanel, {
      props: {
        chatMessages: [],
        devMessages: [],
        loading: false,
        localAssistant: true,
        contextLabel: "Dashboard",
        currentTask: "",
        activeLane: "chat",
      },
      global: {
        stubs: {
          RouterLink: { template: "<a><slot /></a>" },
          UIcon: { template: "<span class='u-icon' />" },
        },
      },
    });

    // Select Format Smith
    const buttons = wrapper.findAll(".chat-panel__mode-btn");
    await buttons[1].trigger("click");

    // Enter raw notes into textarea
    chatStore.input = "# Meeting 2026-11-21\n* Alice & Bob\n* Budget: $1,250 (estimated?)";
    await flushPromises();

    // Send
    const sendButton = wrapper.get(".chat-panel__send");
    await sendButton.trigger("click");
    await flushPromises();

    expect(wrapper.emitted("send-chat")).toBeTruthy();
    const emitted = wrapper.emitted("send-chat")![0];
    expect(emitted[0]).toContain("Meeting 2026-11-21");
    expect(emitted[2]).toBe("format-smith");

    wrapper.unmount();
  });

  it("preserves/recovers input draft when an error restores chatStore.input", async () => {
    const chatStore = useChatStore();
    const wrapper = mount(ChatBubblePanel, {
      props: {
        chatMessages: [],
        devMessages: [],
        loading: false,
        localAssistant: true,
        contextLabel: "Dashboard",
        currentTask: "",
        activeLane: "chat",
      },
      global: {
        stubs: {
          RouterLink: { template: "<a><slot /></a>" },
          UIcon: { template: "<span class='u-icon' />" },
        },
      },
    });

    const notes = "# Raw notes with budget $500";
    chatStore.input = notes;
    await flushPromises();

    // Verify textarea displays notes
    const textarea = wrapper.get("textarea");
    expect((textarea.element as HTMLTextAreaElement).value).toBe(notes);

    // Simulate send clears, then error restores chatStore.input
    chatStore.input = "";
    await flushPromises();
    expect((textarea.element as HTMLTextAreaElement).value).toBe("");

    // Error recovery restores input
    chatStore.input = notes;
    await flushPromises();
    expect((textarea.element as HTMLTextAreaElement).value).toBe(notes);

    wrapper.unmount();
  });

  it("renders assistant messages using Markdown renderer", async () => {
    const wrapper = mount(ChatBubblePanel, {
      props: {
        chatMessages: [
          { role: "user", content: "notes" },
          { role: "assistant", content: "```markdown\n# Formatted Heading\n- Item 1\n```" },
        ],
        devMessages: [],
        loading: false,
        localAssistant: true,
        contextLabel: "Dashboard",
        currentTask: "",
        activeLane: "chat",
      },
      global: {
        stubs: {
          RouterLink: { template: "<a><slot /></a>" },
          UIcon: { template: "<span class='u-icon' />" },
        },
      },
    });

    expect(wrapper.get(".chat-panel__msg--assistant h1").text()).toBe("Formatted Heading");
    expect(wrapper.get(".chat-panel__msg--assistant li").text()).toBe("Item 1");

    wrapper.unmount();
  });
});
