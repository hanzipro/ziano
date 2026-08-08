# 直排時楷體「重心偏左」——中央基線的字體度量錯位

**日期**：2026-08-01　**狀態**：已定位，未修　**影響**：Chromium 直排，跨家族混排

## 一、結論先講

1. 不是楷體本身歪。霞鶩文楷的字面在字身框裡是**正的**（1500 字統計，ink bbox
   中心 x＝497.4/1000；尚古明體 500.4/1000，差 0.3%）。
2. 真正歪掉的是**尚古明體**：Chromium 直排時把它整體往右推 0.11em，楷體幾乎不動
   （＋0.01em），於是看起來像「楷體偏左 0.1em」。
3. 成因是 CSS／字體度量，**與 OpenType 特性完全無關**。`vert`／`vrt2`／`palt`
   ／BASE 表都不參與；改 `font-feature-settings` 一點用都沒有。
4. 只有 **Chromium** 有這個行為。WebKit（Safari）與 Firefox 三種配置量到的偏移
   都在 ±0.5px 內。
5. 能修，而且**必須修在 ziano 的 `@font-face`**（`ascent-override`／
   `descent-override`）。使用端沒有乾淨的修法——原因見第五節。

## 二、量到的症狀

直排欄（`writing-mode: vertical-rl; text-orientation: upright`），同一欄內
明體與楷體混排，量每個字的墨跡（ink）水平中心：

| 引擎 | 明體中心 | 楷體中心 | Δ |
|---|---|---|---|
| Chromium | 189.5 | 185.0 | **−4.5px＝−0.094em** |
| WebKit | 183.5 | 183.0 | −0.010em |
| Firefox | 183.5 | 184.0 | ＋0.010em |

（font-size 48px。Chromium 的明體同時比 WebKit／Firefox 的位置右移 6px＝0.11em，
可見偏掉的是明體，不是楷體。）

## 三、機制

Chromium 直排排字時，字符的**中央基線**（central baseline，決定字在欄內的左右
位置）是這樣算的：

```
偏移量 = (hhea.ascent − |hhea.descent|)/2  ── 實際畫字的那個 font
       − (hhea.ascent − |hhea.descent|)/2  ── 該行 strut（第一個 available font）
```

兩者是同一個 font 時偏移為零（Chromium 走 `vhea` 的 500/−500 路徑，完美置中）；
一旦畫字的 font 不是 strut，就用各自的 `hhea` 橫排度量去合成中央基線，於是每個
family 落在不同的水平位置。

實測驗證（尚古明體 200px 欄、font-size 100px、理想中心 152）：

| 配置 | 量到中心 | 模型預測 |
|---|---|---|
| 尚古明體單獨（自己就是 strut） | 152.0 | 152（偏移 0） |
| 尚古明體有 `unicode-range` | 163.0 | 162.8 |
| `Palatino, 尚古明體` | 168.0 | 168.0 |
| `Palatino, 尚古明體`＋override 至 A−D＝0.649em | 157.0 | 157.2 |
| `Palatino, 霞鶩文楷` | 157.5 | 157.4 |

Palatino 的 `(A−D)/2` ＝0.2727em，代進公式誤差 <0.3px。四個字體（尚古、霞鶩、
源黑 CFF、芫荽）都吻合，OTF/CFF 與 TTF/glyf 行為相同。

用到的是 `hhea`，不是 `OS/2` 的 typo 或 win：兩支字的 typo 都是 880/−120（相同，
無法產生差異），win 差值只能解釋 5.9px，實測 9.8px＝`hhea` 差值。這和
`text-emphasis` 撐行高的那條發現同源——macOS Chrome 一律讀 `hhea`。

### 為什麼 ziano 必然踩到

**帶 `unicode-range` 的 `@font-face` 永遠當不上 strut。** 實測：同一支尚古明體，
不加 `unicode-range` 置中（152），加了就跳到 163。ziano 每個家族都是分片
（Fontsource 式 `unicode-range` 子集），所以 ziano 的字**永遠**是「畫字的 font ≠
strut」，永遠吃到這個偏移。

