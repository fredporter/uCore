// @vitest-environment jsdom
import { describe, expect, it } from "vitest";
import {
  parseChartSpec,
  renderSvgChart,
} from "./svgChartRenderer";

describe("svgChartRenderer", () => {
  it("parses declarative key-value lines into a bar ChartSpec", () => {
    const raw = `
type: bar
title: Memory Usage
Chrome: 650
Code: 420
uCore: 85
    `;
    const spec = parseChartSpec(raw);
    expect(spec.type).toBe("bar");
    expect(spec.title).toBe("Memory Usage");
    expect(spec.labels).toEqual(["Chrome", "Code", "uCore"]);
    expect(spec.data).toEqual([650, 420, 85]);
  });

  it("parses JSON formatted chart spec", () => {
    const raw = JSON.stringify({
      type: "donut",
      title: "Storage",
      labels: ["Audio", "Video", "Data"],
      data: [30, 50, 20],
      unit: "GB",
    });
    const spec = parseChartSpec(raw);
    expect(spec.type).toBe("donut");
    expect(spec.labels.length).toBe(3);
    expect(spec.data).toEqual([30, 50, 20]);
    expect(spec.unit).toBe("GB");
  });

  it("renders a vertical bar chart with SVG elements", () => {
    const svg = renderSvgChart(`
type: bar
title: Q1 Revenue
labels: [Jan, Feb, Mar]
data: [100, 150, 200]
unit: k
    `);
    expect(svg).toContain("<svg");
    expect(svg).toContain('class="usx-chart usx-chart--bar"');
    expect(svg).toContain("Q1 Revenue");
    expect(svg).toContain("Jan");
    expect(svg).toContain("150 k");
  });

  it("renders a horizontal bar chart when horizontal is true", () => {
    const svg = renderSvgChart(`
type: bar
horizontal: true
title: Task Status
Done: 15
Active: 8
Pending: 4
    `);
    expect(svg).toContain('class="usx-chart usx-chart--bar-h"');
    expect(svg).toContain("Done");
    expect(svg).toContain("Pending");
  });

  it("renders a line chart with SVG polyline and gradient area", () => {
    const svg = renderSvgChart(`
type: line
title: CPU Temperature
labels: [10s, 20s, 30s]
data: [42, 55, 48]
unit: °C
    `);
    expect(svg).toContain('class="usx-chart usx-chart--line"');
    expect(svg).toContain("<path");
    expect(svg).toContain("lineGrad");
    expect(svg).toContain("CPU Temperature");
    expect(svg).toContain("55 °C");
  });

  it("renders a donut chart with arc slices and legend percentages", () => {
    const svg = renderSvgChart(`
type: donut
title: Asset Distribution
Prose: 50
Diagrams: 50
    `);
    expect(svg).toContain('class="usx-chart usx-chart--donut"');
    expect(svg).toContain("50%");
    expect(svg).toContain("100"); // total
  });

  it("renders a sparkline with minimal path", () => {
    const svg = renderSvgChart(`
type: sparkline
data: [10, 25, 18, 30, 42]
    `);
    expect(svg).toContain('class="usx-chart usx-chart--sparkline"');
    expect(svg).toContain("<path");
  });

  it("returns fallback SVG when data is empty", () => {
    const svg = renderSvgChart(`type: bar\ntitle: Empty`);
    expect(svg).toContain("usx-chart--empty");
    expect(svg).toContain("No valid numeric data found for chart");
  });
});
