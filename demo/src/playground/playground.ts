// Playground orchestration. One immutable-ish state + per-script specimen texts,
// persisted to localStorage; pure-ish apply() functions push state → DOM. The
// slice piano (piano.ts) owns hit-lighting/flash and pushes its hit set back here
// via onHits so we can report the actual downloaded KB.
import type { Font, Generic, Script } from '../fonts/fonts'
import { byId } from '../fonts/fonts'
import type { Source } from '../cdn/cdn'
import { SOURCE_LABEL, snippet, woff2Url } from '../cdn/cdn'
import { useSource, useWeight } from '../cdn/fontLink'
import { mountFontSelect } from '../fonts/fontSelect'
import { setPianoScript } from './piano'
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
}
type Saved = { config?: Partial<State>; texts?: Partial<Record<Script, Sample>> }
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
  const $previewTab = $<HTMLInputElement>('#playground input[name="pane"][value="preview"]')

  const $title = $<HTMLElement>('h1', $spec)
  const $body = $<HTMLElement>('div', $spec)
  const $weight = $<HTMLInputElement>('#playground input[name="font-weight"]')
  const $weightField = $weight?.closest('label') ?? null
  const $weightOut = $weightField?.querySelector('output') ?? null
  const $size = $<HTMLInputElement>('#playground input[name="font-size"]')
  const $sizeOut = $size?.closest('label')?.querySelector('output') ?? null
  const $snippet = $<HTMLElement>('#playground .snippet')
  const $cssUsage = $<HTMLElement>('#playground .css-usage')
  const $copy = $<HTMLButtonElement>('#playground .copy')
  const $meta = $<HTMLElement>('#playground .meta')
  const ids = fonts.map((f) => f.id)

  const saved = loadSaved()
  const texts: Record<Script, Sample> = {
    tc: withDefaults(saved.texts?.tc, SAMPLES.tc),
    sc: withDefaults(saved.texts?.sc, SAMPLES.sc),
    jp: withDefaults(saved.texts?.jp, SAMPLES.jp),
  }
  let state: State = {
    source: 'jsdelivr',
    fontId: fonts[0].id,
    weight: 400,
    pickWeight: null,
    size: 18,
    vertical: false,
    ...saved.config,
  }
  const font = () => byId(fonts, state.fontId) ?? fonts[0]
  // the per-weight file to load/recommend: a static font's picked weight, else
  // null (VF, or static 全部 → whole-family swap.css)
  const weightFile = (): number | null => (font().variable ? null : state.pickWeight)

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
    if ($meta)
      $meta.textContent = `${f.family}・${GENERIC_LABEL[f.generic]}・${f.variable ? 'VF' : 'Static'}・字重 ${state.weight}・${state.size}px・${SOURCE_LABEL[state.source]}`
  }

  const applySnippet = () => {
    if ($snippet)
      $snippet.textContent = snippet(state.source, state.fontId, weightFile() ?? undefined)
    const f = font()
    if ($cssUsage)
      $cssUsage.textContent = `body {\n  font-family: '${f.family}', ${GENERIC_FALLBACK[f.generic]};\n}`
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

  const render = () => {
    applyWeightField()
    applyType()
    applySnippet()
    applyMeta()
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
    applySnippet()
    applyMeta()
    save()
  }

  // stash the current specimen under `from`, load `to` (per-script editable text)
  const swapText = (to: Script, from?: Script) => {
    if (from && $title && $body)
      texts[from] = { title: $title.textContent ?? '', body: $body.innerHTML }
    if ($title) $title.textContent = texts[to].title
    if ($body) $body.innerHTML = texts[to].body
  }

  const pickFont = (id: string) => {
    const prev = font()
    const next = byId(fonts, id) ?? prev
    const [lo, hi] = weightRange(next)
    if (next.script !== prev.script) swapText(next.script, prev.script)
    // new font → back to 全部; VF keeps the slider weight, static resets to default
    state = {
      ...state,
      fontId: id,
      pickWeight: null,
      weight: next.variable ? clamp(state.weight, lo, hi) : defaultWeight(next),
    }
    useWeight(state.source, id, null)
    $select.value = id
    setPianoScript(next.script)
    render()
    save()
  }

  const setSource = (source: Source) => {
    state = { ...state, source }
    useSource(source, ids)
    useWeight(source, state.fontId, weightFile()) // re-add the per-weight extra on the new origin
    applySnippet()
    applyMeta()
    save()
  }

  // ── KB readout (piano → here): actual downloaded bytes of the hit slices ──
  const measureKB = async (slices: readonly number[]) => {
    const $kb = $<HTMLElement>('#playground .kb')
    if (!$kb) return
    const f = font()
    const weight = f.variable ? undefined : state.weight
    const urls = slices.map(
      (i) => new URL(woff2Url(state.source, f.id, i, weight), location.href).href,
    )
    await document.fonts.ready
    const seen = urls
      .map((u) => performance.getEntriesByName(u).at(-1) as PerformanceResourceTiming | undefined)
      .filter((e): e is PerformanceResourceTiming => !!e?.encodedBodySize)
    const kb = Math.round(seen.reduce((sum, e) => sum + e.encodedBodySize, 0) / 1024)
    $kb.textContent = seen.length === 0 ? '—' : `${kb} KB${seen.length < urls.length ? '+' : ''}`
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

  // persist specimen edits into the current script's slot
  const onEdit = () => {
    if ($title && $body)
      texts[font().script] = { title: $title.textContent ?? '', body: $body.innerHTML }
    save()
  }
  $title?.addEventListener('input', onEdit)
  $body?.addEventListener('input', onEdit)

  // paste as plain text — drop the source's fonts/colours/sizes so pasted content
  // inherits the specimen's styling like everything typed
  const onPaste = (e: ClipboardEvent) => {
    e.preventDefault()
    document.execCommand('insertText', false, e.clipboardData?.getData('text/plain') ?? '')
  }
  $title?.addEventListener('paste', onPaste)
  $body?.addEventListener('paste', onPaste)
  $copy?.addEventListener(
    'click',
    async () => {
      await navigator.clipboard.writeText(
        snippet(state.source, state.fontId, weightFile() ?? undefined),
      )
      const label = $copy.textContent
      $copy.textContent = 'Copied ✓'
      setTimeout(() => ($copy.textContent = label), 1400)
    },
  )

  // restore the saved specimen text for the starting font's script, then render
  swapText(font().script)
  $select.value = state.fontId
  setPianoScript(font().script)
  render()

  return {
    onHits: (slices) => void measureKB(slices),
    selectFont: pickFont,
    // jump back to the 預覽 tab — used when a hero card picks a font to show it
    showPreview: () => {
      if ($previewTab) $previewTab.checked = true
    },
  }
}