再加上 `usage.md` 建議的四層字體堆疊以西文字體（Palatino/Cambria）打頭，strut
更確定是那支西文字——但這其實無所謂：strut 是誰只影響**共同的**絕對偏移，兩個
CJK 家族之間的**相對**錯位永遠等於它們 `(A−D)/2` 的差。

### ziano 各家族的 `(A−D)/2`

| 家族 | hhea asc/desc | (A−D)/2 | 與尚古明體之差＝直排錯位 |
|---|---|---|---|
| shanggu-sans / -tc | 1.160/0.288 | 0.4360 | ＋0.004em |
| klee-one | 1.160/0.288 | 0.4360 | ＋0.004em |
| shanggu-serif / -tc | 1.151/0.286 | 0.4325 | — |
| iansui | 0.940/0.180 | 0.3800 | −0.053em |
| genki-*／genyo-*（全部） | 0.880/0.120 | 0.3800 | −0.053em |
| **lxgw-wenkai / -tc** | 0.928/0.256 | **0.3360** | **−0.097em** |

最壞的組合就是尚古＋霞鶩（0.097em）。尚古＋Klee One 反而幾乎不會出事；
尚古＋源黑／芫荽會錯 0.05em。實務印證：改用**源起明體＋霞鶩**（0.380 vs 0.336
＝0.044em）就看不出來了。

### diantenjeom 也在同一張表上

DTJ 的標點字同樣是 `unicode-range` 分片，同樣永遠當不上 strut，所以它和正文字
之間也吃這條公式：

| DTJ | (A−D)/2 | vs 尚古明／黑（0.4325／0.4360） | vs 源起／源樣（0.3800） |
|---|---|---|---|
| serif（4 種標點慣例都一樣） | 0.4325 | 0.000／0.004em | **0.053em** |
| sans（同上） | 0.4360 | 0.004／0.000em | **0.056em** |

DTJ 是從 Source Han 系血統來的，度量和尚古對得上；但 ButTaiwan 的源起／源樣是
0.880/0.120，**和 DTJ 差 0.053em**。也就是說「改用源起明體」解決了正文與楷體的
錯位，卻會在標點上開一個新的 0.05em——換家族時整條鏈（正文＋楷＋標點）要一起看。

## 四、修法比較（都實測過）

| 方案 | Chromium | WebKit | Firefox | 評語 |
|---|---|---|---|---|
| A 現況 | −0.094em | ok | ok | ── |
| **B 各家族統一 `ascent-override`／`descent-override`** | **ok（−0.01em）** | **ok** | **ok** | **建議** |
| C 同名非分片「度量錨」face（`src: local(...)`） | ok | **−0.094em** | ok | 反而把 WebKit 弄壞 |
| D 呼叫端 `vertical-align: <length>` | 可調 | 跟著位移 | 跟著位移 | 三家都會動，只有 Chrome 該動 |

方案 B 除了對齊，順帶把 Chromium 的絕對位置也拉回和 WebKit／Firefox 一致
（明體 414.5 vs 413.5）。

方案 D 值得記一筆：直排時 `vertical-align` 的長度值確實是沿**水平**軸位移的
（cross axis），所以它是唯一能在呼叫端搬動字的手段——但三個引擎都會照做，等於
把另外兩家弄歪，除非做引擎偵測，不建議。

## 五、為什麼不能在呼叫端修

`ascent-override` 只是 `@font-face` 的 descriptor，**沒有辦法對已宣告的
`@font-face` 追加**。使用端要改，只能把 ziano 那幾十條分片 `@font-face` 整份重抄
一次再補上 descriptor——那就是複製 ziano 的 CSS，不是使用。所以這件事的正確位置
是 `src/ziano/cssgen.py`，讓每個家族輸出時就帶上度量覆寫。

## 六、要覆寫成什麼值

### 該把大家調到哪一群

