# ziano CDN 策略報告 — 競速、jsDelivr、Gcore、中國

> 報告 2026-06-16。供日後回顧。
> 來源：與 Gemini 的對話逐字稿見 [`with-gemini.md`](./with-gemini.md)；本文是逐段總結
> ＋Claude 的看法＋給 ziano 的行動建議。

---

## TL;DR

1. **CDN競速頁（`demo/cdn-bench.html`）**：以「診斷／行銷展示」定位 → **保留**，但把 caveats
   攤開、headline 改秀「只下載命中切片」。它**不是**交付機制。
2. **前端 CDN Racing（Gemini 主推的 `<head>` 競速腳本）**：**不建議**做進 ziano 的
   推薦用法。render-blocking、3 倍連線、cache-miss 盲點、補丁越疊越多⸺而 Gemini 自己
   在最後一段就承認「用 Gcore 就不需要它了」。字型在關鍵渲染路徑上，越簡單越好。
3. **「棄用 jsDelivr」太武斷**：那是**一條家用 HiNet 線、單次冷快取**的實測；jsDelivr 仍是
   免費 + npm 直連 + 全球 multi-CDN 的好預設。台灣繞路是已知 caveat，該在**基礎設施層**
   解（origin-proxy / 換預設），不是在每個使用者的前端跑競速。
4. **Gcore 最有價值的用法不是「取代 jsDelivr」，而是 origin-proxy**：用自有網域
   （如 `cdn.hanzi.pro`）回源 unpkg/npm、cache-everything、Anycast。台灣直落台北 PoP、
   中國走近海、全球皆可，且一個硬編碼 URL 就好⸺這是整串對話最強的一招，列為 ziano 的
   **未來 infra 選項**（非必要）。

---

## 一、Gemini 對話逐段總結 ＋ 我的看法

**① 三家 CDN 泛比較** — Gemini：jsDelivr 最穩（multi-CDN）、esm.sh 走現代 ESM、
unpkg 適合 demo。
*我*：同意，無爭議。

**② 拿來 host 中文字型切片，哪家好** — Gemini：jsDelivr 毫無懸念首選（併發、二進位、
CORS、multi-CDN）；列 @chinese-fonts／taipei-sans-tc／花園明朝皆用 jsDelivr；給出限制
（單包 ≤10k 檔、≤50MB、CSS 相對路徑、一字重切 100–120 片）。
*我*：基本同意，且那「100–120 片」正好對上 ziano 的 120 片切法。唯「併發風暴」這個論點，
後面被使用者自己的觀察推翻（見 ⑤）。

**③ 家裡實測 jsDelivr 反而最慢、慢 GF 好幾倍** — Gemini：台灣 HiNet 路由問題；GF 有彰濱
資料中心 + 直連 peering（島內個位數 ms）；jsDelivr 常繞 香港/東京/美西。建議**放棄
jsDelivr**，改 esm.sh 或 Cloudflare Pages/Vercel。
*我*：**台灣繞路是真的**（diantenjeom/這專案的脈絡也吃過 CDN 路由的虧），但**「放棄」下得
太快**：(a) 這是單一 ISP、單次冷測；(b) jsDelivr 2025 末已換 Rust edge worker，路由可能
已不同；(c) 不能拿開發者自家網路替全球受眾決策。應視為 caveat，不是判死刑。

**④ unpkg 併發限制？brotli？** — Gemini：unpkg 無公開 RPS，但 cache-miss/新版易觸發
429/503；三家都支援 brotli；**brotli 對 CSS 有效（壓 70–80%），對 woff2 無效**（woff2 本身
就是 brotli 封裝，CDN 會跳過二次壓縮）。
*我*：**brotli 這段完全正確**，也是本工作區早記過的事（woff2=brotli-internally）。429 風險
同樣被 ⑤ 沖淡。

**⑤ 不可能一次併發 120 片；常用字集中在最後 10–15 片** — Gemini：認同，GF 用 ML 把高頻字
聚到十幾片，實際只觸發 10–15 個請求。據此重排：🥇 esm.sh、🥈 unpkg、❌ jsDelivr（台灣繞路）。
*我*：**這是整串最關鍵的事實**，它一舉拆掉前面「併發風暴」「unpkg 429」兩大恐懼的地基。
既然只有 10–15 個請求，三家在「夠快的網路」下差距都不大，選擇權重應回到**穩定性 + 路由**，
而非併發承載力。

