import vue from "@vitejs/plugin-vue";
import path from "path";
import { createRequire } from "node:module";
import { defineConfig } from "vite";
import { VitePWA } from "vite-plugin-pwa";

const PORT = parseInt(process.env.VITE_PORT || "5175", 10);
const API_ORIGIN = process.env.VITE_API_ORIGIN || "http://localhost:8484";
const CODE_ROOT = path.resolve(__dirname, "../..");

const require = createRequire(import.meta.url);
const fontAssetRoots = [
  "material-symbols/outlined.css",
  "@fontsource/inter/400.css",
  "@fontsource/jetbrains-mono/400.css",
  "@fontsource/merriweather/400.css",
  "@fontsource/press-start-2p/400.css",
  "@fontsource/vt323/400.css",
].map((entry) => path.dirname(require.resolve(entry)));

export default defineConfig({
  plugins: [
    vue({
      template: {
        compilerOptions: {
          // Treat iconify-icon as a custom element (not a Vue component)
          isCustomElement: (tag) => tag === "iconify-icon",
        },
      },
    }),
    VitePWA({
      registerType: "autoUpdate",
      // Off during normal development: a service worker in the dev loop serves
      // stale assets after edits. The standalone install path opts in with
      // UCORE_PWA_DEV=1, which scripts/enable-engineering-https.sh sets.
      devOptions: {
        enabled: process.env.UCORE_PWA_DEV === "1",
        type: "module",
        navigateFallback: "index.html",
      },
      manifest: {
        name: "uCore",
        short_name: "uCore",
        description: "Local-first uDOS workspace and developer environment",
        theme_color: "#111318",
        background_color: "#111318",
        display: "standalone",
        start_url: "/",
        icons: [
          { src: "/icon-192.png", sizes: "192x192", type: "image/png" },
          { src: "/icon-512.png", sizes: "512x512", type: "image/png" },
          { src: "/icon-1024.png", sizes: "1024x1024", type: "image/png" },
        ],
      },
      workbox: {
        navigateFallback: "/index.html",
        maximumFileSizeToCacheInBytes: 4 * 1024 * 1024,
        runtimeCaching: [{
          urlPattern: ({ url }) =>
            url.pathname.startsWith("/api/workspace") ||
            url.pathname.startsWith("/api/editor/files") ||
            url.pathname.startsWith("/api/system/settings") ||
            url.pathname.startsWith("/api/user/preferences") ||
            url.pathname.startsWith("/api/identity"),
          handler: "NetworkFirst",
          options: { cacheName: "ucore-workspace", networkTimeoutSeconds: 3, expiration: { maxEntries: 100, maxAgeSeconds: 86400 } },
        }],
      },
    }),
  ],
  resolve: {
    alias: [
      // Local src alias
      { find: "@", replacement: path.resolve(__dirname, "src") },
      // Cross-repo aliases (resolve to ~/Code/<repo>)
      { find: "@uCodePlus", replacement: path.resolve(CODE_ROOT, "uCodePlus") },
      {
        find: "@HomeNest",
        replacement: path.resolve(CODE_ROOT, "uConnect/homenest-console"),
      },
      {
        find: "@usxd-browser",
        replacement: path.resolve(CODE_ROOT, "uConnect/usxd-browser"),
      },
      {
        find: "@usx-pkg",
        replacement: path.resolve(CODE_ROOT, "uConnect/packages/usx"),
      },
      {
        find: "@udos/usx-tokens",
        replacement: path.resolve(__dirname, "../packages/usx-tokens"),
      },
      // Subpath alias (listed first) so @udos/gridcore/<module> resolves to the
      // canonical source as a leaf import — avoids pulling the full index/bridge
      // into the frontend type-check.
      {
        find: /^@udos\/gridcore\/(.+)$/,
        replacement: path.resolve(CODE_ROOT, "uCode/packages/gridcore/src/$1"),
      },
      {
        find: "@udos/gridcore",
        replacement: path.resolve(
          CODE_ROOT,
          "uCode/packages/gridcore/src/index.ts",
        ),
      },
      {
        find: "@udos/viewport-renderer",
        replacement: path.resolve(
          CODE_ROOT,
          "uCode/packages/viewport-renderer/src/index.ts",
        ),
      },
    ],
  },
  server: {
    port: PORT,
    strictPort: true,
    host: "localhost",
    fs: { allow: [path.resolve(__dirname, ".."), ...fontAssetRoots] },
    hmr: { host: "localhost" },
    proxy: {
      // Route API calls to aiohttp backend in local dev.
      "/api": {
        target: API_ORIGIN,
        changeOrigin: true,
        ws: true,
      },
      "/snackmachine": {
        target: API_ORIGIN,
        changeOrigin: true,
      },
    },
  },
});
