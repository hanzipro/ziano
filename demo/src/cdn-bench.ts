// Entry for cdn-bench.html. Times how fast each CDN delivers a ziano webfont — the
// stylesheet's onload, then 字體就緒, then a representative woff2 slice — with Google
// Fonts (Noto Sans TC) as a speed yardstick. Pure stat/url helpers; the effects (DOM,
// fetch, font loading, localStorage) live in the shell. Runs accumulate in
// localStorage and the table is a pure projection of them.
type CdnKey = 'jsdelivr' | 'unpkg' | 'esmsh' | 'gfonts'
type Cdn = {
  readonly label: string
  readonly tao: boolean // sends Timing-Allow-Origin → cross-origin timing is exposed
  readonly css: string
  readonly probe: string | null // a woff2 slice to time; null = not a fixed npm asset
  readonly family: string
}
type Run = { cssMs: number; fontMs: number; woffMs: number | null }
type RunRec = { css: number[]; font: number[]; woff2: number[] }
type Runs = Partial<Record<CdnKey, RunRec>>
type Stat = {
  key: CdnKey
  label: string
  tao: boolean
  n: number
  min: number | null
  med: number | null
  avg: number | null
  fmed: number | null
  wmed: number | null
}

const $ = <T extends Element>(sel: string, root: ParentNode = document) =>
  root.querySelector<T>(sel)
const $$ = <T extends Element>(sel: string) => [...document.querySelectorAll<T>(sel)]

// ── config (pure data) ─────────────────────────────────────────
// Rides @latest (like cdn.ts) so it tracks the newest stable publish; all three npm
// CDNs share the spec, so the comparison stays fair.
const PKG = '@hanzi.pro/webfonts-shanggu-sans@latest'
const PROBE = 'files/shanggu-sans.55.woff2' // a representative ~54 kB body-text slice
// `base` already includes any registry path prefix: ONLY jsDelivr serves npm packages
// under /npm/ — unpkg and esm.sh serve them at the root. (mirrors cdn.ts ORIGIN.) Passing
// /npm to unpkg made it resolve the package literally named `npm` → the real path 404'd →
// link error, which looked like the CDN being down. It wasn't.
const npm = (base: string) => ({
  css: `${base}/${PKG}/swap.css`,
  probe: `${base}/${PKG}/${PROBE}`,
  family: 'Shanggu Sans',
})
const CDNS: Record<CdnKey, Cdn> = {
  jsdelivr: { label: 'jsDelivr', tao: true, ...npm('https://cdn.jsdelivr.net/npm') },
  unpkg: { label: 'unpkg', tao: false, ...npm('https://unpkg.com') },
  esmsh: { label: 'esm.sh', tao: false, ...npm('https://esm.sh') },
  // Google Fonts serves a DIFFERENT font (Noto Sans TC) via its own dynamic subset
  // service — a yardstick, not a like-for-like asset. Only CSS / 字體就緒 compare;
  // the woff2 probe is npm-only (probe: null).
  gfonts: {
    label: 'Google Fonts',
    tao: true,
    probe: null,
    family: 'Noto Sans TC',
    css: 'https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@400&display=swap',
  },
}
const KEYS = Object.keys(CDNS) as CdnKey[]
const STORE = 'cdn-bench-runs'
const HELP: readonly string[] = [
  '「繞過快取」勾選=冷抓：CSS 加 ?bust、woff2 用 no-store，每次都走網路（CDN 邊緣仍熱）。',
  '取消勾選=暖抓：CSS 不加 bust、woff2 用 force-cache，第一次後從瀏覽器快取讀（量本地命中速度）。',
  'woff2 中位 = 實抓 slice 55（約 54kB 正文字切片）的下載時間中位數。切換冷/暖前建議先「重置數據」避免混在一起。',
  'Google Fonts 是不同的字（Noto Sans TC）＋自家動態 subset，只有 CSS／字體就緒可比；woff2 欄顯示「—」屬正常。',
]

