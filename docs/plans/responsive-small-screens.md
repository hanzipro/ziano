# Plan — demo 小尺寸設備 responsive（media queries）

**目標**：`demo/index.html`（＋次要 `cdn-bench.html`）在手機／平板上正常瀏覽。
現況：全站只有 **1 條** `@media`（`usage.css:172`，把 config-rail 疊放）＋少數
`clamp()/vw`；其餘版面是桌機固定寬，窄螢幕會橫向溢出、貼邊、欄位擠爆。

**遵循**：`web-style.md`（logical properties、`@media (width < …)` 區間語法、
多行 list 值、token 驅動、低 specificity）。比照既有 `usage.css` 的 `@media
(width < 52rem)` 寫法——**那是本 repo 的範本，照抄它的風格**。

---

## 斷點策略（literal rem，註解標明；同值跨檔重用＝media 版的 token）

`@media` 條件不能吃 `var()`，所以斷點是**固定 rem**，靠「同值重用＋註解」維持一致。
全站只用兩個斷點：

| 斷點 | 約 px | 語意 | 觸發 |
|---|---|---|---|
| `width < 52rem` | ~832 | **平板以下**：雙欄 → 單欄堆疊 | usage/playground 疊 aside、faq 3→2 欄、hero 卡片瘦身 |
| `width < 34rem` | ~544 | **手機**：再壓縮 | faq →1 欄、header 收合、aside 視情況隱藏、piano 變矮 |

`52rem` 沿用 usage.css 既有值，不要另創第三個近似斷點。

---

## Step 0 — 基礎：容器留 gutter（最關鍵，先做）

`container.css` 把 `body > *`／各 section 限寬 `--max-w-layout` 並 `margin:auto`，
但**沒有 `padding-inline`** → < 68rem 內容貼邊。加一個 `--gutter` token：

- `variables.css` `:root`：新增
  ```css
  --gutter: clamp(1rem, 4vw, 2rem); /* 容器左右最小留白；窄螢幕收到 1rem */
  ```
- `container.css` 的 `:where(body > *, #playground, #usage, #faq, main > article > dl)`
  規則加 `padding-inline: var(--gutter);`
  - 全寬 `::before/::after`（`inline-size: 100vw`）不受影響，divider 仍滿版。
  - hero `dl`（同選擇器命中）也一起得到 gutter。
- **橫向溢出守門**：`100vw` 在有實體捲軸的系統會比可視寬多出捲軸寬 → 橫捲。
  `root.css` 的 `:where(:root)` 加 `scrollbar-gutter: stable;`，並於 `body`（reset 或
  root）加 `overflow-x: clip;` 作保險（`clip` 不建立捲動容器，比 `hidden` 安全）。

驗收：360px 寬時各 section 內容左右各留 ≥1rem，無橫向捲軸。

---

## Step 1 — Header（`layout.css`）

固定 `inline-size: var(--max-w-layout)`（68rem）會直接溢出。

- `body > header`：`inline-size: var(--max-w-layout)` → 
  `inline-size: min(100%, var(--max-w-layout)); padding-inline: var(--gutter);`
  （置中的 `translateX(-50%)` 保留；寬度改成可收縮。）
- h1 的 `&::after` accent 線 `inset-inline-end: -2.5rem` 在窄螢幕會戳出容器 →
  併入 padding 後通常 OK；若仍溢出，`@media (width < 34rem)` 內縮短到 `-1rem`
  或 `inline-size: 3rem`。
- `@media (width < 34rem)`：menu 收合
  - `h1 small`（傳承字形副標）`display: none` 或縮字；
  - menu `gap` 1rem → .5rem，nav 連結 `font-size` 再降一階；
  - 若仍擠，nav 文字連結（GitHub/npm 等）`display:none`，**只保留暗色切換鈕**
    （主要功能鍵），比照「空間不夠可不留」原則。

驗收：320–414px header 不溢出、暗色鈕可按、wordmark 不破。

---

## Step 2 — Hero（`hero.css`）

`figure`／glyph 已是 `min(60vh,30rem)`／`min(64vh,32rem)` 流體，基本 OK。問題在
roster 卡片 `dl`：`padding: 5rem 0 1rem 60%`（左留 60% 給絕對定位的 `dt` 5rem 大字），
窄螢幕 dd 文字被擠進右側 40% → 過窄。

