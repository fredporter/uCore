/**
 * @module utils/diagramHydrator
 * @description Dynamic client-side hydrator for diagrams and charts rendered in markdown.
 * Implements lazy loading of Mermaid.js (zero bundle impact for documents without diagrams)
 * and attaches sovereign export actions (Copy SVG, Download, View Source).
 */

let mermaidInitialized = false;

async function getMermaid() {
  const m = await import("mermaid");
  const mermaid = m.default || m;

  if (!mermaidInitialized) {
    mermaid.initialize({
      startOnLoad: false,
      suppressErrorRendering: true,
      securityLevel: "loose",
      theme: "base",
      themeVariables: {
        darkMode: true,
        background: "#0b1120",
        primaryColor: "#1e293b",
        primaryBorderColor: "#00e5ff",
        primaryTextColor: "#f8fafc",
        secondaryColor: "#0f172a",
        tertiaryColor: "#1e293b",
        lineColor: "#00e5ff",
        textColor: "#e2e8f0",
        mainBkg: "#0f172a",
        nodeBorder: "#00e5ff",
        clusterBkg: "#0b1120",
        clusterBorder: "#334155",
        defaultLinkColor: "#38bdf8",
        titleColor: "#f8fafc",
        edgeLabelBackground: "#0b1120",
        actorBorder: "#00e5ff",
        actorBkg: "#1e293b",
        actorTextColor: "#f8fafc",
        actorLineColor: "#64748b",
        signalColor: "#00e5ff",
        signalTextColor: "#f8fafc",
        labelBoxBkgColor: "#1e293b",
        labelBoxBorderColor: "#00e5ff",
        labelTextColor: "#f8fafc",
        loopTextColor: "#f8fafc",
        noteBorderColor: "#334155",
        noteBkgColor: "#1e293b",
        noteTextColor: "#f8fafc",
        fontFamily: "JetBrains Mono, monospace",
        fontSize: "13px",
      },
    });
    mermaidInitialized = true;
  }
  return mermaid;
}

let diagramCounter = 0;

/**
 * Hydrate all diagrams, charts, and teletext displays within a DOM container.
 */
export async function hydrateDiagrams(container: HTMLElement | null): Promise<void> {
  if (!container || typeof window === "undefined") return;

  // 1. Hydrate Mermaid diagrams
  const mermaidEls = container.querySelectorAll<HTMLElement>(
    '.md-diagram--mermaid:not([data-hydrated="true"])',
  );

  if (mermaidEls.length > 0) {
    try {
      const mermaid = await getMermaid();
      for (const el of Array.from(mermaidEls)) {
        el.setAttribute("data-hydrated", "true");
        const codeEl = el.querySelector(".mermaid");
        const rawCode = (codeEl?.textContent || "").trim();
        if (!rawCode) continue;

        const id = `mermaid-svg-${Date.now()}-${++diagramCounter}`;
        try {
          const { svg } = await mermaid.render(id, rawCode);
          el.innerHTML = `
            <div class="md-diagram__viewport">${svg}</div>
            <div class="md-diagram__source" style="display: none;"><pre><code>${escapeHtml(rawCode)}</code></pre></div>
          `;
          attachToolbar(el, "Mermaid Diagram", rawCode);
        } catch (err: any) {
          el.innerHTML = `
            <div class="md-diagram__error">
              <span class="material-symbols-outlined">warning</span>
              <span>Diagram Syntax Error</span>
            </div>
            <div class="md-diagram__source"><pre><code>${escapeHtml(rawCode)}</code></pre></div>
          `;
        }
      }
    } catch (e) {
      console.warn("Could not load or execute Mermaid:", e);
    }
  }

  // 2. Hydrate Declarative Charts
  const chartEls = container.querySelectorAll<HTMLElement>(
    '.md-diagram--chart:not([data-hydrated="true"])',
  );
  for (const el of Array.from(chartEls)) {
    el.setAttribute("data-hydrated", "true");
    const rawEncoded = el.getAttribute("data-chart-raw") || "";
    const rawCode = rawEncoded ? decodeURIComponent(rawEncoded) : "";
    attachToolbar(el, "SVG Chart", rawCode);
  }

  // 3. Hydrate Teletext / GridCore blocks
  const teletextEls = container.querySelectorAll<HTMLElement>(
    '.md-diagram--teletext:not([data-hydrated="true"])',
  );
  for (const el of Array.from(teletextEls)) {
    el.setAttribute("data-hydrated", "true");
    attachCopyTextToolbar(el, "Teletext Grid");
  }
}