**⑥ 前端判斷選最快 CDN，記住它** — Gemini：這叫 CDN Racing；字型是 render-blocking，
等競速跑完會 FOUT，故主推「先斬後奏：盲選一家擋首刷、idle 後台 HEAD 競速、localStorage
記贏家、下次秒開」。
*我*：方向聰明，但**對字型而言是把問題搬錯層**。下面 ⑦–⑨ 會看到補丁越疊越高。

**⑦ 前台競速 + loading indicator？** — Gemini：視覺變好，但把「字慢」升級成「擋整頁」；
三風險：3 網域同時連線內耗、輸家仍偷下載 3× 流量、罕用字切片測不準。折衷：HEAD + AbortController
砍輸家。

**⑧ 只測 HEAD 準嗎？換網路/出國怎辦** — Gemini：小檔 RTT 主導，HEAD ~85% 準；盲點是
cache hit/miss；要 100% 改 GET 一個 5KB 探針。換網路 → LS 變毒藥；解法 A) TTL、B) Network
Information API、C) **Stale-While-Revalidate（最推薦）**。

**⑨ 還有破綻嗎** — Gemini：3 邊緣案例：iOS Safari 無 `navigator.connection`（2026 仍是）→
靠 TTL；極慢網 loading 卡死 → 熔斷 1s；SPA 字型突變閃爍 → 背景競速只寫 LS、不動 DOM。
附「終極鐵壁版」腳本。
*我（⑥–⑨ 合評）*：**這四段是一條精彩但不該走的路。** 每加一個 fix 就冒一個新坑
（TTL／熔斷／iOS／SPA／AbortController…），最後堆成一坨要長期維護的 render-path JS。
而 HEAD 競速量的是「CSS URL 的 TTFB」，**量不到真正用到的那十幾片 woff2 的邊緣快取狀態**
⸺也就是說它競的速，跟使用者實際體感未必對得上。對「越快越簡單」為賣點的字型 CDN，
這個複雜度/收益比很差。

**⑩ 服務中國大陸的 CDN** — Gemini：困難模式；jsDelivr 失去 ICP、三家都會被導去香港/東京/美西、
GFW 風險。策略 A) 國內免費 npm 鏡像（餓了麼/zstatic/onmicrosoft.cn）塞進競速腳本；
B) 阿里 OSS/騰訊 COS + 國內 CDN（需 ICP 備案）；無備案 → 中國優化外網（香港 CN2、Gcore 亞太）。
*我*：方向對。我先前的獨立分析也指到「中國是 jsDelivr 唯一真破口」。

**⑪ 國內鏡像 2026 現況** — Gemini：雪崩。餓了麼 2.0/5（防盜鏈 403）、zstatic 3.5/5
（晚高峰塞車）、onmicrosoft.cn 1.5/5（民間反代、隨時蒸發）。新生態：字節/網易需提交收錄，
或中國優化外網（Gcore 亞太）。
*我*：這類民間鏡像本就脆，當生產依賴是賭博，認同別碰。

**⑫ Gcore 有 npm 自動備份嗎** — Gemini：沒有公共鏡像，但可用 **Origin Proxy** 5 分鐘 DIY：
源站填 unpkg/registry、綁自有網域、cache-everything（woff2/css TTL 30d–1y），首訪被動回源、
之後全由 Gcore 邊緣扛。免費額度 1TB/月。
*我*：**這是整串最有價值的一招**，也回答了我先前 doc 的疑問⸺「jsDelivr 已含 Gcore，那直連
Gcore 有何意義？」意義在：jsDelivr 的負載平衡**未必**把 HiNet 用戶導到 Gcore 台北節點；
而你自建 origin-proxy 用 Gcore 的 Anycast，是**確定性**落台北 PoP。所以「Gcore 直連能贏
台灣的 jsDelivr」與「jsDelivr 內含 Gcore」兩件事不矛盾。