- `@media (width < 52rem)`：
  ```css
  body > main > article dl {
    padding-inline-start: 40%;   /* 大字佔比降一點 */
  }
  body > main > article dl dt {
    font-size: 3.5rem;           /* 5rem → 3.5rem */
  }
  ```
- `@media (width < 34rem)`：
  - 改成上下堆疊更穩：`dt` 由 `position:absolute` 改回流內
    （`position: static; font-size: 3rem;`），`dl` `padding: 3rem var(--gutter) 1rem;`
    讓字名在上、說明在下。**改動只在這條 media 內**，桌機版面不動。
  - `figure` `block-size: min(60vh,30rem)` → 手機可再收 `min(42vh, 18rem)`，
    避免單一大字佔滿首屏。

驗收：手機上每張字體卡字名＋說明都讀得到，不重疊。

---

## Step 3 — Playground（`playground.css`）— aside 可隱

`display:flex; flex-wrap:wrap`，aside 固定 `20rem`、`.panes flex:1`、`.Piano`
full-bleed `order:-1`。窄螢幕 aside（20rem）會 wrap 到 panes 下方但仍佔滿寬。

- `@media (width < 52rem)`：
  - `#playground { gap: 1.5rem; }`（4rem 太寬）
  - `#playground aside { inline-size: 100%; }`（控制列滿寬堆疊在 specimen 下）
  - `.panes` 的 `max-block-size: clamp(20rem, 40rem, …)` 在窄螢幕沒問題，但確認
    specimen 有合理高度：`min-block-size: 60vh`。
- `@media (width < 34rem)` — **依你的指示：空間不夠就不留 aside**
  - 字重等控制非展示必需（字體從 hero 卡片選、specimen 仍可編輯），故
    `#playground aside { display: none; }`，只留 specimen 滿屏展示字體。
  - 取捨記錄在註解：`/* 手機：控制列讓位給字體展示，比照 plan Step 3 */`
  - 折衷選項（若想保留調字重）：只隱藏 `.chips/.meta/.status`，保留字重 slider。
    預設採「全隱」，要保留 slider 再放寬。

驗收：手機 playground 能看到 piano 背景＋可編輯的字體 specimen，版面不爆。

---

## Step 4 — Usage（`usage.css`）— 已有 52rem，補手機

已有 `@media (width < 52rem)` 把 config-rail（`> aside`）由 sticky 改 `static`、
滿寬堆疊——**保留**。補手機段：

- `@media (width < 34rem)`：依你的指示，config generator 是「產生器」，輸出已反映在
  guide 的程式碼終端機，手機空間不夠可整個收起：
  ```css
  #usage > aside { display: none; } /* 手機：產生器讓位，終端機顯示預設片段即可 */
  ```
  - 終端機 `pre` 已 `overflow-x:auto`，長行可橫捲，OK。
  - `table`（font-display 對照）`font-size` 降一階、`td:first-child` 取消
    `white-space:nowrap` 以免撐爆：`white-space: normal;`
  - `#usage { gap: 0; }`（單欄後不需欄距）

驗收：手機 usage 指南全文可讀、程式碼區塊可橫捲、無溢出。

---

## Step 5 — FAQ（`faq.css`）

`.explainer { column-count: 3 }` 雜誌三欄在手機完全不可讀。

- `@media (width < 52rem)`：`.explainer { column-count: 2; column-gap: 2rem; }`
- `@media (width < 34rem)`：`.explainer { column-count: 1; }`
  （`h2 { break-before: column }` 在單欄自然失效，無副作用。）
- `.credits ul` 已 `flex-wrap:wrap`，OK；確認窄螢幕 `gap` 不過大（可降 `1rem 1.5rem`）。

驗收：手機 FAQ 單欄順讀，致謝清單正常 wrap。

---

## Step 6 — Piano（`piano.css`）— **永遠保留**，手機轉「直式」縮小

**定位（使用者指示）**：piano 是展示頁**最重要的裝飾**，無論如何保留，不可隱藏。
手機橫式 120 鍵 ÷ 375px ≈ 3px/鍵太糊 → **改直式**（鍵盤豎排於側邊），尺寸縮小。

