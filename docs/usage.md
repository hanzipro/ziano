# ziano使用指南⸺讓傳承字形在網頁上好看

ziano把整套OFL傳承字形（傳承／舊字形）切成`unicode-range` woff2，用CDN或npm分發。
載入只是第一步；**真正讓字好看的，是`font-family`那條回落鏈怎麼排。**這份指南先講載入，
再把我們驗證過的回落順序，當成一套「照著寫就會變好看」的美學原則交給你。

---

## 一、載入字體

### 方法一：CDN（最快上手）

把這兩行加進`<head>`。`preconnect`先暖好連線，stylesheet只會拉下頁面**實際用到**的切片
（沒用到的切片永遠不會被請求）：

```html
<link rel="preconnect" href="https://cdn.jsdelivr.net" crossorigin />
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@hanzi.pro/webfonts-shanggu-serif@latest/swap.css" />
```

把`shanggu-serif`換成你要的字族id。`@latest`永遠指向最新正式版；若想要 CDN 邊緣不可變、
可長期快取的 URL，把`@latest`改釘一個明確版本號（如`@0.1.0`）即可。

### 方法二：自行托管（npm）

想把字體放自己的伺服器？用npm裝這個套件⸺`files/`裡的woff2會一起裝進來，再用打包工具
`import`對應的CSS即可：

```bash
npm i @hanzi.pro/webfonts-shanggu-serif@latest
```

```js
import '@hanzi.pro/webfonts-shanggu-serif/swap.css'
```

---

## 二、指定字族：一套「自動變好看」的fallback美學

`font-family`不只是「挑一個字」，而是排一條**回落鏈**。排得好，中英混排自動和諧、罕用字有著落、
連離線都不崩。一條好的中文字族鏈，由前到後是**四層**：

```css
font-family:
  'Avenir Next', 'Segoe UI Variable', 'Segoe UI', Roboto, /* ① 西文打頭 */
  'Shanggu Sans',                                         /* ② 傳承字形居中 */
  'Hiragino Sans', 'Hiragino Sans GB', 'Yu Gothic',       /* ③ 系統日文字墊底 */
  system-ui, sans-serif                                   /* ④ generic 收尾 */
;
```

### ① 西文打頭⸺用web-safe西文字渲染拉丁字母與數字

黑體用`'Avenir Next', 'Segoe UI Variable', 'Segoe UI'`，明體用`Palatino, Cambria`。**為什麼放最前？**

- **零成本**：這些西文字幾乎每台機器都內建（web-safe），不必下載、即刻顯示。
- **西文更好看**：它們的拉丁字母與數字，比CJK字體「附贈」的西文好看得多⸺後者往往是等寬、
  生硬的陪襯。
- **對中文零影響**：它們**不含漢字**，所以中文字會直接略過它們、落到下一層。放最前只升級西文，
  完全不動到中文。

結果：漂亮的西文＋傳承的漢字，混排天衣無縫。這是專業中文網頁排版的標準做法。

### ② 傳承字形居中⸺漢字的正主

`'Shanggu Sans'`（尙古黑體）、`'Shanggu Serif'`（尙古明體）、`'LXGW Wenkai TC'`（霞鶩文楷）…
漢字落在ziano webfont上，呈現未被各地標準改寫的**傳承印刷形**。

### ③ 系統日文字墊底⸺webfont萬一沒載入時的高品質保險

webfont可能因離線、CDN故障等原因**整個**載入失敗。這時別讓中文無處可去⸺但也**不要**落到
繁中系統字：

- **別用**蘋方（PingFang）、微軟正黑、新細明體：它們走的是國字標準字體那套「楷化」印刷體的路子，
  把端正的印刷形硬掰成手寫楷書，矯枉過正，正是傳承字形要避開的方向。
- **改用日文系統字**：macOS／iOS內建的**Hiragino**、Windows內建的**游ゴシック（YuGothic）／
  游明朝（YuMincho）**⸺字形沉穩、合於印刷、不過度楷化，是退而求其次的好選擇。順序是
  **Mac字（Hiragino）在前、Windows字（Yu*）在後**。
- 黑體鏈多帶一支**Hiragino Sans GB**：少數中文常用字（查、啟、鄉…）日文版收在別的碼位，GB版
  補得回來（雖是陸標字形，但這只是離線保險，可接受）。明體沒有對應的GB版，故從略。

> **註：只要webfont正常載入，這一層永遠輪不到。**傳承字形的收字量比這些日文字全面得多⸺
> 不可能有日文字有、而傳承字形沒有的字，所以**不會逐字回落**到它們。它純粹是「整個webfont掛掉」
> 時的保險，寫在後面只為那個萬一。

### ④ generic收尾

`sans-serif` / `serif` / `cursive, serif`，交給瀏覽器預設，最後一道防線。

---

## 三、用CSS變量重用整條鏈（別每次重寫）

這條鏈很長，每次手打容易漏字、寫錯順序。**定義一次，到處`var()`重用**：

```css
:root {
  --font-system-ui:
    'Avenir Next', 'Segoe UI Variable', 'Segoe UI', Roboto,
    'Shanggu Sans',
    'Hiragino Sans', 'Hiragino Sans GB', 'Yu Gothic',
    system-ui, sans-serif
  ;
  --font-sans-serif:
    'Avenir Next', 'Segoe UI Variable', 'Segoe UI', Roboto,
    'Shanggu Sans',
    'Hiragino Sans', 'Hiragino Sans GB', 'Yu Gothic',
    sans-serif
  ;
  --font-serif:
    Palatino, Cambria,
    'Shanggu Serif',
    'Hiragino Mincho ProN', 'Yu Mincho',
    serif
  ;
  --font-cursive:
    Palatino, Cambria,
    'LXGW Wenkai TC',
    Klee, 'Klee One',
    BiauKai, DFKai-SB, 'Kaiti TC',
    'Hiragino Mincho ProN', 'Yu Mincho',
    cursive, serif
  ;
}

body         { font-family: var(--font-sans-serif); }  /* 黑體：內文、UI */
h1, .display { font-family: var(--font-serif); }       /* 明體：大標 */
blockquote   { font-family: var(--font-cursive); }     /* 楷體：引文、詩句 */
```

