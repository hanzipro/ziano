# Visual smoke test

1. Build packages:
   ```bash
   uv run python -m cheritage.build shanggu-serif && uv run python -m cheritage.build shanggu-sans
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
   - **(c)** かな / 한글 / 简体 render from system fonts — no tofu boxes.

A reference screenshot (`smoke.png`, headless Chrome) sits next to this file, but
heritage-vs-MOE glyph shapes must be confirmed by a human — that is the point of
this test.
