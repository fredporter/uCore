/**
 * @module router
 * @description Vue Router 4 — canonical surface routes.
 * Mirrors the React Router config from the legacy frontend.
 * Enhanced with Dev Mode guard that watches for toggle changes.
 */
import {
  createRouter,
  createWebHistory,
  type RouteRecordRaw,
} from "vue-router";
import DashboardSurface from "../surfaces/dashboard/DashboardSurface.vue";
import WorkflowSurface from "../surfaces/workflow/WorkflowSurface.vue";

const routes: RouteRecordRaw[] = [
  {
    path: "/",
    name: "dashboard",
    component: DashboardSurface,
    meta: { title: "Mission Control", icon: "home" },
  },
  {
    path: "/assistui/:pathMatch(.*)*",
    redirect: (to) => {
      const tab = String(to.query.tab || "chat");
      if (["agents", "models", "budget"].includes(tab)) return "/snackbar?tab=ai";
      if (tab === "history") return "/snackbar?tab=logs";
      return "/";
    },
  },
  {
    path: "/intelligence/:pathMatch(.*)*",
    redirect: (to) => {
      const tab = String(to.query.tab || "chat");
      if (["agents", "models", "budget", "intel"].includes(tab)) return "/snackbar?tab=ai";
      if (tab === "history") return "/snackbar?tab=logs";
      return "/";
    },
  },
  {
    path: "/ucode/:pathMatch(.*)*",
    name: "ucode",
    component: () => import("../surfaces/ucode/UCodeSurface.vue"),
    meta: { title: "uCode", icon: "grid" },
  },
  {
    path: "/snackbar/:pathMatch(.*)*",
    name: "snackbar",
    component: () => import("../surfaces/snackbar/SnackbarSurface.vue"),
    meta: { title: "Snackbar", icon: "storefront" },
  },
  {
    path: "/server/:pathMatch(.*)*",
    redirect: (to) => ({
      path: `/snackbar${to.path.replace(/^\/server/, "")}`,
      query: to.query,
    }),
  },
  {
    path: "/developer/:pathMatch(.*)*",
    name: "developer",
    component: () =>
      import("../surfaces/developer/DeveloperSurface.vue"),
    meta: { title: "Developer", icon: "code" },
  },
  {
    path: "/workflow/:pathMatch(.*)*",
    name: "workflow",
    component: WorkflowSurface,
    meta: { title: "Workflow", icon: "workflow" },
  },
  {
    path: "/system/:pageId(s\\d{3}|p\\d{3})",
    name: "systempage",
    component: () => import("../surfaces/system/SystemPage.vue"),
    meta: { title: "System Page" },
  },
  {
    path: "/system/:pathMatch(.*)*",
    name: "system",
    component: () => import("../surfaces/system/SystemSurface.vue"),
    meta: { title: "System", icon: "settings" },
  },
  {
    path: "/snackmachine/:pathMatch(.*)*",
    redirect: (to) => {
      const tab = String(to.query.tab || "snacks");
      if (tab === "workflows") return "/workflow?tab=publish";
      if (tab === "vault") return "/workflow?tab=binder";
      if (tab === "mcp") return "/developer";
      if (tab === "variables") return "/system?tab=configuration";
      if (tab === "scheduler") return "/snackbar?tab=dashboard";
      return "/snackbar?tab=automation";
    },
  },
  {
    path: "/groovebox/:pathMatch(.*)*",
    name: "groovebox",
    component: () => import("../surfaces/groovebox/GrooveboxSurface.vue"),
    meta: { title: "Groovebox", icon: "music_note" },
  },
  {
    path: "/sonic/:pathMatch(.*)*",
    name: "sonic",
    component: () => import("../surfaces/sonic/SonicScrewdriverSurface.vue"),
    meta: { title: "SonicScrewdriver", icon: "usb" },
  },
  {
    path: "/browserui/:pathMatch(.*)*",
    name: "browserui",
    component: () => import("../surfaces/browserui/BrowserUISurface.vue"),
    meta: { title: "Browser", icon: "globe", hidden: true },
  },
  {
    path: "/documentation/:pathMatch(.*)*",
    name: "documentation",
    component: () =>
      import("../surfaces/documentation/DocumentationSurface.vue"),
    meta: { title: "Documentation", icon: "help" },
  },
  {
    path: "/teletext/:pathMatch(.*)*",
    redirect: "/ucode?tab=teletext",
  },
  {
    path: "/terminal/:pathMatch(.*)*",
    redirect: "/ucode?tab=terminal",
  },
  // Legacy redirects
  {
    path: "/gridui/:pathMatch(.*)*",
    redirect: (to) => `/ucode${to.path.replace("/gridui", "")}`,
  },
  {
    path: "/userver/:pathMatch(.*)*",
    redirect: (to) => `/snackbar${to.path.replace("/userver", "")}`,
  },
  // Legacy direct shortcuts
  {
    path: "/:pathMatch(s\\d{3}|p\\d{3})",
    redirect: (to) =>
      `/system/${String(to.params.pathMatch || "").toLowerCase()}`,
  },
];

export const router = createRouter({
  history: createWebHistory(),
  routes,
});

router.beforeEach((to) => {
  // Server owns the automation/skills runner; Workflow only invokes its items.
  if (
    to.path.startsWith("/workflow") &&
    ["automation", "automations", "feeds", "skills"].includes(String(to.query.tab || ""))
  ) {
    return { path: "/snackbar", query: { tab: "automation" } };
  }
});

const DYNAMIC_IMPORT_RELOAD_KEY = "ucore.router.dynamic-import-reload";
const RUNTIME_WARNING_KEY = "ucore.runtime.warning";

function publishRuntimeWarning(message: string) {
  if (typeof window === "undefined") return;
  window.sessionStorage.setItem(RUNTIME_WARNING_KEY, message);
  window.dispatchEvent(
    new CustomEvent("ucore:runtime-warning", {
      detail: { message },
    }),
  );
}

router.onError((error, to) => {
  const message = String((error as any)?.message || "");
  const isDynamicImportFailure =
    /Failed to fetch dynamically imported module/i.test(message) ||
    /Outdated Optimize Dep/i.test(message) ||
    /Importing a module script failed/i.test(message) ||
    /Loading chunk [\d]+ failed/i.test(message);

  if (!isDynamicImportFailure || typeof window === "undefined") {
    return;
  }

  const target =
    to?.fullPath ||
    `${window.location.pathname}${window.location.search}${window.location.hash}`;
  const lastReloadTarget = window.sessionStorage.getItem(
    DYNAMIC_IMPORT_RELOAD_KEY,
  );

  // Prevent infinite reload loops on persistent failures.
  if (lastReloadTarget === target) {
    window.sessionStorage.removeItem(DYNAMIC_IMPORT_RELOAD_KEY);
    publishRuntimeWarning(
      "A surface failed to load due to stale dev dependencies. Restart with 'pnpm -C frontend-vue run dev:clean -- --host 127.0.0.1 --port 4173'.",
    );
    return;
  }

  window.sessionStorage.setItem(DYNAMIC_IMPORT_RELOAD_KEY, target);
  window.location.assign(target);
});

// Update document title
router.afterEach((to) => {
  if (typeof window !== "undefined") {
    window.sessionStorage.removeItem(DYNAMIC_IMPORT_RELOAD_KEY);
  }

  const title = to.meta.title as string | undefined;
  document.title = title ? `${title} — uCore` : "uCore";
});
