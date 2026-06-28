# ziano — TODO

## 發布上線 checklist（2026-06-22 重新盤點）

現況：18 套 family 全 build 完成（`dist/`，每包帶 LICENSE）；npm 全在 `rc` tag
（shanggu rc.5、genki/lxgw/iansui/klee rc.1–2），`latest` 仍指舊 rc → **無穩定
0.1.0**。demo build 乾淨、預設已 genyo→genki。pytest 40 pass / 1 fail（缺 `py7zr`，
純 env）。

**Blocker（上線前必做）**

- [ ] **1. 定案 0.1.0 正式 roster** — genki 當預設、genyo 發 0.1.0「收尾不推廣」。
      確認哪些包上 `latest` 穩定版（見下方「源樣→源起」段落）。
- [ ] **2. 發 stable `0.1.0` 到 `latest` tag** — 不可逆 + 2FA，使用者執行。目前
      latest 還停在 rc（shanggu rc.3、其餘 rc.0）。
- [ ] **3. Demo `@rc → @latest`／收斂版本** — 見下方「switch `@rc`→`@latest`」段。
- [ ] **4. Demo 部署管線** — 無 CI、無 host 設定。決定 host（hanzi.pro？GitHub
      Pages `VITE_BASE=/ziano/`？）並接上自動部署。`vite build` 只打包 index +
      cdn-bench；其餘 *-test.html 是開發 harness，不出貨。
- [x] **5. README + docs/usage.md 對齊** — ✅ README roster 換成 genki（min 7／
      gothic 6 字重）＋補 Shanggu TC、加丹/月說明、GenYo 降 footnote；usage.md 早已
      用源起。commit `b1cee03`。

**收尾 / 決定要不要帶著上**

- [ ] 6. Shanggu base/TC `-tc` 後綴方向與 genyo 相反 → 命名決策（見下）。README 已
      就現況加註說明，但「後綴慣例」本身仍待你拍板。
- [ ] 7. Firefox 直排 `：；` 旋轉 — 已判定可接受先上（見下）。
- [ ] 8. 窄字集（Klee）skip 空 slice — 純優化（見下）。
- [ ] 9. `py7zr` 補進 dev deps，讓 pytest 全綠。

**本輪已完成（demo 打磨，非上線 blocker）**

- [x] Demo 小尺寸 responsive C1–C6（含直式 piano、cdn-bench 結果表橫捲）—— CDP
      實測 320–1280px 全斷點零水平溢出、桌機不變。
- [x] Dark mode 重構成 `light-dark()`（token 級逐一比對等價）＋ code terminal／
      cdn-bench ink 按鈕的 dark 邊界與可讀性修復。
- [x] box-sizing latent bug 根治（全站 border-box）。
- [x] dark-mode 模式寫進 workspace `web-style.md`／`CLAUDE.md`（已 push knowledge repo）。

---

## On stable 0.1.0: switch demo's floating CDN tag `@rc` → `@latest`

**Context:** the demo previews fonts via the floating `rc` dist-tag (`@rc`) so it
tracks each `npm publish --tag rc` without a code change. `@latest`/unversioned
can't be used during prerelease — `--tag rc` doesn't move the `latest` tag, so
they'd freeze at the first version. User-facing snippets + README stay **pinned**.

**Do (when 0.1.0 ships to the `latest` tag):**
- `demo/src/cdn.ts` — `DEMO_TAG` `'rc'` → `'latest'`, `VERSION` → `'0.1.0'`
- `demo/cdn-bench.html` — `PKG` `@rc` → `@latest`
- README/snippet pins follow the build version automatically.

Grep `DEMO_TAG` and `0.1.0-rc.0` to find every spot.


## Skip empty/near-empty slices for narrow-coverage fonts

**Context:** the slice table has ~108 `unicode-range` buckets (snapshot of Noto's
partition). Wide fonts (Shanggu, GenYo, LXGW) fill almost all of them, but a
narrow font like **Klee One** (~10k glyphs, JP-flavoured) covers nothing in many
slices. We still emit a `@font-face` + a woff2 for those — the woff2 is a valid
but near-empty file (.notdef only), and the `@font-face`'s `unicode-range` can
never match a glyph the font has.