- 三個變量對應三種generic：`--font-sans-serif`（黑體）、`--font-serif`（明體）、
  `--font-cursive`（楷體）。換字族只要改`:root`一處，所有用到的地方自動跟著變，不會漏改、寫錯。
- 楷體（`--font-cursive`）一樣前置西文serif；若你偏愛霞鶩文楷自帶那手帶筆觸的拉丁字母，把
  `Palatino, Cambria`拿掉即可。

**進階**：固定不變的「日文字＋generic」尾巴也能抽出來，組合得更乾淨：

```css
:root {
  --fallback-hei:    'Hiragino Sans', 'Hiragino Sans GB', 'Yu Gothic', sans-serif;
  --fallback-ming:   'Hiragino Mincho ProN', 'Yu Mincho', serif;
  --font-sans-serif: 'Avenir Next', 'Segoe UI Variable', 'Segoe UI', 'Shanggu Sans', var(--fallback-hei);
  --font-serif:       Palatino, Cambria, 'Shanggu Serif', var(--fallback-ming);
}
```

---

## 四、`font-display`：載入過程的行為

每個套件都附三種`font-display`入口，換檔只要換CSS檔名：

| 檔案 | 行為 | 適合 |
|---|---|---|
| `swap.css`（預設） | 先顯示退化字形，webfont到了再換 | 一般內文，最不擋內容 |
| `block.css` | 短暫隱形等webfont，再現形 | 大標題，不想閃一下退化形 |
| `optional.css` | webfont沒即時到就這次不換 | 重CWV的頁面，零版位位移（CLS=0） |

靜態字體（源起、霞鶩文楷等）還能**只取單一字重**：用`swap/<字重>.css`取代整族的`swap.css`，
下載更小。可變字體（尙古）單檔即涵蓋整段字重軸，不必分檔。

### 說出刻別：`dan/`

npm上**無後綴一律指丹**：`webfonts-shanggu-serif`就是丹（0.1.0起沒變過），
`webfonts-shanggu-serif-yue`是月。所以預設樣式表宣告的是不帶後綴的名字，
0.1.0的使用者升上來一行都不用改。

想在字體堆疊裡把刻別寫明的，每個無後綴套件都另附一份同樣的face，掛在帶刻別的名字下：

```css
/* 同一個字體，兩個名字——擇一引入 */
@import url(".../webfonts-shanggu-serif/swap.css");      /* 'Shanggu Serif'     */
@import url(".../webfonts-shanggu-serif/dan/swap.css");  /* 'Shanggu Serif Dan' */
```

`block`／`optional`同樣有`dan/`版本（靜態字體另有`dan/swap/<字重>.css`），套件出口是
`@hanzi.pro/webfonts-shanggu-serif/dan`。兩份同時引入無害但沒有意義：URL相同、
只是把每個face用兩個名字各宣告一次。

字體檔內部一律用帶刻別的全名——name表沒有含糊的餘地。

---

## 五、直排重心：ziano已經幫你對齊了

直排（`writing-mode: vertical-rl`）混用兩個家族時⸺正文明體配楷體引文、或正文配
diantenjeom標點⸺常見一段字整條**左右錯開**。根因不在你的CSS：Chromium與Safari
都把字的中央基線合成成`(hhea.ascent − |hhea.descent|) / 2`，取自實際畫出那個字的
font；而帶`unicode-range`的分片`@font-face`永遠當不上一行的第一順位字體，所以
**永遠**走這條合成路徑。上游各家的`hhea`差很多（思源系0.4325em、ButTaiwan系
0.380em、霞鶩0.336em），兩家族最多差到0.0965em，肉眼一看就是歪的。

ziano自0.2.0起**在切片前就把每個家族的`hhea`／`usWin*`統一寫成`1100/−340`**，
中央基線一律落在0.380em⸺也就是字身框中心，Hiragino／YuMincho／源起／芫荽本來
就在這個位置，所以webfont沒載入、退回系統日文字時位置也不跳。你**不必**加任何
`ascent-override`：CSS那條路Safari根本不吃，度量必須寫進字檔裡才有效（樣式表仍會
把同樣的數字宣告一次，純屬對齊保險）。

要跟ziano併排的第三方字體，把它的`hhea`也正規化成同一組值即可；
diantenjeom的標點字用`880/−120`（同樣0.380em中心，但總高只有1.0em，才不會撐大
別人的行高）。完整推導與量測見`vertical-baseline-offset.md`。

同版另修：`：`（U+FF1A）與`；`（U+FF1B）在UTR50屬**Tr**類⸺沒有`vert`規則的字體，
Firefox會照標準把它們**轉倒**。ziano替所有家族補了一條「自己換成自己」的`vert`
規則，Firefox直排下的冒號、分號因此保持直立。

---

## 六、延伸：字本身也要講究

字選對了，文字內容的排版細節也別放過⸺全形標點、中西文之間不打空格（間距交給CSS
`text-autospace`）等，能讓整體再上一個檔次。這部分屬於文案／排版規範，見工作區的
`copy-style.md`。