// ── pure helpers ───────────────────────────────────────────────
const median = (xs: readonly number[]): number | null => {
  if (!xs.length) return null
  const s = [...xs].sort((a, b) => a - b)
  const m = s.length >> 1
  return s.length % 2 ? s[m] : (s[m - 1] + s[m]) / 2
}
const mean = (xs: readonly number[]): number | null =>
  xs.length ? xs.reduce((a, b) => a + b, 0) / xs.length : null
const fmt = (v: number | null): string => (v == null ? '—' : `${v.toFixed(1)} ms`)
const rnd = () => Math.random().toString(36).slice(2)
const sleep = (ms: number) => new Promise((r) => setTimeout(r, ms))

// ── store + log (effects) ──────────────────────────────────────
const loadRuns = (): Runs => {
  try {
    return (JSON.parse(localStorage.getItem(STORE) ?? 'null') as Runs | null) ?? {}
  } catch {
    return {}
  }
}
const saveRuns = (runs: Runs): void => {
  try {
    localStorage.setItem(STORE, JSON.stringify(runs))
  } catch {
    /* ignore */
  }
}
const log = (line: string): void => {
  const $log = $<HTMLElement>('#log')
  if (!$log) return
  $log.textContent += `${line}\n`
  $log.scrollTop = $log.scrollHeight
}

// cold: ?bust per run → URL never cached → always network. warm: no bust → served
// from the browser cache after the first run.
const isCold = () => $<HTMLInputElement>('input[name="cold"]')?.checked ?? true
const bust = (url: string) =>
  isCold() ? `${url}${url.includes('?') ? '&' : '?'}bust=${rnd()}` : url

// ── measurement (one run of one CDN) ───────────────────────────
const timeCss = (cdn: Cdn): Promise<number> =>
  new Promise((resolve, reject) => {
    $$<HTMLLinkElement>('link[data-bench]').forEach((l) => l.remove()) // re-register @font-face cleanly
    const link = Object.assign(document.createElement('link'), {
      rel: 'stylesheet',
      href: bust(cdn.css),
    })
    link.dataset.bench = ''
    const t0 = performance.now()
    link.onload = () => resolve(performance.now() - t0)
    link.onerror = () => reject(new Error('link error'))
    document.head.append(link)
  })

const showSpecimen = async (cdn: Cdn): Promise<number> => {
  const $title = $<HTMLElement>('#specimen p:first-of-type')
  const $body = $<HTMLElement>('#specimen p:nth-of-type(2)')
  if ($title) $title.style.fontFamily = `'${cdn.family}'`
  if ($body) $body.style.fontFamily = `'${cdn.family}'`
  const t0 = performance.now()
  try {
    await document.fonts.load(`400 1rem '${cdn.family}'`, $body?.textContent ?? '')
  } catch {
    /* font load races are fine; we still timestamp below */
  }
  await document.fonts.ready
  const $tag = $<HTMLElement>('#specimen figcaption')
  if ($tag) $tag.textContent = `現以 ${cdn.label} 提供 ${cdn.family}`
  return performance.now() - t0
}

const timeWoff2 = async (cdn: Cdn): Promise<number | null> => {
  if (!cdn.probe) return null // Google's slices aren't a fixed, comparable URL
  try {
    const t0 = performance.now()
    const res = await fetch(bust(cdn.probe), {
      cache: isCold() ? 'no-store' : 'force-cache',
      mode: 'cors',
    })
    await res.arrayBuffer()
    return performance.now() - t0
  } catch (e) {
    log(`${cdn.label} woff2 probe 失敗：${(e as Error).message}`)
    return null
  }
}

const runOne = async (key: CdnKey): Promise<Run> => {
  const cdn = CDNS[key]
  const cold = isCold()
  const cssMs = await timeCss(cdn)
  const fontMs = (await showSpecimen(cdn)) + cssMs
  const woffMs = await timeWoff2(cdn)
  log(
    `${cdn.label.padEnd(9)} [${cold ? '冷' : '暖'}] css ${cssMs.toFixed(1)}ms` +
      `  字體就緒 ${fontMs.toFixed(1)}ms  woff2 ${woffMs == null ? '—' : `${woffMs.toFixed(1)}ms`}`,
  )
  return { cssMs, fontMs, woffMs }
}

