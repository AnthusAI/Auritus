import { defineConfig } from "tsup";

export default defineConfig({
  entry: { embed: "src/index.ts" },
  format: ["iife", "esm"],
  globalName: "Auritus",
  outDir: "dist",
  clean: true,
  dts: true,
  sourcemap: true,
  outExtension({ format }) {
    return { js: format === "iife" ? ".js" : ".esm.js" };
  },
});