**為何幾乎免費**：piano 幾何全是 `%` ＋ **logical properties**——
`--wkstep`/`--pos` 用 `%`、白鍵 `flex:1`＋`block-size:100%`、黑鍵
`inset-inline-start: var(--pos)`／`inset-block-start:0`／`inline-size`／`block-size:62%`。
對 `.Piano` 加 `writing-mode: vertical-rl`，inline 軸由「左右」轉成「上下」：
白鍵自動豎排、黑鍵 `--pos` 落在正確的縱向位置。**`piano.ts` 完全不動**
（`--pos`/`--wkstep` 是 `%`、strike 用 `scale` 非 translate，皆與方向無關）。

**唯一物理軸 gotcha**：黑鍵置中用 `transform: translateX(-50%)`（physical X）。
直式時置中軸變縱向 → 在 media 內覆寫成 `translateY(-50%)`。這是唯一需要改的一行。

**草案（`@media (width < 34rem)`）**：
```css
.Piano {
  writing-mode: vertical-rl;     /* inline 軸轉縱向 → 鍵盤豎排 */
  inline-size: 100vh;            /* 沿縱向鋪滿視高（原本是 100vw 橫向滿版） */
  block-size: min(5rem, 22vw);   /* 鍵盤厚度（橫向薄條），縮小尺寸 */
  margin-inline: 0;              /* 取消橫向 full-bleed 負邊距 */
  margin-block: calc(50% - 50vh); /* 改成縱向滿出視高（直式 full-bleed 的對偶） */
}
.Piano kbd.black {
  transform: translateY(-50%);   /* 置中軸由 X→Y（直式唯一物理修正） */
}
```

**一個待定的版面決策（實作時拍板）**：直式 piano 要
- (A) **留在 `#playground` flow 內**當側欄（`order:-1` 已使它排在最前 → 變左側豎條，
  specimen/aside 排其右）。改動最小、scope 仍限 playground。**建議採此**。
- (B) `position: fixed` 貼視窗邊緣當全站豎條（橫跨所有 section）。視覺更搶眼，但
  scope 從 playground 擴大到全頁，sticky→fixed 行為變化大、風險高。
先做 (A)，覺得不夠才升 (B)。

驗收：手機 piano 以**直式縮小**呈現、可見且好看、不擋內容、不造成橫/縱向溢出
（配 Step 0 的 `overflow-x: clip`）；打字仍正確點亮對應鍵（JS 未改，行為不變）。

---

## Step 7 — cdn-bench.html（`bench.css`）— ✅ DONE（commit `31660be`）

cdn-bench 透過 `src/bench.css` manifest `@import` 共用 partials，所以 header／gutter／
overflow 守門／dark-mode 全部從 C1–C2 免費繼承。本步實際補的：
- **結果表 7 個 nowrap 欄** 包進 `.results-scroll`（`role=region` + `tabindex=0`，可鍵盤
  捲動），手機改框內橫向捲動而非溢出頁面。
- **dark-mode ink 控件修復**：per-CDN 按鈕與 `.badge` 原用 `--palette-text-inverse`
  （light-dark 重構後在 dark 翻成 ink → 深字埋進深底），改固定淺色文字 + 淡 hairline。
- 控制列本就 `flex-wrap`、`hgroup` 已 `max-inline-size`，無需再動。

驗收（CDP 375/768/1280 × 明暗）：`docScrollW==viewport` 全綠、按鈕/徽章 dark 可讀。

---

## 驗收方式（whole）

1. `pnpm --dir demo dev`，Chrome DevTools device toolbar 跑 **320 / 375 / 414 /
   768 / 1024px**，逐 section 對照各 Step 驗收點。
2. 重點檢查：**無水平捲軸**（Step 0 守門）、暗色模式兩個斷點都不破、
   `:has()`/sticky 行為正常。
3. 兩主題 × 兩斷點各截一張，回貼確認。
4. `pnpm --dir demo build` 仍綠（CSS 純增 media 區塊，風險低）。

## 落地順序（建議 commit 切分）

- C1：Step 0（gutter＋overflow 守門）— 地基，獨立可驗。
- C2：Step 1 header。
- C3：Step 2 hero。
- C4：Step 3–4 playground＋usage（aside 處理）。
- C5：Step 5–6 faq＋piano。
- （C6：Step 7 bench，可延後。）

每條 commit 後在對應斷點手測再進下一條；全程只在 `@media` 區塊內加規則，
桌機版面零改動（低迴歸風險）。
</content>
</invoke>