**Do:** in `build.py` (and/or `cssgen.py`), when a slice's codepoints have **zero
intersection** with the font's cmap for a given weight, skip generating both the
woff2 and the `@font-face` block for that (weight, slice). Mirrors what Google
Fonts does (it omits ranges the font doesn't cover).

**Where:** `cheritage.coverage.cmap_codepoints` already gives the font's cmap;
intersect with `Slice.codepoints()`. Guard inside the per-slice loops of
`_build_vf` / `_build_static`, and filter the slice list passed to `generate_css`
per weight so CSS and files stay in sync.

**Payoff:** smaller Klee package, fewer dead `@font-face` rules. Mainly benefits
narrow-coverage fonts; wide fonts are barely affected.

**Test:** build `klee-one` and assert no `klee-one.*.woff2` exists for a slice
that is purely in a block Klee lacks (e.g. a CJK Ext-B-only slice), and that
`400.css` has fewer `@font-face` than the full 108.


## Vertical (直排): Firefox rotates `：；` — should stay upright

**Symptom:** in vertical mode Firefox rotates `：`(U+FF1A) and `；`(U+FF1B); they
should render upright. Chrome/Safari correct. Other punctuation fine. Deemed
可接受 to ship without — fix in a later pass. (Found 2026-06-15 via
`demo/vert-test.html`, case 「句讀位置」.)

**Cause:** both are UTR50 **Tr-class** ("rotate by default *unless* `vert`
substitutes them"). Shanggu's `vert`/`vrt2` lookups (#42, #43) have no rule for
them, so Firefox's strict UTR50 rotates; Chrome/Safari are lax → upright. Exactly
diantenjeom `docs/vertical-text.md` quirk #5.

**Fix:** identity self-substitution — add `uniFF1A → uniFF1A`, `uniFF1B → uniFF1B`
to the `vert`/`vrt2` lookup (diantenjeom's `_add_upright_self_substs` sentinel
trick). Firefox renders upright; Chrome/Safari unchanged (identity = no-op). Run
once on each base OTF **before slicing** so it propagates to every range-slice
containing `：；`. Re-verify with `demo/vert-test.html`.


## Shanggu: ship base + TC, drop JP (10 → 12 families)

**Decision (2026-06-15):** keep Shanggu in two cuts, drop JP entirely.
- **base (無附加名)** — *heritage-enhanced*: force-merges 新→舊 異體字 (内→內, 兑→兌,
  青→靑 …) even when the author typed the new codepoint. Already in roster as
  `shanggu-serif` / `shanggu-sans` (corrected to base OTF; pending rc.2).
- **TC (繁體中文標點版)** — *Unicode-faithful*: respects the encoded codepoint, still
  fully 舊字形 otherwise. NEW: add `shanggu-serif-tc` / `shanggu-sans-tc`.
- Measured difference base↔TC = **159 codepoints (0.35%)**, incl. common 内/争/兑/净/册;
  TC↔JP only 41 → JP not worth shipping.

**Cheap to add:** TC members live in the *same* `…VF_OTFs.7z` → reuse the same
`asset` + `asset_sha256`, same serif/sans slice tables; just 2 new roster entries.

**⚠️ Naming to resolve before building:** suffix direction is inverted vs GenYo —
GenYo `-tc` (丹) is the *more*-heritage cut, but Shanggu `-tc` (TC) is the *milder*
one. Decide: (a) suffix = upstream variant name, document per-package README
(leaning this); or (b) a self-describing suffix for Shanggu's milder cut.

**Publish:** base → rc.2 (corrected bytes); the 2 new TC → publish fresh at rc.2
for catalog consistency. Then per-package snippet handling in `cdn.ts` (Option A).


## 源樣 GenYo → 源起 Genki — 定案：改用體積較小的源起

**決定 (2026-06-15)：ziano 預設改用源起 Genki 取代源樣 GenYo。**
理由：兩者**視覺等同**（見下證據），但源起 woff2 **小 17–24%**⸺對主打速度的
webfont CDN 是淨勝。源樣已上 npm（rc.1）無法下架 → 仍發 `0.1.0` 正式版收尾，
但**不放進 demo**；demo 預設改推源起。

**體積（woff2 實測，ziano 出貨格式）：**
- 明體 L：GenYo 8.97 MB → Genki **6.80 MB（−24%）**
- 黑體 L：GenYo 6.42 MB → Genki **5.31 MB（−17%）**
- 為何斷筆反而小：構件一致、重複性高 → brotli 壓更兇（desub on/off 結果相同）。

**視覺等同（已驗證，結論不變）：**
- outline topology 差 86%（斷筆＝把思源連筆拆成兩段相鄰輪廓），但墨跡幾乎相同。
- 175 常用字 bbox 對齊後像素差中位數 5%、最差 16%（多/言/走，斜筆多）；目視仍只有
  邊緣 ≤1px 紅／青毛邊（均勻次像素位移），無結構性斷裂。

**待辦：**
- roster：新增 `genki-min`/`genki-gothic`（＋ TC：`genki-min-tc`/`genki-gothic-tc`？待確認），
  保留 `genyo-*`（仍需 build 來發 0.1.0 收尾）。
- ⚠️ **黑體 Genki 無 N(350) 字重**（GenYo Gothic 有）→ 換用即少掉 350。明體字重一致。
- demo：font 清單以 genki-* 取代 genyo-*（源樣不再出現）。
- 發佈（RC 輪，不發正式版；維持 `--tag rc`，demo 維持 `@rc`）：
  - **尚古 base 2 包 → `0.1.0-rc.2`**（修正 bytes，接續 rc 線）；
    **尚古 TC 2 包 → `0.1.0-rc.0`**（全新套件，從 rc.0 起）。
  - **Genki 4 包 → `0.1.0-rc.0`**（新預設）。
  - **GenYo → 晚點再發 `0.1.0` 正式版**（收尾、不推廣；本輪不動）。
  - 其餘（iansui/klee/lxgw）維持 rc.1，本輪不動。
  ⚠️ 不可逆＋2FA，由使用者執行。正式版 0.1.0（含 demo @rc→@latest）留待 GenYo 收尾時一起。

**評估工具（保留）：** `demo/genki-test.html`、`demo/genki-diff.html`；
字檔在 gitignore 的 `demo/public/genki-test/`。
