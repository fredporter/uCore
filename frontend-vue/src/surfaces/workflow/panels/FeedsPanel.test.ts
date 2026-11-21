// @vitest-environment jsdom
import { flushPromises, mount } from "@vue/test-utils";
import { createPinia, setActivePinia } from "pinia";
import { afterEach, expect, it, vi } from "vitest";
import { createMemoryHistory, createRouter } from "vue-router";
import { useWorkflowStore } from "../../../stores/workflow";
import FeedsPanel from "./FeedsPanel.vue";

afterEach(() => {
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});

it("imports a saved item for review and links its explicitly promoted task", async () => {
  const pinia = createPinia();
  setActivePinia(pinia);
  const workflow = useWorkflowStore();
  vi.spyOn(workflow, "fetchTasks").mockResolvedValueOnce().mockImplementation(async () => {
    workflow.tasks = [{
      id: "feed-12", title: "Read local news", status: "todo", priority: "medium",
      board: "inbox", tags: [], description: "An offline story",
    }];
  });
  const router = createRouter({
    history: createMemoryHistory(),
    routes: [{ path: "/workflow", component: FeedsPanel }],
  });
  await router.push("/workflow?tab=feeds");
  await router.isReady();

  const item = { guid: "rss-item-1", title: "Read local news", summary: "An offline story" };
  let items: Record<string, unknown>[] = [];
  const fetchMock = vi.fn(async (url: string, _options?: RequestInit) => {
    const path = new URL(url).pathname;
    if (path === "/api/feed/rss") {
      items = [{ id: 12, title: item.title, content: item.summary, type: "rss_item", source: "rss" }];
      return Response.json({ activity_id: 12, spool_receipt: "import-receipt" });
    }
    if (path === "/api/feed/promote") {
      return Response.json({ task_id: "feed-12", binder: "", spool_receipt: "task-receipt" });
    }
    return Response.json({ activities: items, connections: [], sources: [], count: 0 });
  });
  vi.stubGlobal("fetch", fetchMock);

  const wrapper = mount(FeedsPanel, { global: { plugins: [pinia, router] } });
  await flushPromises();
  const fileInput = wrapper.get<HTMLInputElement>('input[type="file"]');
  Object.defineProperty(fileInput.element, "files", {
    value: [{ size: 100, text: async () => JSON.stringify({ rss_item: item, peer_handshake: {} }) }],
  });
  await fileInput.trigger("change");
  await wrapper.get("form").trigger("submit");
  await flushPromises();
  expect(fetchMock).toHaveBeenCalledWith(expect.stringMatching(/\/api\/feed\/rss$/), expect.objectContaining({
    body: JSON.stringify({ ...item, review_only: true }),
  }));
  expect(wrapper.text()).toContain("import-receipt");
  expect(wrapper.text()).toContain(item.title);

  await wrapper.get('[aria-label="Add to tasks"]').trigger("click");
  await flushPromises();
  expect(wrapper.text()).toContain("Task created.");
  expect(wrapper.text()).toContain("task-receipt");
  expect(wrapper.get('[role="alert"]').text()).toContain("Task saved");
  await wrapper.findAll("button").find(button => button.text().includes("Retry loading task"))!.trigger("click");
  await flushPromises();
  expect(wrapper.findAll("a").find(link => link.text() === "Open task")?.attributes("href")).toContain("task=feed-12");
  expect(wrapper.find('[aria-label="Add to tasks"]').exists()).toBe(false);
  wrapper.unmount();
});