把全部候選字排成一張 `(A−D)/2` 表，會看到四個群：

| (A−D)/2 | 成員 |
|---|---|
| 0.4360 | 尚古黑體／-tc、Klee One、DTJ sans（4 慣例皆同） |
| 0.4325 | 尚古明體／-tc、DTJ serif（4 慣例皆同） |
| **0.3800** | 源起／源樣全系、芫荽、**Hiragino Mincho ProN／Hiragino Sans／Hiragino Sans GB／YuMincho／Hiragino Maru Gothic** |
| 0.3600 | PingFang、Songti、Heiti、Kaiti（macOS 系統字，動不了也用不到） |
| 0.3360 | 霞鶩文楷 TC／SC |

所以「只調尚古」不夠：那只是把尚古從 0.4325 群搬到別群，霞鶩（0.3360）還是誰都
不合，而 DTJ 反而從「和尚古完全一致」被拉開 0.05em。真正的離群值是**霞鶩**。

**尚古不是特立獨行，它是原廠值。** `1.151/−0.286`＝思源宋體、`1.160/−0.288`＝
思源黑體，尚古兩支一字不差地留著；DTJ 從思源 subset 出來，所以也一樣；Klee One
也是 `1.160/−0.288`。反倒是 ButTaiwan（源起／源樣／芫荽）刻意把 `hhea` 重設成
`0.880/−0.120`＝字身框＝日系（Hiragino／YuMincho）慣例，而霞鶩把 Klee 的
`1.160/−0.288` 自行降到 `0.928/−0.256`。兩個流派：**思源系寫的是「行」度量**
（給 `line-height: normal` 用的寬鬆值），**日系／ButTaiwan 寫的是字身框**。這個
workspace 的字庫剛好日系那派人多而已。

`0.3800` 是唯一該選的目標值：它等於 `(0.88−0.12)/2`＝字身框中心（sTypo 的 CJK
慣例），而且**四層堆疊裡的日文系統 fallback 全部剛好就是這個值**——統一過去以後
連 webfont 掛掉退到 Hiragino／YuMincho 時位置都不跳。ziano 16 個家族與 DTJ 8 支
都是 codegen 產出的 CSS，改一次的成本和只改尚古一樣。

（DTJ 四種標點慣例彼此度量完全相同，所以 JIS↔MOE↔GB↔KLR 互換不會動到位置。）

### 改在字體裡還是改在 CSS？

兩者實測**完全等效**（尚古直排中心：原樣 163.0；字體層改 `hhea` 880/−120 →
158.0；CSS `ascent-override: 88%; descent-override: 12%` → 158.0）。取捨：

- **字體層**（DTJ、ziano 都是自己 build，重寫 `name` 表的地方順手加一行）：對直接
  引 woff2、不吃我們 CSS 的人也生效；不依賴 `ascent-override` 支援度（這版 WebKit
  直接忽略該 descriptor）。DTJ 另有純賺的理由——它現在 1.437em 的行度量會參與行框
  union，等於一個標點就把行高撐大（和 `text-emphasis` 那條同源），降到字身框是
  雙重改善。**但要記得 `usWinAscent`／`usWinDescent` 一起改**，Windows 走 win。
- **CSS 層**：可逆、不動二進位、不必重 build 一整組子集；而且**跨平台反而更穩**
  ——它一次蓋掉引擎實際使用的 ascent/descent，不管該平台讀 `hhea` 還是 `usWin*`。
  這件事有實際差別：霞鶩的 win（0.3735）和 hhea（0.336）不一致，只改 `hhea` 的話
  Windows 上的錯位量會和 macOS 不同。

### 兩個旋鈕

兩個旋鈕彼此獨立：

- **差 A−D** 決定直排的水平位置（就是本 bug）。
- **和 A＋D** 決定 `line-height: normal` 的行高，與本 bug 無關。

所以只要**全家族用同一組值**，錯位就消失，取什麼值都對齊。取值建議：

