# Web CJK 渲染:格式、hinting、gasp

ziano 在 2026-06 一輪除錯中釐清的東西。核心結論:**web CJK 走 glyf + gasp,不走
CFF2、也不指望逐字 hinting**——這正是 Noto CJK 在 Google Fonts 的作法,ziano 跟進。

相關:CFF2 在 Chrome 被畫細的根因見 `memory/cff2-renders-thin-in-browsers.md`。

## 1. 三種輪廓格式

`.otf` / `.ttf` 只是副檔名慣例;真正決定渲染的是裡面的**輪廓表**:

| 表 | 曲線 | 出身 | web 上 |
|---|---|---|---|
| **CFF** | 三次 (cubic) | PostScript / 印刷 | 靜態可用;Chrome 走 CoreText/DWrite,正常 |
| **CFF2** | 三次,變數 | OpenType 1.8 | ⚠️ Chrome 用 FreeType 畫,**比同輪廓的 glyf 細 ~1.6×**(看上面那篇) |
| **glyf** | 二次 (quad) | TrueType / Apple-MS | web 主流;Chrome+Safari 都正常 |

woff2 壓縮後 glyf 只比 CFF2 大 ~3%,所以 CFF 的「cubic 較精簡」優勢在 web 換不到好處。

## 2. Hinting:把筆畫對齊像素格

逐字 hinting = 讓 rasterizer 把豎/橫筆吸附到整數像素,小字級才銳利、筆畫均勻。
兩種載體:CFF 的宣告式 stem-hint + blue zones;TrueType 的命令式 bytecode
(`fpgm`/`prep`/`cvt` + 逐字指令)。CJK 要嘛 Adobe 手調(思源),要嘛 autohint
(ttfautohint,對密集漢字常幫倒忙)——沒人替 4 萬字認真上 hint。

實測各家(抽 300 漢字):

| 字型 | 表 | 逐字 hinting | gasp |
|---|---|---|---|
| **GenYo Min**(源樣,思源血統) | CFF | ✅ **99%** | ❌ |
| **Shanggu 原始 base** | CFF2 | ❌ 16%(上游 VF 合併掉光) | ❌ |
| **Shanggu 原始 base** | glyf | ❌ **0%** | ❌ |
| **Noto Sans TC**(GF webfont) | glyf | ❌ **0%** | ✅ |
| Adobe/Google 下載的 Noto/思源 OTF | CFF | ✅ 有 | — |

要點:**真正有逐字 hinting 的只有 CFF 血統的下載版**(GenYo、Noto-OTF);**所有走 web
的 glyf 版**(Noto-GF、Shanggu)**都沒 hinting**。「Noto 有沒有 hinting」永遠要問
「哪個發行版」。

## 3. gasp:渲染模式的開關

`gasp` = "Grid-fitting And Scan-conversion Procedure",一張十幾 bytes 的表,告訴引擎
(主要 Windows GDI/DirectWrite)**每個尺寸用哪種模式畫**。旗標:

| 旗標 | 值 | 意思 |
|---|---|---|
| GRIDFIT | 0x01 | 套用 hinting(對齊格線) |
| DOGRAY | 0x02 | 灰階反鋸齒 |
| SYM_GRIDFIT | 0x04 | ClearType 對稱格線對齊 |
| SYM_SMOOTH | 0x08 | ClearType 對稱平滑 |

Noto 用 **一筆涵蓋全尺寸、四旗標全開**:`{0xFFFF: 0x000F}`。對**無 hint** 的字,
GRIDFIT 形同空轉(沒指令可套),真正起作用的是 DOGRAY + SYM_SMOOTH —— 保證
「任何大小都平滑反鋸齒」,把舊路徑「鋸齒黑白小字」這個下限托住。macOS/Chrome 一律
AA、基本忽略 gasp,所以這純是 Windows 的保險,別處無害。

## 4. gasp ≠ hinting(不是二選一,是搭配)

常見誤會:「有 gasp 就不用 hinting」。其實:

- **hinting** = 對齊格線的**資料**(snapping 指令)
- **gasp** = 決定「**每個尺寸要不要套 hinting / 要不要反鋸齒**」的**開關**(GRIDFIT 旗標
  本身就是 hinting 的開關)

所以 gasp 是閘門、hinting 是閘門後的資料。**頂級字型兩者都有**(思源:有 hint 釘準 +
gasp 控模式)。我們是 unhinted,gasp 唯一能做的就是「保證平滑」,於是看起來像「gasp
取代了 hinting」——那是缺 hint 才退而求其次,不是本質互斥。

小字級銳利度的光譜(成本由高到低):

1. **內嵌點陣圖**(細明體):每字每尺寸手畫像素,最銳利、最重。
2. **TT hinting**:對齊格線、銳利、無點陣圖,中等成本。
3. **gasp only**(Noto、Shanggu):平滑但偏軟,不對齊,幾乎零成本。← web CJK 現實標準
4. 什麼都沒有:舊 Windows 路徑可能鋸齒。

gasp 拉高的是**下限**(不鋸齒),不是**上限**(銳利對齊)。

## 5. ziano 的決定

- **來源走 glyf**(上游 Shanggu 的 TTF VF),不走 CFF2 → Chrome+Safari 都正常。
- **`subset.py` `_ensure_gasp()`** 對 glyf 切片注入 `{0xFFFF: 0x000F}`(抄 Noto),
  glyf-only;genki/lxgw 是 **CFF、已自帶 hint**,不碰。
- Shanggu glyf+gasp 在 Windows 1x = Noto 水準(平滑、可讀,非極致銳利)。

## 6. 給用戶的取捨

| 想要 | 選 |
|---|---|
| **傳承字形(舊字形)** | **Shanggu**(glyf+gasp,Windows 平滑夠用) |
| **Windows 1x 最銳利的 hinting** | **GenYo**(hinted CFF)——但**是另一套字、無舊字形 merge** |

關鍵:GenYo **不是** Shanggu 的「有 hint 版」,是不同設計。所以這是
「**hinting vs 傳承字形**」的取捨,不是同一字的兩個檔。ziano 的賣點是傳承字形,
所以 Shanggu 走 gasp、GenYo 當「我就是要 hinting」的退路。
