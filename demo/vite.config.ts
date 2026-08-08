import { fileURLToPath } from "node:url";
import { defineConfig } from "vite";

// base: "/" for local dev; "/ziano/" for project GitHub Pages (set via env).
export default defineConfig({
  base: process.env.VITE_BASE ?? "/",
  // `host: true` binds 0.0.0.0 instead of localhost, so a phone on the same
  // Wi-Fi can open http://<your-lan-ip>:7070/. This page is a typography demo
  // whose whole point is how it renders on a real device — iOS Safari picks
  // different fallback faces from Chrome, and the sheet/tab layout bugs found
  // on 2026-08-07 only reproduced there. Without it vite listens on [::1] alone
  // and the phone can't reach it at all.
  server: { port: 7070, strictPort: true, host: true },
  preview: { port: 7070, strictPort: true, host: true },
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