- **原則派**：`ascent-override: 110%; descent-override: 34%`
  （差 0.76em＝`sTypo` 880/−120 的字身框中心，和 0.76 這個 CJK 慣例一致；
  和 1.44em 維持寬鬆的 `normal` 行高，接近尚古現況 1.437em，不會讓沒設
  `line-height` 的舊頁面突然縮排）。殘留一個各家族**共同**的 Chromium 直排偏移
  （strut 是 Palatino 時約 0.107em）——歪得整齊，肉眼看不出來，但那是 Chromium 的
  bug，值得回報上游。
- **實測歸零派**：差取 0.649em（例如 `92.45%`／`27.55%`）可以讓「純 ziano 堆疊」
  在 macOS Chrome 直排完全置中。但那個 0.3245em 的常數來自瀏覽器 default font，
  換平台／換西文打頭字就不準，不建議寫死。

### ⚠️ 更正（2026-08-02）：真的 Safari 也有這個 bug，CSS 覆寫救不到

下面那節「WebKit 沒事」是**用 Playwright 的 WebKit 量的，那個 build 和 Safari 行為
不同**——它整個忽略 `ascent-override`，而且本來就沒有這個偏移，於是看起來像「沒事」。

拿真的 Safari（macOS，度量覆寫**已開啟**的出貨 CSS）截圖逐列量欄內墨跡中心：

| 列（24px 正文、2× 螢幕） | 中心 |
|---|---|
| 尚古明體 丹（正文） | 241.6 |
| 霞鶩文楷 TC（`<q>` 引文） | 237.3 |
| 尚古明體 丹（正文） | 241.8 |

偏移 **4.3 螢幕 px ÷ 48 ＝ 0.090em**，而兩支字的 `hhea` 差是 0.0965em——在量測誤差內
吻合。同一頁同一時刻的 Chrome 截圖逐列都是 297±1.5，沒有系統性偏移。

結論修正：

- **Safari 和 Chromium 一樣，直排中央基線讀的是 `hhea`。**
- **但 Safari 不把 `ascent-override` 套用到這條路徑**，所以 CSS 覆寫只修好 Chromium。
- 其他候選來源都對不上：`usWin` 差只解釋 0.059em、`sTypo` 兩支相同（差 0）。是 `hhea`。

→ **`@font-face` 覆寫不是完整解，必須改在字體檔裡**（切片前改 `hhea` ＋ `usWin*`，
就像 `upright.py` 那個鉤子）。CSS 那份可以留著（同一個常數推導），但它不能是唯一的。

### CSS 覆寫摸不到的另一件事：`text-emphasis` 的 outset

同一支尚古切片供應 `●`，32px、`line-height: 1`，量單行 `<p>` 高度：

| | 原樣 `1151/−286` | CSS `ascent-override: 60%/0%` | 字體層改成 `600/0` |
|---|---|---|---|
| Chromium | 61px | **61px（沒動）** | **48px** |
| WebKit | 70px | **70px（沒動）** | **36px** |
| Firefox | 49px | 49px | 49px（固定 0.5em，與度量無關）|

獨立重現了 `diantenjeom/docs/text-emphasis-line-height.md` 的結論，只是這次在 ziano
的字上：**`ascent-override` 完全碰不到 mark 字體的 outset，字體檔可以。**

但這對 ziano 的取值沒有幫助：outset 由 asc/desc 的**和**決定，而正文字體需要大的和
（1.44em）來撐 `line-height: normal`。所以 ziano 這邊 outset 仍是 0.72em，著重號的
正解還是用選擇器指到 `Diantenjeom Emphasis`（0.30em）。

### 字體層 vs CSS 層（更新後）

| | CSS `ascent-override` | 字體層 `hhea` ＋ `usWin*` |
|---|---|---|
| Chromium 直排中央基線 | ✅ | ✅（實測 158.0，與 CSS 同值）|
| **Safari 直排中央基線** | **❌** | ✅（預期，待真機複驗）|
| `line-height: normal` | Chromium／Firefox ✅、WebKit ❌ | 三家 ✅ |
| `text-emphasis` outset | ❌ | ✅ |
| 不吃我們 CSS 的人 | ❌ | ✅ |
| Chrome <87 ／ Safari <16.4 | ❌ | ✅ |
| 可 A/B（demo 開關）| ✅ | 需另存未修改副本 |

