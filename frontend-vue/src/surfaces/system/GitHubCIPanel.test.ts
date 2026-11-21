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