**⑬ 適用全球還是只港陸** — Gemini：全球（Gcore 盧森堡總部、全球 Anycast）；台灣落台北 PoP
（10–30ms、與 HiNet 等 peering）、中國走近海、歐美落本地。**用了它甚至不需要競速腳本**
⸺硬編碼一個 URL，零 race-JS，對 Core Web Vitals 最友善。盲點：免費額度尖峰節點優先權較低。
*我*：**同意，而且這正是我對 ⑥–⑨ 的反論的佐證**：Gemini 自己承認 origin-proxy 一上，前面那套
競速腳本就多餘了。把網路層複雜度收回基礎設施，前端保持一個乾淨 URL⸺這才是對的架構方向。

---

## 二、三個核心問題的結論

### Q1. CDN競速，需要？合理？照搬 or 調整？

要分清**兩種「競速」**：

- **ziano 現有的 `cdn-bench.html`（診斷/展示頁）**：量同一套件在 jsDelivr/unpkg/esm.sh 的
  交付速度，GF 當標尺。→ **需要**（backing「毫秒神速」文案、兼診斷工具）、**方法學合理**
  （同物比較、累積中位數、TAO 標記、GF 明說非同物）。**調整**：caveats 攤給使用者看、
  別當排行榜、headline 改秀「只下載命中切片」。
- **Gemini 主推的「前端 CDN Racing 腳本」（交付機制）**：→ **不建議照搬進 ziano 的推薦用法**。
  理由見 ⑥–⑨ 合評：render-blocking、3× 連線、cache-miss 盲點、補丁堆疊、量不到真正的
  woff2 快取狀態。字型 CDN 的賣點是「貼一行就快」，不該要消費端在關鍵路徑跑競速 JS。

### Q2. Gcore 更好嗎？

- **取代 jsDelivr 當全球免費分發 → 不值得**：jsDelivr 已是 multi-CDN（含 Gcore/Fastly/
  Cloudflare/Bunny）、免費無限流量、npm 直連零基建。
- **但 Gcore 的 origin-proxy（自有網域回源 npm）是真有料**：給你**確定性**的 Anycast 路由
  （台北 PoP、中國近海）、解掉台灣繞路與中國破口、移除競速腳本的必要、一個硬編碼 URL。
  代價：要開 Gcore 帳號、綁網域、設快取規則；免費 1TB/月尖峰優先權較低。
- 一句話：**jsDelivr 當預設；Gcore-origin-proxy 當「要掌控台灣/中國速度」時的 infra 升級**。

### Q3. 該棄用 jsDelivr 嗎？

**不該**（至少不能憑一條 HiNet 冷測）。它仍是 OSS 字型的事實標準分發（@chinese-fonts、
taipei-sans 都用）、免費、npm 直連、全球。台灣繞路是**已知 caveat**，靠 infra 解，不靠
全球受眾的前端競速解。

---

## 三、給 ziano 的行動建議

1. **預設維持 jsDelivr `@rc`**（demo 與推薦 snippet）。穩定後 `@rc → @latest`（見
   `docs/TODO.md`）。
2. **`cdn-bench.html` 保留**，做三個調整：攤開 caveats、改描述性語氣（非排行榜）、
   headline 改秀「只命中切片才下載」。它也順便是台灣路由現實的證據。
3. **不要**把前端 CDN-racing 腳本做成 ziano 的官方整合方式。整合 snippet 保持一行
   `<link>` + 視需要 `preconnect`。
4. **未來 infra 選項（非必要）**：若要認真服務台灣/中國速度，評估在 `hanzi.pro` 自有網域上
   架 **Gcore（或 Bunny）origin-proxy**（回源 npm/unpkg、cache-everything、自訂網域）。
   一個 URL 全球通吃，免競速。先用個人網域實測台灣/內地 TTFB 再決定。
5. **中國**：別依賴國內免費 npm 鏡像（2026 多半半死）。要嘛 origin-proxy 近海線路，要嘛
   正規 ICP + 阿里/騰訊 OSS（商用才值得）。

---

### Sources
- 對話逐字稿：[`with-gemini.md`](./with-gemini.md)
- jsDelivr Network（multi-CDN：Cloudflare/Fastly/Bunny/Gcore）— https://www.jsdelivr.com/network
- jsDelivr vs unpkg vs cdnjs — https://blog.blazingcdn.com/en-us/jsdelivr-vs-unpkg-vs-cdnjs-best-free-cdn-for-open-source-projects
- 25 Best CDN Providers 2026 — https://linuxblog.io/best-cdn-providers/
