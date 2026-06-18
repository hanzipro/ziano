# Webfont emoji 破圖（Safari tofu）— unicode-range 沒跟 cmap 取交集

> 一句話：`@font-face` 的 `unicode-range` 不可以 claim 字體沒有的碼點。Safari 會認帳並渲染
> `.notdef`，不 fall through。修法 = 每片 range ∩ 字體 cmap、丟空片（`slices.prune_slices`，
> commit `4c83d48`）。

## 症狀（快速辨識）

- 某些 emoji 在用到本站 webfont 的網頁上 **Safari 顯示空白方塊 / tofu，Chrome 正常**；
  別人沒用這些字體的網頁一切正常。最早抓到 **🌞 U+1F31E**，後來也見 😊 🎹 🔥。
- 只在字族 fallback 鏈含到出問題的 webfont 時才發生（例：`--font-default` 含 `'Shanggu Sans'`
  → 連深色切換鈕的 🌞 都破）。
- 旁支：某 BMP 符號（`☀ U+2600` 等）顯示**單色**而非彩色 —— 這個**不是 bug**，bare
  `U+2600` 在 Unicode 預設就是「文字呈現」，到處都單色。

## 根因

切片配方（Google **nam-files**，per-script、font-independent）把 emoji / PUA / 部分外語碼點
也分進某些片；CJK 字體在那幾片是**空的**（zero glyph）。但 `cssgen._face` 早期直接吐
`unicode-range: {slice.unicode_range}`（原始配方），**沒跟字體實際 cmap 取交集** → 空片也
claim 了整段 range，woff2 卻是空的（cmap=0、~1.3 KB）。

- **Safari**：認 bare `unicode-range`，即使下載的 woff2 沒那 glyph，也渲染 `.notdef`，
  **不** fall through 到系統 emoji 字體 → tofu。
- **Chrome**：用 `unicode-range ∩ cmap`，空片 → 不覆蓋該碼點 → fall through → 正常。
- 同碼點在「空片」破、在「非空片」不破：非空片即使缺這個字，∩ cmap 仍把它排除掉。

## 為什麼配方含 emoji 不是錯（不要急著怪 nam-files）

CJK 字體本來就收了一批「掛在符號/emoji 區塊、但**當文字用**」的單色字形，這些**該**由字體
自己畫，不該跳彩色 emoji。實測尚古/源起：

- emoji 區塊（≥U+1F000）905 個碼點裡，字體只有 **58** 個（如外框字母 🅰🅱）。
- BMP `U+2190–2BFF`（★ ☆ → ← ☎ ♥ ☀…）674 個裡，字體有 **367** 個。

配方把整段連續區間圈進來，是讓字體服務它**有**的那些；**沒有**的（真彩色 emoji 🌞😊…847 個）
就該被 prune 掉、回落系統。問題從來不是「配方含 emoji」，是「**claim 了字體沒有的**」。

## 修法

`src/ziano/slices.py::prune_slices(slices, cmap)`：每片 `unicode_range ∩ 字體 cmap`，丟掉空片
（保留原 index）。`build_family` 在 CSS-gen + subset 前算一次 cmap 並套用。等於補上
**GF / Noto 一直在做、nam-files 本身不負責的「∩ cmap」那一步**。

- 效果：尚古 120 → **109** 片（丟 emoji 1–5、PUA 9–11、孟/阿/希 94–96），覆蓋滿的 CJK 大片
  byte-identical。
- 對照：Google Noto CJK 線上 CSS 早就是 range ∩ cmap → Noto Sans TC **105** 片、尚古 109 片，
  都不是配方的 120；差數＝各自字體覆蓋不同。

## 快速診斷指令

```bash
ID=shanggu-sans; CP=0x1F31E   # 換成出問題的字 + 碼點
# 1) 線上 @rc 的 CSS 有沒有 claim 這個碼點？
curl -s "https://cdn.jsdelivr.net/npm/@hanzi.pro/webfonts-$ID@rc/swap.css" \
 | python3 -c "import sys,re;cp=$CP
def cov(r):
 for t in r.lower().split(','):
  t=t.strip().replace('u+','');
  if '-' in t: lo,hi=t.split('-'); 
  else: lo=hi=t
  if int(lo,16)<=cp<=int(hi,16): return True
print(any(cov(r) for r in re.findall(r'unicode-range:\s*([^;]+);',sys.stdin.read())))"
# 2) claim 它的那片 woff2 是不是空的？（cmap=0 → 就是這個 bug）
python3 -c "from fontTools.ttLib import TTFont; print(len(TTFont('x.woff2').getBestCmap() or {}))"
# 3) 源字體到底有沒有這個 glyph？
python3 -c "from fontTools.ttLib import TTFont; print($CP in (TTFont('src.otf').getBestCmap() or {}))"
```

## 相關檔案

- `src/ziano/slices.py` — `prune_slices`（修法本體）
- `src/ziano/build.py` — `build_family` 套用點
- `src/ziano/cssgen.py` — 吐 `unicode-range` 的地方
- `tests/test_slices.py` — prune 單元測試；`tests/test_build.py` — build 回歸斷言
  （`no emoji range` / `no slice-5 woff2`）