// ── intents (events → store) ───────────────────────────────────
const benchKey = async (key: CdnKey, reps: number): Promise<void> => {
  for (let i = 0; i < reps; i++) {
    const runs = loadRuns()
    const rec = (runs[key] ??= { css: [], font: [], woff2: [] })
    try {
      const r = await runOne(key)
      rec.css.push(r.cssMs)
      rec.font.push(r.fontMs)
      if (r.woffMs != null) rec.woff2.push(r.woffMs)
    } catch (e) {
      log(`${key} 失敗：${(e as Error).message}`)
    }
    saveRuns(runs)
    render()
    await sleep(120)
  }
}

// ── apply (store → DOM) ────────────────────────────────────────
const statRow = (runs: Runs, key: CdnKey): Stat => {
  const rec = runs[key]
  const css = rec?.css ?? []
  return {
    key,
    label: CDNS[key].label,
    tao: CDNS[key].tao,
    n: css.length,
    min: css.length ? Math.min(...css) : null,
    med: median(css),
    avg: mean(css),
    fmed: median(rec?.font ?? []),
    wmed: median(rec?.woff2 ?? []),
  }
}
const rowHtml = (s: Stat, winner: CdnKey | undefined): string => {
  const win = s.key === winner && s.n > 0
  const badge = win ? '<span class="badge">最快</span>' : ''
  const noTao = s.tao ? '' : '<span class="muted"> ·無TAO</span>'
  return (
    `<tr${win ? ' class="winner"' : ''}>` +
    `<td class="cdn">${s.label}${badge}${noTao}</td>` +
    `<td class="n">${s.n || '—'}</td>` +
    `<td class="n">${fmt(s.min)}</td>` +
    `<td class="n">${fmt(s.med)}</td>` +
    `<td class="n">${fmt(s.avg)}</td>` +
    `<td class="n">${fmt(s.fmed)}</td>` +
    `<td class="n">${fmt(s.wmed)}</td>` +
    '</tr>'
  )
}
const render = (): void => {
  const $tbody = $<HTMLElement>('#results tbody')
  if (!$tbody) return
  const runs = loadRuns()
  const rows = KEYS.map((k) => statRow(runs, k))
  const winner = rows
    .filter((r) => r.med != null)
    .sort((a, b) => (a.med as number) - (b.med as number))[0]?.key
  $tbody.innerHTML = rows.map((r) => rowHtml(r, winner)).join('')
}

// ── wire ───────────────────────────────────────────────────────
const setBusy = (busy: boolean) =>
  $$<HTMLButtonElement>('button').forEach((b) => (b.disabled = busy))

const runClicked = ($btn: HTMLButtonElement) => async (): Promise<void> => {
  const reps = Math.max(1, Math.min(50, Number($<HTMLInputElement>('input[name="reps"]')?.value) || 1))
  const key = $btn.dataset.run as CdnKey | 'all'
  setBusy(true)
  log(`\n▶ ${key === 'all' ? '四家' : CDNS[key].label}　${reps} 次/家　[${isCold() ? '冷抓' : '暖抓'}]`)
  const keys = key === 'all' ? KEYS : [key]
  for (const k of keys) await benchKey(k, reps)
  log('✔ 完成')
  setBusy(false)
}
$$<HTMLButtonElement>('[data-run]').forEach(($btn) =>
  $btn.addEventListener('click', runClicked($btn)),
)

$('[data-reset]')?.addEventListener(
  'click',
  () => {
    saveRuns({})
    const $log = $<HTMLElement>('#log')
    if ($log) $log.textContent = ''
    render()
  },
)

// dark mode: initial state is restored by the inline pre-paint script next to the
// checkbox (it must tick :checked before paint); here we only persist the toggle.
const $dark = $<HTMLInputElement>('input[name="dark-mode"]')
$dark?.addEventListener(
  'change',
  () => {
    try {
      localStorage.setItem('ziano-theme', $dark.checked ? 'dark' : 'light')
    } catch {
      /* ignore */
    }
  },
)

// ── init ───────────────────────────────────────────────────────
render()
HELP.forEach((line) => log(line))
