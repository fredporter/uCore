/**
 * @module utils/svgChartRenderer
 * @description Pure sovereign SVG micro-chart generator.
 * Produces deterministic, resolution-independent SVG diagrams from simple declarative
 * markdown chart specs (YAML/key-value or JSON) without any external dependencies.
 */

export type ChartType = "bar" | "line" | "donut" | "pie" | "sparkline";

export interface ChartSeries {
  name: string;
  data: number[];
  color?: string;
}

export interface ChartSpec {
  type: ChartType;
  title?: string;
  unit?: string;
  labels: string[];
  data: number[];
  series?: ChartSeries[];
  width?: number;
  height?: number;
  horizontal?: boolean;
}

const PALETTE = [
  "#00e5ff", // USX electric cyan
  "#3b82f6", // sapphire blue
  "#10b981", // emerald green
  "#f59e0b", // amber gold
  "#ec4899", // magenta
  "#8b5cf6", // violet
  "#06b6d4", // cyan
  "#f97316", // coral orange
];

/**
 * Parse declarative text or JSON into a ChartSpec.
 */
export function parseChartSpec(raw: string): ChartSpec {
  const trimmed = raw.trim();
  if (trimmed.startsWith("{")) {
    try {
      const parsed = JSON.parse(trimmed);
      return normalizeSpec(parsed);
    } catch {
      // Fall through to line-by-line parser
    }
  }

  const spec: Partial<ChartSpec> = {
    type: "bar",
    labels: [],
    data: [],
    series: [],
  };

  const lines = trimmed.split("\n").map((l) => l.trim()).filter(Boolean);

  for (const line of lines) {
    // Check for comment
    if (line.startsWith("#") || line.startsWith("//")) continue;

    const colonIdx = line.indexOf(":");
    if (colonIdx === -1) {
      // Could be CSV comma-separated "Label, 123"
      const parts = line.split(",").map((s) => s.trim());
      if (parts.length >= 2) {
        const val = Number(parts[1]);
        if (!isNaN(val)) {
          spec.labels!.push(parts[0]);
          spec.data!.push(val);
        }
      }
      continue;
    }

    const key = line.slice(0, colonIdx).trim().toLowerCase();
    const val = line.slice(colonIdx + 1).trim();

    if (key === "type") {
      const t = val.toLowerCase();
      if (["bar", "line", "donut", "pie", "sparkline"].includes(t)) {
        spec.type = t as ChartType;
      }
    } else if (key === "title") {
      spec.title = val;
    } else if (key === "unit") {
      spec.unit = val;
    } else if (key === "horizontal") {
      spec.horizontal = val.toLowerCase() === "true" || val === "1";
    } else if (key === "labels") {
      spec.labels = val
        .replace(/^\[|\]$/g, "")
        .split(",")
        .map((s) => s.trim().replace(/^["']|["']$/g, ""));
    } else if (key === "data") {
      spec.data = val
        .replace(/^\[|\]$/g, "")
        .split(",")
        .map((s) => Number(s.trim()))
        .filter((n) => !isNaN(n));
    } else {
      // Treat as label: value
      const num = Number(val);
      if (!isNaN(num)) {
        // preserve original case of label
        const rawLabel = line.slice(0, colonIdx).trim();
        spec.labels!.push(rawLabel);
        spec.data!.push(num);
      }
    }
  }

  return normalizeSpec(spec);
}

function normalizeSpec(spec: Partial<ChartSpec>): ChartSpec {
  return {
    type: spec.type || "bar",
    title: spec.title || "",
    unit: spec.unit || "",
    labels: spec.labels || [],
    data: spec.data || [],
    series: spec.series || [],
    width: spec.width,
    height: spec.height,
    horizontal: spec.horizontal || false,
  };
}

/**
 * Render a chart from spec or raw string into standalone SVG markup.
 */
export function renderSvgChart(input: string | ChartSpec): string {
  const spec = typeof input === "string" ? parseChartSpec(input) : input;

  if (spec.data.length === 0 && (!spec.series || spec.series.length === 0)) {
    return renderFallback("No valid numeric data found for chart");
  }

  switch (spec.type) {
    case "bar":
      return spec.horizontal ? renderHorizontalBarChart(spec) : renderVerticalBarChart(spec);
    case "line":
      return renderLineChart(spec);
    case "donut":
    case "pie":
      return renderDonutChart(spec);
    case "sparkline":
      return renderSparkline(spec);
    default:
      return renderVerticalBarChart(spec);
  }
}

function escapeXml(text: string): string {
  return text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&apos;");
}

function renderFallback(message: string): string {
  return `<svg viewBox="0 0 400 80" xmlns="http://www.w3.org/2000/svg" class="usx-chart usx-chart--empty" role="img" aria-label="Empty chart">
  <rect width="400" height="80" rx="6" fill="#0f172a" stroke="#334155" stroke-dasharray="4 4" />
  <text x="200" y="45" fill="#94a3b8" text-anchor="middle" font-family="JetBrains Mono, monospace" font-size="12">${escapeXml(message)}</text>
</svg>`;
}

// ─── Vertical Bar Chart ──────────────────────────────────────────────

function renderVerticalBarChart(spec: ChartSpec): string {
  const width = spec.width || 560;
  const height = spec.height || 280;
  const padLeft = 60;
  const padRight = 24;
  const padTop = spec.title ? 48 : 28;
  const padBottom = 45;

  const chartW = width - padLeft - padRight;
  const chartH = height - padTop - padBottom;

  const maxVal = Math.max(...spec.data, 0);
  const scaleMax = maxVal === 0 ? 10 : Math.ceil(maxVal * 1.15);
  const n = spec.data.length;
  const slotW = chartW / n;
  const barW = Math.max(8, Math.min(slotW * 0.65, 48));

  let barsHtml = "";
  for (let i = 0; i < n; i++) {
    const val = spec.data[i];
    const barH = (val / scaleMax) * chartH;
    const x = padLeft + i * slotW + (slotW - barW) / 2;
    const y = padTop + chartH - barH;
    const color = PALETTE[i % PALETTE.length];
    const label = spec.labels[i] || `${i + 1}`;
    const formattedVal = `${val}${spec.unit ? " " + spec.unit : ""}`;

    barsHtml += `
    <g class="usx-chart-bar" tabindex="0">
      <title>${escapeXml(label)}: ${escapeXml(formattedVal)}</title>
      <rect x="${x}" y="${y}" width="${barW}" height="${Math.max(barH, 2)}" rx="3" fill="${color}" opacity="0.9">
        <animate attributeName="height" from="0" to="${Math.max(barH, 2)}" dur="0.4s" fill="freeze" />
      </rect>
      <text x="${x + barW / 2}" y="${y - 6}" text-anchor="middle" fill="#f8fafc" font-family="JetBrains Mono, monospace" font-size="10">${escapeXml(formattedVal)}</text>
      <text x="${x + barW / 2}" y="${height - padBottom + 18}" text-anchor="middle" fill="#94a3b8" font-family="JetBrains Mono, monospace" font-size="11">${escapeXml(label)}</text>
    </g>`;
  }

  // Y-axis gridlines
  let gridHtml = "";
  const steps = 4;
  for (let s = 0; s <= steps; s++) {
    const stepVal = Math.round((scaleMax / steps) * s);
    const y = padTop + chartH - (s / steps) * chartH;
    gridHtml += `
    <line x1="${padLeft}" y1="${y}" x2="${width - padRight}" y2="${y}" stroke="#334155" stroke-width="1" stroke-dasharray="${s === 0 ? "none" : "2 3"}" />
    <text x="${padLeft - 8}" y="${y + 4}" text-anchor="end" fill="#64748b" font-family="JetBrains Mono, monospace" font-size="10">${stepVal}</text>`;
  }

  const titleHtml = spec.title
    ? `<text x="${padLeft}" y="24" fill="#e2e8f0" font-family="Inter, system-ui, sans-serif" font-weight="600" font-size="14">${escapeXml(spec.title)}</text>`
    : "";

  return `<svg viewBox="0 0 ${width} ${height}" xmlns="http://www.w3.org/2000/svg" class="usx-chart usx-chart--bar" role="img" aria-label="${escapeXml(spec.title || "Bar Chart")}">
  <rect width="${width}" height="${height}" rx="6" fill="#0b1120" />
  ${titleHtml}
  ${gridHtml}
  ${barsHtml}
</svg>`;
}

// ─── Horizontal Bar Chart ────────────────────────────────────────────

function renderHorizontalBarChart(spec: ChartSpec): string {
  const width = spec.width || 560;
  const barH = 22;
  const rowH = 34;
  const padLeft = 110;
  const padRight = 65;
  const padTop = spec.title ? 44 : 20;
  const padBottom = 20;

  const n = spec.data.length;
  const height = padTop + n * rowH + padBottom;
  const chartW = width - padLeft - padRight;
  const maxVal = Math.max(...spec.data, 0) || 1;

  let barsHtml = "";
  for (let i = 0; i < n; i++) {
    const val = spec.data[i];
    const w = (val / maxVal) * chartW;
    const y = padTop + i * rowH;
    const color = PALETTE[i % PALETTE.length];
    const label = spec.labels[i] || `${i + 1}`;
    const formattedVal = `${val}${spec.unit ? " " + spec.unit : ""}`;

    barsHtml += `
    <g class="usx-chart-bar-h">
      <title>${escapeXml(label)}: ${escapeXml(formattedVal)}</title>
      <text x="${padLeft - 10}" y="${y + barH / 2 + 4}" text-anchor="end" fill="#94a3b8" font-family="JetBrains Mono, monospace" font-size="11">${escapeXml(label)}</text>
      <rect x="${padLeft}" y="${y}" width="${chartW}" height="${barH}" rx="3" fill="#1e293b" />
      <rect x="${padLeft}" y="${y}" width="${Math.max(w, 2)}" height="${barH}" rx="3" fill="${color}" opacity="0.9" />
      <text x="${padLeft + w + 8}" y="${y + barH / 2 + 4}" text-anchor="start" fill="#f8fafc" font-family="JetBrains Mono, monospace" font-size="10">${escapeXml(formattedVal)}</text>
    </g>`;
  }

  const titleHtml = spec.title
    ? `<text x="20" y="24" fill="#e2e8f0" font-family="Inter, system-ui, sans-serif" font-weight="600" font-size="14">${escapeXml(spec.title)}</text>`
    : "";

  return `<svg viewBox="0 0 ${width} ${height}" xmlns="http://www.w3.org/2000/svg" class="usx-chart usx-chart--bar-h" role="img" aria-label="${escapeXml(spec.title || "Bar Chart")}">
  <rect width="${width}" height="${height}" rx="6" fill="#0b1120" />
  ${titleHtml}
  ${barsHtml}
</svg>`;
}

// ─── Line / Area Chart ───────────────────────────────────────────────

function renderLineChart(spec: ChartSpec): string {
  const width = spec.width || 560;
  const height = spec.height || 260;
  const padLeft = 60;
  const padRight = 24;
  const padTop = spec.title ? 46 : 24;
  const padBottom = 40;

  const chartW = width - padLeft - padRight;
  const chartH = height - padTop - padBottom;

  const maxVal = Math.max(...spec.data, 0);
  const minVal = Math.min(...spec.data, 0);
  const range = maxVal - minVal === 0 ? 1 : maxVal - minVal;
  const n = spec.data.length;

  const points: Array<{ x: number; y: number; val: number; label: string }> = [];
  for (let i = 0; i < n; i++) {
    const val = spec.data[i];
    const x = padLeft + (n > 1 ? (i / (n - 1)) * chartW : chartW / 2);
    const y = padTop + chartH - ((val - minVal) / range) * chartH;
    const label = spec.labels[i] || `${i + 1}`;
    points.push({ x, y, val, label });
  }

  const pathD = points.map((p, i) => `${i === 0 ? "M" : "L"} ${p.x.toFixed(1)} ${p.y.toFixed(1)}`).join(" ");
  const areaD = `${pathD} L ${points[points.length - 1].x.toFixed(1)} ${padTop + chartH} L ${points[0].x.toFixed(1)} ${padTop + chartH} Z`;

  // Gridlines
  let gridHtml = "";
  const steps = 4;
  for (let s = 0; s <= steps; s++) {
    const stepVal = Math.round(minVal + (range / steps) * s);
    const y = padTop + chartH - (s / steps) * chartH;
    gridHtml += `
    <line x1="${padLeft}" y1="${y}" x2="${width - padRight}" y2="${y}" stroke="#334155" stroke-width="1" stroke-dasharray="${s === 0 ? "none" : "2 3"}" />
    <text x="${padLeft - 8}" y="${y + 4}" text-anchor="end" fill="#64748b" font-family="JetBrains Mono, monospace" font-size="10">${stepVal}</text>`;
  }

  let pointsHtml = "";
  for (const p of points) {
    const formatted = `${p.val}${spec.unit ? " " + spec.unit : ""}`;
    pointsHtml += `
    <g class="usx-chart-point">
      <title>${escapeXml(p.label)}: ${escapeXml(formatted)}</title>
      <circle cx="${p.x.toFixed(1)}" cy="${p.y.toFixed(1)}" r="4" fill="#00e5ff" stroke="#0b1120" stroke-width="2" />
      <text x="${p.x.toFixed(1)}" y="${height - padBottom + 18}" text-anchor="middle" fill="#94a3b8" font-family="JetBrains Mono, monospace" font-size="10">${escapeXml(p.label)}</text>
    </g>`;
  }

  const titleHtml = spec.title
    ? `<text x="${padLeft}" y="24" fill="#e2e8f0" font-family="Inter, system-ui, sans-serif" font-weight="600" font-size="14">${escapeXml(spec.title)}</text>`
    : "";

  return `<svg viewBox="0 0 ${width} ${height}" xmlns="http://www.w3.org/2000/svg" class="usx-chart usx-chart--line" role="img" aria-label="${escapeXml(spec.title || "Line Chart")}">
  <defs>
    <linearGradient id="lineGrad" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#00e5ff" stop-opacity="0.3" />
      <stop offset="100%" stop-color="#00e5ff" stop-opacity="0.0" />
    </linearGradient>
  </defs>
  <rect width="${width}" height="${height}" rx="6" fill="#0b1120" />
  ${titleHtml}
  ${gridHtml}
  <path d="${areaD}" fill="url(#lineGrad)" />
  <path d="${pathD}" fill="none" stroke="#00e5ff" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" />
  ${pointsHtml}
</svg>`;
}

// ─── Donut / Pie Chart ───────────────────────────────────────────────

function renderDonutChart(spec: ChartSpec): string {
  const width = spec.width || 520;
  const height = spec.height || 260;
  const cx = 150;
  const cy = height / 2 + (spec.title ? 10 : 0);
  const outerR = 80;
  const innerR = spec.type === "donut" ? 50 : 0;

  const total = spec.data.reduce((acc, v) => acc + v, 0);
  if (total === 0) return renderFallback("Total value is 0");

  let currentAngle = -Math.PI / 2;
  let slicesHtml = "";
  let legendHtml = "";

  const legendX = 280;
  const legendStartY = cy - (spec.data.length * 24) / 2;

  for (let i = 0; i < spec.data.length; i++) {
    const val = spec.data[i];
    const fraction = val / total;
    const sliceAngle = fraction * 2 * Math.PI;
    const color = PALETTE[i % PALETTE.length];
    const label = spec.labels[i] || `Item ${i + 1}`;
    const percent = Math.round(fraction * 100);

    const x1 = cx + outerR * Math.cos(currentAngle);
    const y1 = cy + outerR * Math.sin(currentAngle);
    const x2 = cx + outerR * Math.cos(currentAngle + sliceAngle);
    const y2 = cy + outerR * Math.sin(currentAngle + sliceAngle);

    const ix1 = cx + innerR * Math.cos(currentAngle + sliceAngle);
    const iy1 = cy + innerR * Math.sin(currentAngle + sliceAngle);
    const ix2 = cx + innerR * Math.cos(currentAngle);
    const iy2 = cy + innerR * Math.sin(currentAngle);

    const largeArc = sliceAngle > Math.PI ? 1 : 0;

    let pathD = "";
    if (innerR > 0) {
      pathD = `M ${x1.toFixed(2)} ${y1.toFixed(2)} A ${outerR} ${outerR} 0 ${largeArc} 1 ${x2.toFixed(2)} ${y2.toFixed(2)} L ${ix1.toFixed(2)} ${iy1.toFixed(2)} A ${innerR} ${innerR} 0 ${largeArc} 0 ${ix2.toFixed(2)} ${iy2.toFixed(2)} Z`;
    } else {
      pathD = `M ${cx} ${cy} L ${x1.toFixed(2)} ${y1.toFixed(2)} A ${outerR} ${outerR} 0 ${largeArc} 1 ${x2.toFixed(2)} ${y2.toFixed(2)} Z`;
    }

    slicesHtml += `
    <path d="${pathD}" fill="${color}" opacity="0.9">
      <title>${escapeXml(label)}: ${val}${spec.unit ? " " + spec.unit : ""} (${percent}%)</title>
    </path>`;

    // Legend row
    const ly = legendStartY + i * 24;
    legendHtml += `
    <g class="usx-chart-legend-item">
      <rect x="${legendX}" y="${ly}" width="12" height="12" rx="2" fill="${color}" />
      <text x="${legendX + 20}" y="${ly + 10}" fill="#e2e8f0" font-family="JetBrains Mono, monospace" font-size="11">${escapeXml(label)}</text>
      <text x="${width - 30}" y="${ly + 10}" text-anchor="end" fill="#94a3b8" font-family="JetBrains Mono, monospace" font-size="11">${percent}%</text>
    </g>`;

    currentAngle += sliceAngle;
  }

  const titleHtml = spec.title
    ? `<text x="24" y="24" fill="#e2e8f0" font-family="Inter, system-ui, sans-serif" font-weight="600" font-size="14">${escapeXml(spec.title)}</text>`
    : "";

  const centerText =
    spec.type === "donut"
      ? `<text x="${cx}" y="${cy + 5}" text-anchor="middle" fill="#f8fafc" font-family="JetBrains Mono, monospace" font-weight="700" font-size="15">${total}${spec.unit ? " " + spec.unit : ""}</text>`
      : "";

  return `<svg viewBox="0 0 ${width} ${height}" xmlns="http://www.w3.org/2000/svg" class="usx-chart usx-chart--donut" role="img" aria-label="${escapeXml(spec.title || "Donut Chart")}">
  <rect width="${width}" height="${height}" rx="6" fill="#0b1120" />
  ${titleHtml}
  <g class="usx-chart-donut-slices">${slicesHtml}</g>
  ${centerText}
  <g class="usx-chart-legend">${legendHtml}</g>
</svg>`;
}

// ─── Sparkline ───────────────────────────────────────────────────────

function renderSparkline(spec: ChartSpec): string {
  const width = spec.width || 160;
  const height = spec.height || 40;
  const pad = 4;

  const chartW = width - pad * 2;
  const chartH = height - pad * 2;

  const maxVal = Math.max(...spec.data, 0);
  const minVal = Math.min(...spec.data, 0);
  const range = maxVal - minVal === 0 ? 1 : maxVal - minVal;
  const n = spec.data.length;

  const points = spec.data.map((val, i) => {
    const x = pad + (n > 1 ? (i / (n - 1)) * chartW : chartW / 2);
    const y = pad + chartH - ((val - minVal) / range) * chartH;
    return `${x.toFixed(1)},${y.toFixed(1)}`;
  });

  const pathD = `M ${points.join(" L ")}`;
  const lastPoint = points[points.length - 1].split(",");

  return `<svg viewBox="0 0 ${width} ${height}" xmlns="http://www.w3.org/2000/svg" class="usx-chart usx-chart--sparkline" role="img" aria-label="Sparkline">
  <path d="${pathD}" fill="none" stroke="#00e5ff" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" />
  <circle cx="${lastPoint[0]}" cy="${lastPoint[1]}" r="3" fill="#00e5ff" />
</svg>`;
}
