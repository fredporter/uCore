import vue from "@vitejs/plugin-vue";
import path from "path";
import { defineConfig } from "vite";

const PORT = parseInt(process.env.VITE_PORT || "5175", 10);
const API_ORIGIN = process.env.VITE_API_ORIGIN || "http://localhost:8484";
const CODE_ROOT = path.resolve(__dirname, "../..");

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
  ],
  resolve: {
    alias: [
      // Local src alias
      { find: "@", replacement: path.resolve(__dirname, "src") },
      // Cross-repo aliases (resolve to ~/Code/<repo>)
      { find: "@uCode3", replacement: path.resolve(CODE_ROOT, "uCode3") },
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
    fs: { allow: [".."] },
    hmr: { host: "localhost" },
    proxy: {
      // Route API calls to aiohttp backend in local dev.
      "/api": {
        target: API_ORIGIN,
        changeOrigin: true,
      },
      "/snackmachine": {
        target: API_ORIGIN,
        changeOrigin: true,
      },
    },
  },
});
