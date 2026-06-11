# Visual smoke test

1. Build packages:
   ```bash
   for f in shanggu-serif shanggu-sans genyo-min genyo-gothic; do
     uv run python -m cheritage.build "$f"
   done
   ```
2. Serve the repo root (the page imports `../../dist/...`):
   ```bash
   python -m http.server 8000
   ```
3. Open http://localhost:8000/tests/visual/
4. Confirm by eye:
   - **(a)** 戶 / 骨 / 直 / 過 / 青 show 傳承 (old) forms, not MOE standard forms;
   - **(b)** the 字重 900 line is visibly heavier than the weight-300 line
     (proves the variable-weight axis works from a single woff2);
   - **(c)** かな / 한글 / 简体 render from system fonts — no tofu boxes;
   - **(d)** GenYo Min/Gothic (月版/TW, neutral cut) render and read as a *milder*
     alternative to Shanggu's full 舊字形 — and the 400 vs 700 GenYo lines prove the
     separate static per-weight files load.

A reference screenshot (`smoke.png`, headless Chrome) sits next to this file, but
heritage-vs-MOE glyph shapes must be confirmed by a human — that is the point of
this test.
