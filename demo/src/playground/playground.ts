// Playground orchestration. One immutable-ish state + three editable specimen buffers
// (只彈常用鍵 / 彈奏全部120鍵 / 自訂內容), each persisted to localStorage and refilled with
// its default when blanked; pure-ish apply() functions push state → DOM. The slice piano
// (piano.ts) owns hit-lighting/flash and pushes its hit set back here via onHits so we
// can report the actual load time.
import type { Font, Generic, Script } from '../fonts/fonts'
import { byId } from '../fonts/fonts'
import type { Source } from '../cdn/cdn'
import { useSource, useWeight } from '../cdn/fontLink'
import { mountFontSelect } from '../fonts/fontSelect'
import { setPianoScript } from './piano'
import { PLAY_ALL_TITLE, PLAY_ALL_BODY } from './play120'
import { SAMPLES, type Sample } from '../fonts/samples'

const $ = <T extends Element>(sel: string, root: ParentNode = document) =>
  root.querySelector<T>(sel)
const $$ = <T extends Element>(sel: string) => [...document.querySelectorAll<T>(sel)]

const clamp = (n: number, lo: number, hi: number) => Math.min(hi, Math.max(lo, n))

// a specimen field is "empty" if it has no non-whitespace text once any markup is
// stripped (e.g. '' or '<p>   </p>'); such a field falls back to the default sample.
const blankText = (html: string): boolean => {
  const el = document.createElement('div')
  el.innerHTML = html
  return (el.textContent ?? '').trim() === ''
}
const withDefaults = (saved: Sample | undefined, def: Sample): Sample => ({
  title: saved && !blankText(saved.title) ? saved.title : def.title,
  body: saved && !blankText(saved.body) ? saved.body : def.body,
})

const GENERIC_LABEL: Record<Generic, string> = { ming: '明體', hei: '黑體', kai: '楷體' }
// the CSS generic to fall back to per glyph class, so the specimen degrades sanely
// before the webfont loads (and for any uncovered codepoint)
const GENERIC_FALLBACK: Record<Generic, string> = {
  ming: 'serif',
  hei: 'sans-serif',
  kai: 'cursive, serif',
}

// the weight slider's [lo, hi]: a VF spans its range, a static font its weights
const weightRange = (font: Font): readonly [number, number] =>
  font.variable
    ? [font.weights[0], font.weights[font.weights.length - 1]]
    : [Math.min(...font.weights), Math.max(...font.weights)]

// a static font's default display weight (Regular if present, else the lightest)
const defaultWeight = (font: Font): number =>
  font.weights.includes(400) ? 400 : font.weights[0]

// the three content tabs — each an independent editable buffer with its own default
type Tab = 'common' | 'all' | 'custom'
const CUSTOM_SAMPLE: Sample = {
  title: '自訂內容',
  body: '<p>在此打上你的內容，來看看字體載入的情況。</p>',
}
// a tab's fallback specimen, used on first load or whenever a field is blanked:
// 只彈常用鍵 follows the font's script (common chars only) · 彈奏全部120鍵 is the
// 120-slice showcase (play120.ts) · 自訂內容 a placeholder prompt
const tabDefault = (tab: Tab, script: Script): Sample =>
  tab === 'common'
    ? SAMPLES[script]
    : tab === 'all'
      ? { title: PLAY_ALL_TITLE, body: PLAY_ALL_BODY }
      : CUSTOM_SAMPLE

const LS = 'ziano-pg'
type State = {
  source: Source
  fontId: string
  weight: number
  // static only: a chosen weight loads swap/<w>.css (one weight); null = 全部
  // (whole-family swap.css). VF ignores it.
  pickWeight: number | null
  size: number
  vertical: boolean
  tab: Tab
}
type Saved = { config?: Partial<State>; texts?: Partial<Record<Tab, Sample>> }
const loadSaved = (): Saved => {
  try {
    return JSON.parse(localStorage.getItem(LS) ?? '{}') as Saved
  } catch {
    return {}
  }
}