function escapeHtml(text: string): string {
  return text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function attachToolbar(el: HTMLElement, label: string, rawSource: string) {
  const existing = el.querySelector(".md-diagram__toolbar");
  if (existing) existing.remove();

  const toolbar = document.createElement("div");
  toolbar.className = "md-diagram__toolbar";

  // Label tag
  const labelEl = document.createElement("span");
  labelEl.className = "md-diagram__label";
  labelEl.textContent = label;
  toolbar.appendChild(labelEl);

  // Actions wrapper
  const actions = document.createElement("div");
  actions.className = "md-diagram__actions";

  // Copy SVG
  const copyBtn = document.createElement("button");
  copyBtn.type = "button";
  copyBtn.className = "md-diagram__btn";
  copyBtn.title = "Copy SVG markup to clipboard";
  copyBtn.innerHTML = `<span class="material-symbols-outlined" style="font-size: 14px;">content_copy</span> SVG`;
  copyBtn.onclick = async () => {
    const svgEl = el.querySelector("svg");
    if (svgEl) {
      const svgMarkup = svgEl.outerHTML;
      await navigator.clipboard.writeText(svgMarkup);
      copyBtn.innerHTML = `<span class="material-symbols-outlined" style="font-size: 14px;">check</span> Copied`;
      setTimeout(() => {
        copyBtn.innerHTML = `<span class="material-symbols-outlined" style="font-size: 14px;">content_copy</span> SVG`;
      }, 2000);
    }
  };
  actions.appendChild(copyBtn);

  // Download SVG
  const dlBtn = document.createElement("button");
  dlBtn.type = "button";
  dlBtn.className = "md-diagram__btn";
  dlBtn.title = "Download SVG";
  dlBtn.innerHTML = `<span class="material-symbols-outlined" style="font-size: 14px;">download</span>`;
  dlBtn.onclick = () => {
    const svgEl = el.querySelector("svg");
    if (svgEl) {
      const blob = new Blob([svgEl.outerHTML], { type: "image/svg+xml" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `diagram-${Date.now()}.svg`;
      a.click();
      URL.revokeObjectURL(url);
    }
  };
  actions.appendChild(dlBtn);

  // Toggle raw source code
  if (rawSource) {
    const srcBtn = document.createElement("button");
    srcBtn.type = "button";
    srcBtn.className = "md-diagram__btn";
    srcBtn.title = "Toggle Markdown Source";
    srcBtn.innerHTML = `<span class="material-symbols-outlined" style="font-size: 14px;">code</span>`;
    srcBtn.onclick = () => {
      let srcBox = el.querySelector<HTMLElement>(".md-diagram__source");
      if (!srcBox) {
        srcBox = document.createElement("div");
        srcBox.className = "md-diagram__source";
        srcBox.innerHTML = `<pre><code>${escapeHtml(rawSource)}</code></pre>`;
        el.appendChild(srcBox);
      } else {
        srcBox.style.display = srcBox.style.display === "none" ? "block" : "none";
      }
    };
    actions.appendChild(srcBtn);
  }

  toolbar.appendChild(actions);
  el.insertBefore(toolbar, el.firstChild);
}

function attachCopyTextToolbar(el: HTMLElement, label: string) {
  const existing = el.querySelector(".md-diagram__toolbar");
  if (existing) existing.remove();

  const toolbar = document.createElement("div");
  toolbar.className = "md-diagram__toolbar";

  const labelEl = document.createElement("span");
  labelEl.className = "md-diagram__label";
  labelEl.textContent = label;
  toolbar.appendChild(labelEl);

  const actions = document.createElement("div");
  actions.className = "md-diagram__actions";

  const copyBtn = document.createElement("button");
  copyBtn.type = "button";
  copyBtn.className = "md-diagram__btn";
  copyBtn.title = "Copy teletext block to clipboard";
  copyBtn.innerHTML = `<span class="material-symbols-outlined" style="font-size: 14px;">content_copy</span> Copy`;
  copyBtn.onclick = async () => {
    const code = el.querySelector("code")?.textContent || el.textContent || "";
    await navigator.clipboard.writeText(code);
    copyBtn.innerHTML = `<span class="material-symbols-outlined" style="font-size: 14px;">check</span> Copied`;
    setTimeout(() => {
      copyBtn.innerHTML = `<span class="material-symbols-outlined" style="font-size: 14px;">content_copy</span> Copy`;
    }, 2000);
  };
  actions.appendChild(copyBtn);

  toolbar.appendChild(actions);
  el.insertBefore(toolbar, el.firstChild);
}
