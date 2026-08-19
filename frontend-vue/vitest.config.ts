import { defineConfig, mergeConfig } from "vitest/config";

import viteConfig from "./vite.config";

export default mergeConfig(
  viteConfig,
  defineConfig({
    test: {
      // Playwright owns browser/golden specs; Vitest owns unit tests.
      exclude: ["e2e/**", "node_modules/**", "dist/**"],
    },
  }),
);
