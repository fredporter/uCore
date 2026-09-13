// @vitest-environment jsdom
import { describe, expect, it } from "vitest";
import { hydrateDiagrams } from "./diagramHydrator";

describe("diagramHydrator", () => {
  it("gracefully handles null or empty container", async () => {
    await expect(hydrateDiagrams(null)).resolves.toBeUndefined();
    const empty = document.createElement("div");
    await expect(hydrateDiagrams(empty)).resolves.toBeUndefined();
  });

  it("hydrates declarative chart blocks with toolbars", async () => {
    const container = document.createElement("div");
    container.innerHTML = `
      <div class="md-diagram md-diagram--chart" data-diagram="chart" data-chart-raw="type%3A%20bar">
        <svg viewBox="0 0 100 100"><rect width="100" height="100" /></svg>
      </div>
    `;

    await hydrateDiagrams(container);

    const chartEl = container.querySelector(".md-diagram--chart")!;
    expect(chartEl.getAttribute("data-hydrated")).toBe("true");
    expect(chartEl.querySelector(".md-diagram__toolbar")).toBeTruthy();
    expect(chartEl.querySelector(".md-diagram__label")?.textContent).toBe("SVG Chart");
    expect(chartEl.querySelectorAll("button").length).toBeGreaterThanOrEqual(2);
  });

  it("hydrates teletext blocks with copy button", async () => {
    const container = document.createElement("div");
    container.innerHTML = `
      <div class="md-diagram md-diagram--teletext" data-diagram="teletext">
        <pre class="teletext-screen"><code>[P100] CEEFAX 100</code></pre>
      </div>
    `;

    await hydrateDiagrams(container);

    const teletextEl = container.querySelector(".md-diagram--teletext")!;
    expect(teletextEl.getAttribute("data-hydrated")).toBe("true");
    expect(teletextEl.querySelector(".md-diagram__toolbar")).toBeTruthy();
    expect(teletextEl.querySelector(".md-diagram__label")?.textContent).toBe("Teletext Grid");
  });
});
