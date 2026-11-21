// @vitest-environment jsdom
import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, expect, it, vi } from "vitest";
import GitHubCIPanel from "./GitHubCIPanel.vue";

afterEach(() => vi.unstubAllGlobals());

it("opens on the default branch and refreshes the selected view for each repository", async () => {
  const fetchStatus = vi.fn(async (url: string) => Response.json({
    configured: true,
    branch: url.endsWith("branch_view=default") ? "main" : "feature/test",
    runs: [],
  }));
  vi.stubGlobal("fetch", fetchStatus);
  const wrapper = mount(GitHubCIPanel);
  await flushPromises();

  expect(fetchStatus.mock.calls[0][0]).toContain("/uCore/github?branch_view=default");
  expect(wrapper.text()).toContain("Branch: main");

  await wrapper.get("#ci-branch-view").setValue("working");
  await flushPromises();
  expect(wrapper.text()).toContain("Branch: feature/test");

  await wrapper.get("#ci-repository").setValue("uCodePlus");
  await flushPromises();
  await wrapper.get("button").trigger("click");
  await flushPromises();
  expect(fetchStatus.mock.calls.slice(2).map(([url]) => url)).toEqual([
    expect.stringContaining("/uCodePlus/github?branch_view=working"),
    expect.stringContaining("/uCodePlus/github?branch_view=working"),
  ]);
  wrapper.unmount();
});

it("distinguishes unavailable workflow runs from a branch with no runs", async () => {
  vi.stubGlobal("fetch", vi.fn(async () => Response.json({
    configured: true, branch: "main", runs_available: false, runs: [],
  })));
  const wrapper = mount(GitHubCIPanel);
  await flushPromises();
  expect(wrapper.get('[role="alert"]').text()).toContain("workflow runs could not be loaded");
  expect(wrapper.text()).not.toContain("No runs returned");
  wrapper.unmount();
});

it("keeps linked run results and the last successful timestamp through a DNS failure", async () => {
  const runUrl = "https://github.com/fredporter/uCore/actions/runs/123";
  const success = {
    configured: true,
    branch: "main",
    runs: [{ databaseId: 123, workflowName: "Tests", status: "completed", conclusion: "failure", url: runUrl }],
  };
  const fetchStatus = vi.fn()
    .mockResolvedValueOnce(Response.json(success))
    .mockResolvedValueOnce(Response.json({ configured: false, error_code: "network" }))
    .mockResolvedValueOnce(Response.json({ ...success, runs: [] }));
  vi.stubGlobal("fetch", fetchStatus);
  const wrapper = mount(GitHubCIPanel);
  await flushPromises();
  const refreshedAt = wrapper.get("time").attributes("datetime");

  await wrapper.get("button").trigger("click");
  await flushPromises();
  expect(wrapper.get('[role="alert"]').text()).toContain("DNS");
  expect(wrapper.text()).toContain("Showing saved results.");
  expect(wrapper.get("time").attributes("datetime")).toBe(refreshedAt);
  expect(wrapper.get(".ci-run a").attributes("href")).toBe(runUrl);
  expect(wrapper.get(".ci-run").text()).toContain("failure");

  await wrapper.get("button").trigger("click");
  await flushPromises();
  expect(wrapper.find('[role="alert"]').exists()).toBe(false);
  expect(wrapper.text()).toContain("No runs returned");
  wrapper.unmount();
});

it("keeps repo and branch views isolated when an older request finishes last", async () => {
  let completeOriginal!: (response: Response) => void;
  const original = new Promise<Response>((resolve) => { completeOriginal = resolve; });
  const fetchStatus = vi.fn()
    .mockReturnValueOnce(original)
    .mockResolvedValueOnce(Response.json({ configured: true, branch: "feature/test", runs: [] }))
    .mockResolvedValueOnce(Response.json({ configured: false, error_code: "auth" }))
    .mockRejectedValueOnce(new Error("local service unavailable"));
  vi.stubGlobal("fetch", fetchStatus);
  const wrapper = mount(GitHubCIPanel);

  await wrapper.get("#ci-branch-view").setValue("working");
  await flushPromises();
  completeOriginal(Response.json({ configured: true, branch: "main", runs: [] }));
  await flushPromises();
  expect(wrapper.text()).toContain("Branch: feature/test");
  expect(wrapper.text()).not.toContain("Branch: main");

  await wrapper.get("#ci-repository").setValue("uCode");
  await flushPromises();
  expect(wrapper.get('[role="alert"]').text()).toContain("gh auth status");
  expect(wrapper.find("time").exists()).toBe(false);

  await wrapper.get("#ci-repository").setValue("uCore");
  await flushPromises();
  expect(wrapper.get('[role="alert"]').text()).toContain("local uCore service");
  expect(wrapper.text()).toContain("Branch: feature/test");
  wrapper.unmount();
});

it("clears saved results when GitHub confirms the working branch has changed", async () => {
  vi.stubGlobal("fetch", vi.fn()
    .mockResolvedValueOnce(Response.json({ configured: true, branch: "main", runs: [] }))
    .mockResolvedValueOnce(Response.json({ configured: true, branch: "feature/old", runs: [] }))
    .mockResolvedValueOnce(Response.json({
      configured: true, branch: "feature/new", runs_available: false, error_code: "timeout", runs: [],
    })));
  const wrapper = mount(GitHubCIPanel);
  await flushPromises();

  await wrapper.get("#ci-branch-view").setValue("working");
  await flushPromises();
  expect(wrapper.text()).toContain("Branch: feature/old");

  await wrapper.get("button").trigger("click");
  await flushPromises();
  expect(wrapper.get('[role="alert"]').text()).toContain("too long");
  expect(wrapper.find("time").exists()).toBe(false);
  expect(wrapper.text()).not.toContain("Branch: feature/old");
  wrapper.unmount();
});
