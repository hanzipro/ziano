// The 120-key piano backdrop for ziano. Each <kbd> is one of the 120 unicode-range
// slices; typing in the playground "plays" the font — every slice the text reaches
// lights its key, and each keystroke re-strikes it.
//
// Each script (TC / SC / JP) has its own partition — the same one the font was
// sliced with in the pipeline. Default is TC; setPianoScript() follows the font.
import sliceTableTC from './sliceTable.json'
import sliceTableSC from './sliceTable.sc.json'
import sliceTableJP from './sliceTable.jp.json'

type Script = 'tc' | 'sc' | 'jp'
type Table = ReadonlyArray<{ index: number; unicode_range: string }>

const SLICE_N = (sliceTableTC as Table).length // 120 (all scripts)
// semitone offsets that are black keys within each 12-key octave (C# D# F# G# A#)
const BLACK = new Set([1, 3, 6, 8, 10])

// "u+4e00-9fff" / "u+3000" → the codepoints it covers
const expandRange = (token: string): number[] => {
  const t = token.trim().replace(/^u\+/i, '')
  if (!t) return []
  if (!t.includes('-')) return [parseInt(t, 16)]
  const [lo, hi] = t.split('-').map((x) => parseInt(x, 16))
  return Array.from({ length: hi - lo + 1 }, (_, k) => lo + k)
}

// codepoint → slice index (later entries win on overlap, as in the source order)
const buildMap = (table: Table): Map<number, number> =>
  new Map(
    table.flatMap((s) =>
      s.unicode_range
        .split(',')
        .flatMap(expandRange)
        .map((cp) => [cp, s.index] as const),
    ),
  )

const MAPS: Record<Script, Map<number, number>> = {
  tc: buildMap(sliceTableTC as Table),
  sc: buildMap(sliceTableSC as Table),
  jp: buildMap(sliceTableJP as Table),
}

// --- geometry (pure) -------------------------------------------------------
const indices = Array.from({ length: SLICE_N }, (_, i) => i)
const isBlack = (i: number) => BLACK.has(i % 12)
const whiteCount = indices.filter((i) => !isBlack(i)).length
const whitesBefore = (i: number) => indices.slice(0, i).filter((j) => !isBlack(j)).length

// --- mutable view state (a DOM view needs some) ----------------------------
let cp2slice = MAPS.tc
let keys: readonly HTMLElement[] = []
let lastText = ''
let onHits: ((slices: readonly number[]) => void) | null = null

const specimen = () => document.querySelector('#playground article')

const slicesOf = (text: string): Set<number> =>
  new Set(
    [...new Set([...text])]
      .filter((c) => c.trim())
      .map((c) => cp2slice.get(c.codePointAt(0)!))
      .filter((i): i is number => i !== undefined),
  )

const paint = (text: string): void => {
  lastText = text
  const hit = slicesOf(text)
  keys.forEach((k, i) => k.classList.toggle('on', hit.has(i)))
  // write only the count into its <output>; the rest of the status is static markup
  const $hits = document.querySelector('#playground output[name="hit-slices"]')
  if ($hits) $hits.textContent = String(hit.size)
  onHits?.([...hit])
}

// re-strike each typed char's key — invert + depress, reads on white & black keys.
// `scale` (not `transform`) so it composes with the black keys' centring translateX.
const STRIKE: Keyframe[] = [
  { filter: 'invert(1)', scale: '0.94' },
  { filter: 'invert(0)', scale: '1' },
]

const flash = (text: string): void =>
  new Set(
    [...text]
      .filter((c) => c.trim())
      .map((c) => cp2slice.get(c.codePointAt(0)!))
      .filter((i): i is number => i !== undefined && keys[i] !== undefined),
  ).forEach((i) => keys[i].animate(STRIKE, { duration: 460, easing: 'ease-out' }))

// Build the 120 <kbd> keys once. White keys are flex siblings (equal share of the
// keyboard); black keys overlay the boundary after their preceding white key
// (--pos). All %-based → scales with the viewport, no relayout. keys[sliceIndex]
// is that slice's <kbd>, so paint()/flash() index it directly.
const buildKeys = (el: HTMLElement): readonly HTMLElement[] => {
  el.style.setProperty('--wkstep', `${100 / whiteCount}%`)
  const made = indices.map((i) => {
    const black = isBlack(i)
    const k = document.createElement('kbd')
    k.className = black ? 'black' : 'white'
    if (black) k.style.setProperty('--pos', `${(whitesBefore(i) / whiteCount) * 100}%`)
    return { black, k }
  })
  el.replaceChildren()
  made.filter((m) => !m.black).forEach((m) => el.append(m.k)) // white keys, in order
  made.filter((m) => m.black).forEach((m) => el.append(m.k)) // black keys layer on top
  return made.map((m) => m.k)
}

// switch the active partition (TC / SC / JP) to match the playing font's script,
// re-reading the specimen so a programmatic text-swap repaints correctly
export const setPianoScript = (script: Script): void => {
  cp2slice = MAPS[script] ?? MAPS.tc
  paint(specimen()?.textContent ?? lastText)
}

export const mountPiano = (
  selector = '.Piano',
  hitsCb?: (slices: readonly number[]) => void,
): void => {
  onHits = hitsCb ?? null
  const el = document.querySelector<HTMLElement>(selector)
  if (!el) return
  el.setAttribute('aria-hidden', 'true')
  keys = buildKeys(el)

  const sync = () => paint(specimen()?.textContent ?? '')
  const $spec = specimen()
  $spec?.addEventListener(
    'input',
    (e) => {
      sync()
      const typed = (e as InputEvent).data // pulse the just-typed character(s)
      if (typed) flash(typed)
    },
  )
  $spec?.addEventListener(
    'paste',
    (e) => {
      const t = (e as ClipboardEvent).clipboardData?.getData('text')
      if (t) flash(t)
    },
  )
  sync() // initial paint from the seeded specimen text
}