成本幾乎是零：尚古**沒有 MVAR**（查過），`hhea` 在整條 wght 軸上是定值，改一次覆蓋
所有字重與 instance；源起／源樣是 per-weight 靜態檔，逐檔套同一個函式即可。而且
「切片前改 base font」這個鉤子 `upright.prepare()` 已經在了。

取值：**`hhea 1100/−340`、`usWin 1100/340`**——差 0.76em（修直排），和 1.44em（維持
現行 `line-height: normal`，貼近尚古原本的 1.437em）。不要照抄 DTJ 的 `880/−120`：
那個和是 1.0em，適合「不該撐行框」的標點字，不適合正文。

---

### 舊結論（Playwright WebKit，已被上面更正）



**直排位置**：WebKit 與 Firefox 的中央基線走 `vhea`（500/−500）／字身框那條路，
`ascent-override`／`descent-override` 只覆寫**橫排**的 asc/desc，碰不到它。同一頁
三家實測（200px 欄、理想中心 152）：

| | 無 override | 有 override |
|---|---|---|
| Chromium | 163.0（歪） | 152.0（修好） |
| WebKit | 150.5 | 150.5（分毫未動） |
| Firefox | 152.0 | 152.0（分毫未動） |

**橫排的字不會動。** 有顯式 `line-height` 時，覆寫前後量到的墨跡位置一模一樣
（`font-size: 100px`、`line-height: 2`、同一行混排明體與楷體）：

| | 明體墨跡底端在行內的位置 | 明↔楷底端差 |
|---|---|---|
| Chromium | 139 → 139 | ＋1px → ＋1px |
| WebKit | 150 → 150 | ＋1px → ＋1px |
| Firefox | 132 → 132 | ＋1px → ＋1px |

橫排是對齊字母基線（alphabetic baseline），asc/desc 只決定行框大小，不搬字。

**唯一跨引擎的副作用是橫排 `line-height: normal` 的行高**（`font-size: 100px`，
單行 `<p>` 高度）：

| | 尚古明體 → 覆寫後 | 霞鶩文楷 → 覆寫後 |
|---|---|---|
| Chromium | 144 → 144 | 119 → **144** |
| WebKit | 144 → 144 | 119 → **119**（WebKit 直接忽略 override） |
| Firefox | 151 → 145 | 128 → **145** |

也就是說：Chromium／Firefox 會把各家族原本 1.00～1.45em 不等的預設行高統一成
1.44em——那是**統一**不是「亂掉」，現在不一致才是亂的；而且 CJK 頁面本來就該顯式
設 `line-height`，`normal` 只是保險絲。順帶一提，這版 WebKit 根本不理會
`ascent-override`，所以這條修法在 Safari 是「安全但無效」——幸好 Safari 本來就
沒這個 bug。

同一組度量也會改變 `text-emphasis` 的外溢量（見 CLAUDE.md 那條），要一起評估。
屬於 breaking change，要進 CHANGELOG。

## 七、複現

量測件留在 `../../.probe/`（workspace 根目錄，已被 `.gitignore` 擋掉）：

- `probe9.html` 混排最小重現；`probe11.html` 方案 D 對照
- `shot.mjs` 用 han 的 Playwright 跑 chromium／webkit／firefox 三家截圖
- `png.py`／`crop.py` 純 stdlib 的 PNG 解碼與量測（不需要 Pillow）

量法：直排欄裡取字的墨跡像素範圍求中心，比對同欄不同 family 的差值。整套沿用
`diantenjeom/scripts/check_squeeze.py` 的無頭 Chrome 量測套路，只是這次因為要跨
引擎，改用 han 已裝好的 Playwright。