export type Playground = {
  onHits: (slices: readonly number[]) => void
  selectFont: (id: string) => void
  showPreview: () => void
}

export const mountPlayground = (fonts: readonly Font[]): Playground => {
  const noop: Playground = { onHits: () => { }, selectFont: () => { }, showPreview: () => { } }
  const $spec = $<HTMLElement>('#playground article')
  const $select = $<HTMLSelectElement>('#playground select[name="font"]')
  if (!$spec || !$select || fonts.length === 0) return noop

  const $title = $<HTMLElement>('h1', $spec)
  const $body = $<HTMLElement>('div', $spec)
  const $weight = $<HTMLInputElement>('#playground input[name="font-weight"]')
  const $weightField = $weight?.closest('label') ?? null
  const $weightOut = $weightField?.querySelector('output') ?? null
  const $size = $<HTMLInputElement>('#playground input[name="font-size"]')
  const $sizeOut = $size?.closest('label')?.querySelector('output') ?? null
  const $metaFamily = $<HTMLElement>('#playground .meta output[for="font"]:not(.generic):not(.variable)')
  const $metaGeneric = $<HTMLElement>('#playground .meta output.generic')
  const $metaVariable = $<HTMLElement>('#playground .meta output.variable')
  const $metaWeight = $<HTMLElement>('#playground .meta output[for="font-weight"]')
  const $metaSize = $<HTMLElement>('#playground .meta output[for="font-size"]')
  const ids = fonts.map((f) => f.id)

  const saved = loadSaved()
  let state: State = {
    source: 'jsdelivr',
    fontId: fonts[0].id,
    weight: 400,
    pickWeight: null,
    size: 18,
    vertical: false,
    tab: 'common',
    ...saved.config,
  }
  const font = () => byId(fonts, state.fontId) ?? fonts[0]
  // the per-weight file to load/recommend: a static font's picked weight, else
  // null (VF, or static 全部 → whole-family swap.css)
  const weightFile = (): number | null => (font().variable ? null : state.pickWeight)

  // one editable buffer per tab — common's default follows the starting font's script
  const texts: Record<Tab, Sample> = {
    common: withDefaults(saved.texts?.common, SAMPLES[font().script]),
    all: withDefaults(saved.texts?.all, { title: PLAY_ALL_TITLE, body: PLAY_ALL_BODY }),
    custom: withDefaults(saved.texts?.custom, CUSTOM_SAMPLE),
  }

  // chips container for static weights — built once, toggled with the slider
  const $chips = document.createElement('div')
  $chips.className = 'chips'
  $weightField?.append($chips)

  const save = () => {
    try {
      localStorage.setItem(LS, JSON.stringify({ config: state, texts }))
    } catch {
      /* ignore */
    }
  }

  // ── apply (state → DOM) ──────────────────────────────────────
  const applyType = () => {
    const f = font()
    $spec.style.fontFamily = `'${f.family}', ${GENERIC_FALLBACK[f.generic]}`
    $spec.style.fontWeight = String(state.weight)
    $spec.style.writingMode = state.vertical ? 'vertical-rl' : 'horizontal-tb'
    if ($body) $body.style.fontSize = `${state.size}px`
    if ($title) $title.style.fontSize = `${Math.round(state.size * 1.5)}px`
  }

  const applyMeta = () => {
    const f = font()
    if ($metaFamily) $metaFamily.textContent = f.family
    if ($metaGeneric) $metaGeneric.textContent = GENERIC_LABEL[f.generic]
    if ($metaVariable) $metaVariable.textContent = f.variable ? '可變字體' : '靜態字體'
    if ($metaWeight) $metaWeight.textContent = `字重${state.weight}`
    if ($metaSize) $metaSize.textContent = `內文${state.size}px／標題${Math.round(state.size * 1.5)}px`
  }

  // a static-weight chip: 全部 (w=null → whole family) or a single weight (w=number
  // → swap/<w>.css). Pressed state tracks pickWeight, not the display weight.
  const chip = (label: string, w: number | null): HTMLButtonElement => {
    const b = document.createElement('button')
    b.type = 'button'
    b.textContent = label
    b.setAttribute('aria-pressed', String(state.pickWeight === w))
    b.addEventListener('click', () => setPick(w))
    return b
  }

  const applyWeightField = () => {
    const f = font()
    const [lo, hi] = weightRange(f)
    if ($weightOut) $weightOut.textContent = String(state.weight)
    if (f.variable) {
      $chips.hidden = true
      if ($weight) {
        $weight.hidden = false
        $weight.min = String(lo)
        $weight.max = String(hi)
        $weight.value = String(state.weight)
      }
    } else {
      if ($weight) $weight.hidden = true
      $chips.hidden = false
      $chips.replaceChildren(
        chip('全部', null),
        ...f.weights.map((w) => chip(String(w), w)),
      )
    }
  }

  // ── load readout (time-to-finish): time the CURRENT font's slices for the CURRENT
  // specimen text via document.fonts.load — a self-contained measure with its own t0 →
  // awaited promise, so it can't measure a bogus global "everything-settled" span (the
  // old loading/loadingdone approach got hijacked by the carousel → 35000ms).
  //   • Typing usually hits already-cached slices (common chars cluster in a few),
  //     which would read ~1ms and clobber the real figure — so on typing we skip when
  //     `document.fonts.check` says it's all cached, leaving the last genuine number;
  //     only a freshly-needed (uncached) slice refreshes it.
  //   • Deliberate switches (font / weight / CDN) pass force=true and always refresh
  //     (a cached switch honestly reads ~0 ms).
  // Writes just the number; CSS appends 「ms內到位」 once non-empty. Token guards races.
  const $ms = $<HTMLElement>('#playground output[name="ttf"]')
  let measureToken = 0
  const measureLoad = async (force = false) => {
    if (!$ms) return
    const f = font()
    const text = $spec?.textContent ?? ''
    const spec = `${state.weight} 1em '${f.family}'`
    if (!force && document.fonts.check(spec, text)) return
    const token = ++measureToken
    const t0 = performance.now()
    try {
      await document.fonts.load(spec, text)
    } catch {
      return
    }
    if (token !== measureToken) return // a newer measure superseded this one
    $ms.textContent = `${Math.max(0, Math.round(performance.now() - t0))}ms`
  }

  const render = () => {
    applyWeightField()
    applyType()
    applyMeta()
    void measureLoad(true)
  }

  // ── intents (events → state) ─────────────────────────────────
  // VF slider: just the display weight (pickWeight stays null → whole family)
  const setWeight = (w: number) => {
    state = { ...state, weight: w }
    applyWeightField()
    applyType()
    applyMeta()
    save()
  }

  // static chip: pick a single weight (load swap/<w>.css) or 全部 (whole family)
  const setPick = (w: number | null) => {
    state = { ...state, pickWeight: w, weight: w ?? defaultWeight(font()) }
    useWeight(state.source, state.fontId, w)
    applyWeightField()
    applyType()
    applyMeta()
    void measureLoad(true)
    save()
  }

  const pickFont = (id: string) => {
    const prev = font()
    const next = byId(fonts, id) ?? prev
    const [lo, hi] = weightRange(next)
    // new font → back to 全部; VF keeps the slider weight, static resets to default
    state = {
      ...state,
      fontId: id,
      pickWeight: null,
      weight: next.variable ? clamp(state.weight, lo, hi) : defaultWeight(next),
    }
    useWeight(state.source, id, null)
    $select.value = id
    setPianoScript(next.script) // re-maps the keyboard + repaints from the current text
    render()
    save()
  }

  const setSource = (source: Source) => {
    state = { ...state, source }
    useSource(source, ids)
    useWeight(source, state.fontId, weightFile()) // re-add the per-weight extra on the new origin
    void measureLoad(true)
    save()
  }

  // ── editable buffers (state ⇄ DOM) ───────────────────────────
  const readSpec = (): Sample => ({
    title: $title?.textContent ?? '',
    body: $body?.innerHTML ?? '',
  })
  // write the displayed text back into the active tab's slot
  const stash = () => {
    texts[state.tab] = readSpec()
  }
  // show a tab's text (filling its default where blank) and persist the resolved value.
  // body via innerHTML — set programmatically it does NOT NFC-normalise, so the 120-key
  // showcase's four font-internal keys (compat 樂 + three PUA codepoints) survive.
  const loadTab = (tab: Tab) => {
    const s = withDefaults(texts[tab], tabDefault(tab, font().script))
    texts[tab] = s
    if ($title) $title.textContent = s.title
    if ($body) $body.innerHTML = s.body
  }
  // bubbles to #playground article → piano repaint + load readout for the new text
  const repaint = () => $body?.dispatchEvent(new InputEvent('input', { bubbles: true }))

  const setTab = (tab: Tab) => {
    const $r = $<HTMLInputElement>(`#playground input[name="pane"][value="${tab}"]`)
    if ($r) $r.checked = true
    if (tab === state.tab) return
    stash() // keep the edits on the tab we're leaving
    state = { ...state, tab }
    loadTab(tab)
    repaint()
    save()
  }

  // a blanked title/body refills with the active tab's default (on blur, so it doesn't
  // fight mid-edit)
  const refillIfBlank = () => {
    const def = tabDefault(state.tab, font().script)
    let changed = false
    if ($title && blankText($title.textContent ?? '')) {
      $title.textContent = def.title
      changed = true
    }
    if ($body && blankText($body.innerHTML)) {
      $body.innerHTML = def.body
      changed = true
    }
    if (!changed) return
    stash()
    repaint()
    save()
  }

  // ── wire ─────────────────────────────────────────────────────
  useSource(state.source, ids)
  useWeight(state.source, state.fontId, weightFile()) // restore a saved per-weight pick
  mountFontSelect($select, fonts, pickFont)

  $weight?.addEventListener('input', () => setWeight(Number($weight.value)))
  const applySizeOutput = () => {
    if ($sizeOut) $sizeOut.textContent = `${state.size}px`
  }
  if ($size) {
    $size.value = String(state.size)
    applySizeOutput()
    $size.addEventListener(
      'input',
      () => {
        state = { ...state, size: Number($size.value) }
        applySizeOutput()
        applyType()
        applyMeta()
        save()
      },
    )
  }

  $$<HTMLInputElement>('#playground input[name="writing-mode"]').forEach(($r) => {
    $r.checked = ($r.value === 'vertical') === state.vertical
    $r.addEventListener(
      'change',
      () => {
        state = { ...state, vertical: $r.value === 'vertical' }
        applyType()
        save()
      },
    )
  })
  $$<HTMLInputElement>('#playground input[name="cdn"]').forEach(($r) => {
    $r.checked = $r.value === state.source
    $r.addEventListener('change', () => setSource($r.value as Source))
  })
  $$<HTMLInputElement>('#playground input[name="pane"]').forEach(($r) => {
    $r.checked = $r.value === state.tab
    $r.addEventListener('change', () => setTab($r.value as Tab))
  })

  // persist specimen edits into the active tab's slot
  const onEdit = () => {
    stash()
    save()
  }
  $title?.addEventListener('input', onEdit)
  $body?.addEventListener('input', onEdit)
  $title?.addEventListener('blur', refillIfBlank)
  $body?.addEventListener('blur', refillIfBlank)

  // paste as plain text — drop the source's fonts/colours/sizes so pasted content
  // inherits the specimen's styling like everything typed
  const onPaste = (e: ClipboardEvent) => {
    e.preventDefault()
    document.execCommand('insertText', false, e.clipboardData?.getData('text/plain') ?? '')
  }
  $title?.addEventListener('paste', onPaste)
  $body?.addEventListener('paste', onPaste)

  // seed the active tab's text, then render
  loadTab(state.tab)
  $select.value = state.fontId
  setPianoScript(font().script)
  render()

  return {
    onHits: () => void measureLoad(),
    selectFont: pickFont,
    // a hero card picked a font to look at → show it on the common-sample tab
    showPreview: () => setTab('common'),
  }
}
