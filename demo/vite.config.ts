import { fileURLToPath } from "node:url";
import { defineConfig } from "vite";

// base: "/" for local dev; "/ziano/" for project GitHub Pages (set via env).
export default defineConfig({
  base: process.env.VITE_BASE ?? "/",
  server: { port: 7070, strictPort: true },
  preview: { port: 7070, strictPort: true },
  build: {
    // Each HTML page is a build entry so Vite processes, hashes and rewrites its
    // tags. index.html (the ziano page) bundles from src/main.ts; cdn-bench.html
    // bundles from src/cdn-bench.ts and links src/bench.css (which shares partials
    // with index.html).
    rollupOptions: {
      input: {
        index: fileURLToPath(new URL("./index.html", import.meta.url)),
        "cdn-bench": fileURLToPath(new URL("./cdn-bench.html", import.meta.url)),
      },
    },
  },
});
